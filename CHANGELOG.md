# Changelog

## [Unreleased]

### New Features

### Enhancements

#### Build, CI, internal

- build(deps): bump docker/setup-buildx-action from 3.7.1 to 3.8.0 (#55)
- build(deps): bump python-telegram-bot from 21.7 to 21.9 (#57)

### Bug Fixes

## [0.7.7] - 2024-12-02

### New Features

### Enhancements

- doc: Remove unnecessary build configuration in docker compose

#### Build, CI, internal

- build(deps): bump paho-mqtt from 2.0.0 to 2.1.0 (#39)
- build(deps): bump python-telegram-bot from 21.0.1 to 21.1.1 (#40)
- build(deps): bump python-telegram-bot from 21.1.1 to 21.2 (#42)
- build(deps): bump docker/build-push-action from 5 to 6 (#44)
- build(deps): bump python-telegram-bot from 21.2 to 21.3 (#43)
- build(deps): bump python-telegram-bot from 21.3 to 21.4 (#45)
- build(deps): bump python-telegram-bot from 21.4 to 21.6 (#46)
- ci: specify python version in GitHub workflow
- ci: pin github action dependencies to protect against supply chain attacks, refactor to use common check_paths workflow
- ci(fix): handle empty path filter output
- style: UPPER_CASE naming style for constant name
- build(deps): bump actions/setup-python from 5.2.0 to 5.3.0 (#47)
- build(deps): bump actions/checkout from 4.1.7 to 4.2.2 (#48)
- build(deps): bump actions/upload-artifact from 4.4.0 to 4.4.3 (#49)
- build(deps): bump docker/setup-buildx-action from 3.6.1 to 3.7.1 (#50)
- build(deps): bump python from 3.12-slim-bookworm to 3.13-slim-bookworm (#51)
- build(deps): bump python-telegram-bot from 21.6 to 21.7 (#52)
- build(deps): bump docker/build-push-action from 6.9.0 to 6.10.0 (#53)
- build(deps): bump docker/metadata-action from 5.5.1 to 5.6.1 (#54)

### Bug Fixes

## [0.7.6] - 2024-04-12

### New Features

- feat: support MQTT_NAMESPACE via optional environment variable (#38)

### Enhancements

- doc: remove version tag in example docker compose as it is obsolete in docker 25.05
- build(deps): bump dorny/paths-filter from 3.0.1 to 3.0.2 (#37)

### Bug Fixes

## [0.7.5] - 2024-03-21

### New Features

- feat: allow negative chat_id, which means group chats (#35)
- feat: rewrite type check for some environment variables including 2 minute wait before retry (#36)

### Enhancements

### Bug Fixes

## [0.7.4] - 2024-03-21

### New Features

### Enhancements

### Bug Fixes

- fix: resolve UnboundLocalError if update version is empty (#34)

## [0.7.3] - 2024-03-21

### New Features

### Enhancements

- style: correct typo in filename

### Bug Fixes

- fix: correct type check for some environment variables (#33, thanks @freinbichler for reporting)

## [0.7.2] - 2024-03-21

### New Features

- feat: send telegram message when bot started and stopped (not working for docker stop)
- feat: add emoticons to messages
- feat: car_id can be set via optional environment variable (see readme)

### Enhancements

- feat: decrease checking interval to 30 seconds to reduce system load
- feat: check some environment variables for valid values
- fix: do not send a message if an empty update SW version is received after a successful update of the car SW

### Bug Fixes

## [0.7.1] - 2024-03-19

### New Features

### Enhancements

### Bug Fixes

- fix: correct use of async functions

## [0.7.0] - 2024-03-18

### New Features

### Enhancements

- feat: use logging instead of simple print
- feat: introduce a global state and send messages depending on the state, improve logging
- ci: add python linting workflow
- ci: set max line length for flake8 python linting workflow
- ci: install requirements before linting
- stlye: fix flake8 findings
- stlye: fix pylint findings

### Bug Fixes

## [0.6.4] - 2024-03-17

### New Features

### Enhancements

- doc: update Docker installation instructions in the README and change to docker compose v2
- build: reduce image size by removing unnecessary packages

### Bug Fixes

- fix: correct number of positional arguments for on_connect() since mqtt5

## [0.6.3] - 2024-03-16

### New Features

### Enhancements

- build: improve non-root user creation in dockerfile
- style: remove global variables for bot and chat_id, ensure UPPERCASE for constants, update imports
- ci: distribute build across multiple runners

### Bug Fixes

fix: Subscription to teslamate_topic_update_version added

## [0.6.2] - 2024-03-16

### New Features

- feat: Specify which SW update is available (#21)

### Enhancements

- ci: use Environment File instead of deprecated set-output
- ci: correct use of environment file outputs

### Bug Fixes

- fix: remove double bot message

## [0.6.1] - 2024-03-15

### New Features

### Enhancements

### Bug Fixes

- fix: re-add notification for available SW update only

## [0.6.0] - 2024-03-15

### New Features

### Enhancements

- doc: show docker pulls in readme
- ci: bump actions/checkout to v4
- ci: bump docker/setup-qemu-action to v3
- ci: Enable dependabot for GitHub Actions
- ci: bump actions/cache to v4
- ci: bump docker/login-action to v3
- ci: Enable dependabot for pip requirements
- build: Update Python base image to version 3.11-slim-bookworm
- build: reduce the size of the Docker image by cleaning the APT cache
- build: use copy instead of add in dockerfile
- build: remove non-existent deb package from docker file
- refactor: improve maintainability by extracting methods, extract environment variable handling, default value handling, add docstrings
- ci: enable dependabot for docker dependencies
- build: Bump python from 3.11-slim-bookworm to 3.12-slim-bookworm (#32)
- feat: update paho-mqtt dependencie to 2.0.0
- chore: Bump python-telegram-bot from 13.5 to 21.0.1

### Bug Fixes

## [0.5.3] - 2021-05-05

### New Features

### Enhancements

- updateded requirements

### Bug Fixes

## [0.5.2] - 2021-05-05

### New Features

### Enhancements

### Bug Fixes

- docker build dependencies

## [0.5.1] - 2021-05-05

### New Features

### Enhancements

- MQTT authentication optional usable, see #23

## [0.5.0] - 2020-12-03

### New Features

### Enhancements

- deployment as docker on docker hub, see #8
- Internal: Docker-Action: use official docker buildx, see #14

## [0.4.0] - 2020-09-04

### New Features

### Enhancements

- deployment as docker, see #6

### Bug Fixes

## [0.3.0] - 2020-09-04

### New Features

### Enhancements

- store configuration in seperate files, see #4
- possibility to exit with STRG+C
- bit better messages on connection

### Bug Fixes

## [0.2.0] - 2020-09-04

### New Features

### Enhancements

- Implemetation in python, as there are libraries for mqtt and telegram bot available for cool features in the future

### Bug Fixes

## [0.1.0] - 2020-09-04

- Initial release with proof of concept, see #1

[Unreleased]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.7...HEAD
[0.7.7]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.6...v0.7.7
[0.7.6]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.5...v0.7.6
[0.7.5]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.4...v0.7.5
[0.7.4]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.6.4...v0.7.0
[0.6.4]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.5.3...v0.6.0
[0.5.3]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/e76bb37d3...v0.1.0
