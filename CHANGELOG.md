# Changelog

## [Unreleased]

### New Features

### Enhancements

- feat: use logging instead of simple print
- feat: introduce a global state and send messages depending on the state, improve logging
- ci: add python linting workflow
- ci: set max line length for flake8 python linting workflow
- stlye: fix flake8 findings
- stlye: fix pylint findings

### Bug Fixes

## [0.6.4] - 2023-03-17

### New Features

### Enhancements

- doc: update Docker installation instructions in the README and change to docker compose v2
- build: reduce image size by removing unnecessary packages

### Bug Fixes

- fix: correct number of positional arguments for on_connect() since mqtt5

## [0.6.3] - 2023-03-16

### New Features

### Enhancements

- build: improve non-root user creation in dockerfile
- style: remove global variables for bot and chat_id, ensure UPPERCASE for constants, update imports
- ci: distribute build across multiple runners

### Bug Fixes

fix: Subscription to teslamate_topic_update_version added

## [0.6.2] - 2023-03-16

### New Features

- feat: Specify which SW update is available (#21)

### Enhancements

- ci: use Environment File instead of deprecated set-output
- ci: correct use of environment file outputs

### Bug Fixes

- fix: remove double bot message

## [0.6.1] - 2023-03-15

### New Features

### Enhancements

### Bug Fixes

- fix: re-add notification for available SW update only

## [0.6.0] - 2023-03-15

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

[unreleased]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.6.4...HEAD
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
