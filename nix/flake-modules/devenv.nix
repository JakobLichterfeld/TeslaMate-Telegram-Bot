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
    in
    {
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
          exec uv run --no-project --with-requirements uv.lock pylint --recursive=y src
        '';
        enterShell = ''
          export SECRETSPEC_PROVIDER=dotenv:.env
          echo "To run the teslamate-telegram-bot with secretspec, use:"
          echo "  secretspec run -- teslamate-telegram-bot"
          echo ""
          echo "To run pylint at the version pinned in uv.lock, use:"
          echo "  pylint"
          echo ""
        '';
      };
    };
}
