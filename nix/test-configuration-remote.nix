# The remote-broker half of the test pair (see test-configuration.nix): no
# mosquitto and no teslamate anywhere on this machine, the broker only a name
# on the network. Never booted: what it proves is that the module evaluates
# without either foreign service - including the guarded access to the
# services.teslamate option, which this configuration leaves undeclared - and
# that the unit then waits for the network instead of local units.
{ config, lib, ... }:
{
  config = {
    services.teslamate-telegram-bot = {
      enable = true;
      secretsFile = "/run/secrets/teslamate-telegram-bot.env";
      mqtt.host = "teslamate.example.org";
    };

    # What this configuration is for: with everything remote, the bot must
    # order after the network and after nothing local. Checked at eval time,
    # so the CI dry-run catches it.
    assertions =
      let
        after = config.systemd.services.teslamate-telegram-bot.after;
      in
      [
        {
          assertion = !(lib.elem "mosquitto.service" after) && !(lib.elem "teslamate.service" after);
          message = "with a remote broker, the bot unit must not be ordered after local units";
        }
        {
          assertion = lib.elem "network-online.target" after;
          message = "with a remote broker, the bot unit must be ordered after network-online.target";
        }
      ];
  };
}
