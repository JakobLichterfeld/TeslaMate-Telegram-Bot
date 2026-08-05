# The smallest machine that switches this service on, so `nix build
# .#nixosConfigurations.test.config.system.build.toplevel --dry-run` has
# something to instantiate module.nix with. It is never booted: what it proves
# is that the module still evaluates against nixpkgs and still renders its unit.
{ lib, ... }:
{
  # A stub, not TeslaMate: module.nix asserts on this option and nixpkgs
  # declares it nowhere, so something has to. Declaring the one option here
  # keeps the test on this repository's module instead of tying its lock to a
  # foreign flake that could break this check by changing.
  options.services.teslamate.enable = lib.mkEnableOption "TeslaMate test stub";

  config = {
    # What the one remaining assertion in module.nix requires, stubbed above.
    services.teslamate.enable = true;

    # The broker the bot below is pointed at, listening on a port nothing
    # defaults to: the settings the bot is given have to be the settings that
    # reach it, so they are worth nothing if they are the defaults on both
    # sides.
    services.mosquitto = {
      enable = true;
      listeners = [
        {
          port = 1884;
          users.bot = {
            acl = [ "readwrite #" ];
            passwordFile = "/run/secrets/mosquitto-bot";
          };
        }
      ];
    };

    services.teslamate-telegram-bot = {
      enable = true;
      secretsFile = "/run/secrets/teslamate-telegram-bot.env";
      # Set away from their defaults, so the options are not only declared but
      # also carried into the unit - and matching the broker above, host, port
      # and user alike.
      carId = 2;
      mqtt = {
        host = "127.0.0.1";
        port = 1884;
        user = "bot";
        namespace = "garage";
      };
    };

    # What a machine needs to evaluate to a toplevel, none of it ever used.
    boot.loader.grub.enable = false;
    fileSystems."/" = {
      device = "/dev/null";
      fsType = "ext4";
    };
    system.stateVersion = "26.05";
  };
}
