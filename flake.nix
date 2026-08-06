{
  description = "TeslaMate Telegram Bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";
    devenv-root.url = "file+file:///dev/null";
    devenv-root.flake = false;
    devenv.url = "github:cachix/devenv";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{ self, flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      flake.nixosModules.default = import ./nix/module.nix { inherit self; };

      # Not machines anyone runs: the configurations that instantiate the
      # module, so CI notices when it stops evaluating against nixpkgs. One
      # per broker placement, because the module renders different unit
      # orderings for a local and a remote broker.
      flake.nixosConfigurations =
        let
          machine =
            configuration:
            inputs.nixpkgs.lib.nixosSystem {
              modules = [
                self.nixosModules.default
                ./nix/test-machine.nix
                configuration
              ];
            };
        in
        {
          test = machine ./nix/test-configuration.nix;
          test-remote = machine ./nix/test-configuration-remote.nix;
        };

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      # See ./nix/flake-modules/*.nix for the modules that are imported here.
      imports = [
        ./nix/flake-modules/devenv.nix
        ./nix/flake-modules/formatter.nix
        ./nix/flake-modules/package.nix
      ];
    };
}
