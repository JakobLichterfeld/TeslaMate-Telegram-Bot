{ inputs, self, ... }:
{
  imports = [
    inputs.devenv.flakeModule
  ];

  perSystem =
    { config
    , pkgs
    , lib
    , ...
    }:
    let
      teslamate-telegram-bot = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      python = pkgs.python3;

      # One environment for the interpreter and the project, so the shell's
      # python can import it. Linters do not belong here: their versions come
      # from uv.lock, which is generated from pyproject.toml and is the single
      # place a version is pinned.
      pythonEnv = python.withPackages (ps: [
        teslamate-telegram-bot
      ]);

      # secretspec refuses to load a manifest whose revision it does not know,
      # and that takes the `secretspec run` below with it. Built against the
      # secretspec this shell hands out, not the one a contributor happens to
      # have installed.
      #
      # Every command that loads the manifest resolves the secrets too, so the
      # required ones are answered from the environment with values nothing
      # ever looks at: check asks whether they have one, not what it is. A new
      # required secret has to be listed here as well.
      secretspecManifestValid =
        pkgs.runCommand "secretspec-manifest-valid"
          {
            nativeBuildInputs = [ pkgs.secretspec ];
            TELEGRAM_BOT_API_KEY = "placeholder";
            TELEGRAM_BOT_CHAT_ID = "placeholder";
          }
          ''
            secretspec --file ${../../secretspec.toml} check --no-prompt --provider env
            touch $out
          '';
    in
    {
      # As a check for `nix flake check`, and as a package so CI can build it
      # for the system it runs on instead of hardcoding one.
      checks.secretspec = secretspecManifestValid;
      packages.check-secretspec = secretspecManifestValid;

      devenv.shells.default = {
        containers = lib.mkForce { }; # https://github.com/cachix/devenv/issues/528
        devenv.root =
          let
            devenvRootFileContent = builtins.readFile inputs.devenv-root.outPath;
          in
          pkgs.lib.mkIf (devenvRootFileContent != "") devenvRootFileContent;
        packages =
          [
            # The Python interpreter and the project's own package, providing
            # the main executable and its runtime dependencies.
            pythonEnv

            pkgs.uv
            pkgs.secretspec

            config.treefmt.build.wrapper
          ]
          ++ builtins.attrValues config.treefmt.build.programs;
        # Runs the pylint pinned in uv.lock over the project, the same way CI
        # does.
        scripts.pylint.exec = ''
          exec uv run --locked --group lint pylint --recursive=y src
        '';
        # Runs the test suite at the pytest pinned in uv.lock, the same way CI
        # does. Arguments are passed through; without them pytest uses the
        # testpaths from pyproject.toml, so there is no target to conflict with.
        scripts.pytest.exec = ''
          exec uv run --locked --group test pytest "$@"
        '';
        enterShell = ''
          export SECRETSPEC_PROVIDER=dotenv:.env
          echo "To run the teslamate-telegram-bot with secretspec, use:"
          echo "  secretspec run -- teslamate-telegram-bot"
          echo ""
          echo "To run pylint at the version pinned in uv.lock, use:"
          echo "  pylint"
          echo ""
          echo "To run the test suite, use:"
          echo "  pytest"
          echo ""
        '';
      };
    };
}
