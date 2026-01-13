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
            # The project's own package, providing the main executable and its runtime dependencies.
            teslamate-telegram-bot

            # The Python interpreter itself, for IDEs and manual script execution.
            python

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
