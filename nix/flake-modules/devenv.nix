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

      # One environment for the interpreter, the project and the linters that
      # have to import it. pylint resolves the project's imports only if it
      # lives in the same environment; from a separate derivation it reports
      # every third-party import as E0401.
      pythonEnv = python.withPackages (ps: [
        teslamate-telegram-bot
        ps.pylint
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
            # The Python interpreter, the project's own package (providing the
            # main executable and its runtime dependencies) and pylint, which
            # is not part of treefmt because it does not format.
            pythonEnv

            pkgs.uv
            pkgs.secretspec

            config.treefmt.build.wrapper
          ]
          ++ builtins.attrValues config.treefmt.build.programs;
        enterShell = ''
          export SECRETSPEC_PROVIDER=dotenv:.env
          echo "To run the teslamate-telegram-bot with secretspec, use:"
          echo "  secretspec run -- teslamate-telegram-bot"
          echo ""
        '';
      };
    };
}
