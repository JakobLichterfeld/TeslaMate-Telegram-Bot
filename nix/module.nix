{ self, ... }:
{ config
, lib
, pkgs
, ...
}:

let
  cfg = config.services.teslamate-telegram-bot;
  teslamate-telegram-bot = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
in
{
  options.services.teslamate-telegram-bot = {
    enable = lib.mkEnableOption "TeslaMate Telegram Bot";

    secretsFile = lib.mkOption {
      type = lib.types.path;
      example = "/run/secrets/teslamate-telegram-bot.env";
      description = lib.mdDoc ''
        Path to an environment file containing the secrets for the TeslaMate Telegram Bot.
        Must contain at least:
        - `TELEGRAM_BOT_API_KEY=secret_api_key` # encryption key used to encrypt database
        - `TELEGRAM_BOT_CHAT_ID=secret_chat_id` # password used to authenticate to database

        Optional values:
        - `MQTT_BROKER_PASSWORD=password` # only needed when broker has authentication enabled
      '';
    };

    carId = lib.mkOption {
      type = lib.types.int;
      default = 1;
      description = "The ID of the car to monitor.";
    };

    mqtt = {
      host = lib.mkOption {
        type = lib.types.str;
        default = "127.0.0.1";
        description = "The hostname or IP address of the MQTT broker.";
      };
      port = lib.mkOption {
        type = lib.types.port;
        default = 1883;
        description = "The port of the MQTT broker.";
      };
      user = lib.mkOption {
        type = with lib.types; nullOr str;
        default = null;
        description = "Username for the MQTT broker, only needed when broker has authentication enabled.";
      };
      namespace = lib.mkOption {
        type = with lib.types; nullOr str;
        default = null;
        description = "MQTT namespace, only needed when you specified MQTT_NAMESPACE on your TeslaMate installation.";
      };
    };
    autoStart = lib.mkOption {
      type = types.bool;
      default = true;
      description = "Whether to start TeslaMate Telegram Bot on boot.";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = config.services.teslamate.enable;
        message = "teslamate-telegram-bot cannot be enabled when teslamate is not enabled.";
      }
      {
        assertion = config.services.mosquitto.enable;
        message = "teslamate-telegram-bot cannot be enabled when mosquitto is not enabled.";
      }
    ];

    systemd.services.teslamate-telegram-bot = {
      description = "TeslaMate Telegram Bot";
      after = [
        "network.target"
        "mosquitto.service"
        "teslamate.service"
      ];
      wantedBy = lib.mkIf cfg.autoStart [ "multi-user.target" ];

      serviceConfig = {
        DynamicUser = true;
        Restart = "on-failure";
        RestartSec = "5s";
        ExecStart = "${teslamate-telegram-bot}/bin/teslamate-telegram-bot";
        EnvironmentFile = cfg.secretsFile;
        Environment = [
          "CAR_ID=${toString cfg.carId}"
          "MQTT_BROKER_HOST=${cfg.mqtt.host}"
          "MQTT_BROKER_PORT=${toString cfg.mqtt.port}"
        ]
        ++ lib.optional (cfg.mqtt.user != null) "MQTT_BROKER_USERNAME=${cfg.mqtt.user}"
        ++ lib.optional (cfg.mqtt.namespace != null) "MQTT_NAMESPACE=${cfg.mqtt.namespace}";
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectHome = true;
        ProtectHostname = true;
        ProtectKernelModules = true;
        ProtectKernelTunables = true;
        ProtectControlGroups = true;
        RestrictAddressFamilies = [
          "AF_INET"
          "AF_INET6"
        ]; # IPv4 + IPv6 only
        RestrictRealtime = true;
        SystemCallArchitectures = "native";
        LockPersonality = true;
        MemoryDenyWriteExecute = true;
        ProtectSystem = "strict";
      };
    };
  };
}
