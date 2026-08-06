# The local-broker half of the test pair (see test-configuration-remote.nix):
# broker and bot on the same machine. Never booted: what it proves is that the
# module still evaluates against nixpkgs, still renders its unit, and still
# orders that unit after the local broker.
{ config, lib, ... }:
{
  config = {
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

    # What this configuration is for: with the broker local, the bot must be
    # ordered after it. Checked at eval time, so the CI dry-run catches it.
    assertions = [
      {
        assertion = lib.elem "mosquitto.service" config.systemd.services.teslamate-telegram-bot.after;
        message = "with a local mosquitto, the bot unit must be ordered after mosquitto.service";
      }
    ];
  };
}
