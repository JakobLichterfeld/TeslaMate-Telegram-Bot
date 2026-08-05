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

      # Not a machine anyone runs: the one configuration that instantiates the
      # module, so CI notices when it stops evaluating against nixpkgs.
      flake.nixosConfigurations.test = inputs.nixpkgs.lib.nixosSystem {
        modules = [
          self.nixosModules.default
          ./nix/test-configuration.nix
          { nixpkgs.hostPlatform = "x86_64-linux"; }
        ];
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
