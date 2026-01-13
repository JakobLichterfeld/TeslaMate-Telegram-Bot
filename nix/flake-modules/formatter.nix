{ inputs, ... }:
{
  imports = [
    inputs.treefmt-nix.flakeModule
  ];
  perSystem =
    { config, pkgs, ... }:
    {
      # Auto formatters. This also adds a flake check to ensure that the
      # source tree was auto formatted.
      treefmt = {
        flakeFormatter = true; # Enables treefmt the default formatter used by the nix fmt command
        flakeCheck = true; # Add a flake check to run treefmt
        projectRootFile = "Dockerfile"; # File used to identity repo root

        # we really need to mirror the treefmt.toml as we can't use it directly
        settings.global.excludes = [
          "*.gitignore"
          "*.dockerignore"
          ".envrc"
          "*.node-version"
          "CONTRIBUTING"
          "Dockerfile"
          "Makefile"
          "LICENSE"
          "*.metadata"
          "*.manifest"
          "*.webmanifest"
          "*.dat"
          "*.lock"
          "*.txt"
          "*.csv"
          "*.ico"
          "*.png"
          "*.svg"
          "*.properties"
          "*.xml"
          "*.po"
          "*.pot"
          "*.json.example"
          "*.typos.toml"
          "treefmt.toml"
        ];
        # run shellcheck first
        programs.shellcheck.enable = true;
        settings.formatter.shellcheck.priority = 0; # default is 0, but we set it here for clarity

        # shfmt second
        programs.shfmt.enable = true;
        programs.shfmt.indent_size = 0; # 0 means tabs
        settings.formatter.shfmt.priority = 1;

        programs.prettier.enable = true;

        programs.ruff-format.enable = true;
        programs.ruff-check.enable = true;

        programs.nixpkgs-fmt.enable = true;
      };
    };
}
