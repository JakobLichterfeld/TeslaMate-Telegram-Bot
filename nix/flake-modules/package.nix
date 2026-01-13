{ self, inputs, ... }: {
  perSystem = { pkgs, lib, ... }:
    let

      # Define the python version to be used, consistent with pyproject.toml
      python = pkgs.python3;

      # Construct a PEP 440 compliant version string based on git status
      versionStr =
        # If the working tree is dirty...
        if self.dirtyRev != null then "0.0.0+dirty"
        # Otherwise, if clean, use the short commit hash.
        else "0.0.0+git.${self.shortRev or "unknown"}";
    in
    {
      packages.default = python.pkgs.buildPythonPackage {
        pname = "teslamate-telegram-bot";
        version = versionStr;

        # The source is the root of the repository
        src = ../..;
        format = "pyproject";

        # Build-time dependencies from pyproject.toml's [build-system].requires
        nativeBuildInputs = with python.pkgs; [
          setuptools
          setuptools-scm
        ];

        # Runtime dependencies from pyproject.toml's dependencies
        propagatedBuildInputs = with python.pkgs; [
          paho-mqtt
          python-telegram-bot
        ];

        # This environment variable tells setuptools-scm to use the version
        # we've determined from the flake's context, rather than trying
        # to discover it from git history, which is not available in the sandbox.
        SETUPTOOLS_SCM_PRETEND_VERSION = versionStr;

        # doCheck = true;
        # checkInputs = with python.pkgs; [ pytestCheckHook ];
        # pytestFlagsArray = [ "src/tests" ];

        meta = with lib; {
          description = "A Telegram bot which sends a message if an update for your Tesla is available (use TeslaMate MQTT).";
          homepage = "https://github.com/JakobLichterfeld/TeslaMate-Telegram-Bot";
          changelog = "https://github.com/JakobLichterfeld/TeslaMate-Telegram-Bot/blob/main/CHANGELOG.md";
          license = licenses.mit;
          maintainers = [ "JakobLichterfeld" ];
        };
      };
    };
}
