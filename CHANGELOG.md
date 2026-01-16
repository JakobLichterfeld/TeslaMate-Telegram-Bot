# Changelog

## [Unreleased]

### New Features

### Enhancements

- docs(nix): update README with pinning v1.0.0 by hash example

#### Build, CI, internal

### Bug Fixes

## [1.0.0] - 2026-01-14

Docker:

- Reduced image size by 16 %
- **Breaking Change**: Dropped `armv7` Docker image support due to `uv` base image unavailability for this architecture.

Note for contributors: The default branch was renamed to `main`. Please update your local repository accordingly (see GitHub hint when visiting [JakobLichterfeld/TeslaMate-Telegram-Bot](https://github.com/JakobLichterfeld/TeslaMate-Telegram-Bot) or [GitHub documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/renaming-a-branch#updating-a-local-clone-after-a-branch-name-changes) for more information).

### New Features

- feat(nix): Implement Nix flake for development, packaging, and deployment as NixOS service

### Enhancements

- docs: add DevOps badge to Readme

#### Build, CI, internal

- build(deps): bump docker/setup-buildx-action from 3.11.1 to 3.12.0 (#96)
- build(deps): bump actions/checkout from 6.0.0 to 6.0.1 (#97)
- build(deps): bump actions/download-artifact from 6.0.0 to 7.0.0 (#98)
- build(deps): bump actions/upload-artifact from 5.0.0 to 6.0.0 (#99)
- chore: rename branch to main
- feat: use ruff as linter and formatter for python files
- chore: add treefmt as code formatting multiplexer
- ci: update Python version to 3.14 in linting workflow
- build: Migrate to pyproject.toml for modern project and dependency management
- build: Optimize Dockerfile with multi-stage build
- build: Migrate to uv for Python dependency management and build optimization, drop armv7 support
- feat(ci): Overhaul and modularize CI workflows
- chore: add .typos.toml for custom typo handling

### Bug Fixes

- fix(nix): ensure Nix build runs on a clean git repository
- fix(nix): correct mkOption usage for autoStart in module.nix
- fix(nix): correct type reference for autoStart option in module.nix

## [0.7.9] - 2025-12-02

### New Features

### Enhancements

#### Build, CI, internal

- build(deps): bump docker/setup-buildx-action from 3.8.0 to 3.10.0 (#63)
- build(deps): bump actions/download-artifact from 4.1.8 to 4.1.9 (#64)
- build(deps): bump docker/setup-qemu-action from 3.3.0 to 3.6.0 (#65)
- build(deps): bump docker/metadata-action from 5.6.1 to 5.7.0 (#66)
- build(deps): bump actions/upload-artifact from 4.6.0 to 4.6.1 (#67)
- style: add flake8 disable comments for global state variable
- build(deps): bump actions/setup-python from 5.4.0 to 5.5.0 (#68)
- build(deps): bump actions/download-artifact from 4.1.9 to 4.2.1 (#69)
- build(deps): bump docker/login-action from 3.3.0 to 3.4.0 (#70)
- build(deps): bump docker/build-push-action from 6.13.0 to 6.15.0 (#71)
- build(deps): bump actions/upload-artifact from 4.6.1 to 4.6.2 (#72)
- build(deps): bump python-telegram-bot from 21.10 to 22.0 (#73)
- style: update flake8 disable comments for global state variable to comply with flake8 7.2.0
- build(deps): bump actions/setup-python from 5.5.0 to 5.6.0 (#76)
- build(deps): bump docker/build-push-action from 6.15.0 to 6.16.0 (#74)
- build(deps): bump docker/build-push-action from 6.15.0 to 6.16.0 (#75)
- build(deps): bump docker/build-push-action from 6.16.0 to 6.18.0 (#77)
- build(deps): bump python-telegram-bot from 22.0 to 22.1 (#78)
- build(deps): bump docker/setup-buildx-action from 3.10.0 to 3.11.1 (#79)
- build(deps): bump python-telegram-bot from 22.1 to 22.2 (#80)
- build(deps): bump docker/login-action from 3.4.0 to 3.5.0 (#82)
- build(deps): bump python-telegram-bot from 22.2 to 22.3 (#81)
- build(deps): bump actions/checkout from 4.2.2 to 5.0.0 (#83)
- build(deps): bump docker/metadata-action from 5.7.0 to 5.8.0 (#84)
- build(deps): bump actions/download-artifact from 4.3.0 to 5.0.0 (#85)
- build(deps): bump docker/login-action from 3.5.0 to 3.6.0 (#86)
- build(deps): bump actions/setup-python from 5.6.0 to 6.0.0 (#87)
- build(deps): bump python-telegram-bot from 22.3 to 22.5 (#88)
- build(deps): bump python from 3.13-slim-bookworm to 3.14-slim-bookworm (#91)
- build(deps): bump actions/upload-artifact from 4.6.2 to 5.0.0 (#89)
- build(deps): bump actions/download-artifact from 5.0.0 to 6.0.0 (#90)
- build(deps): bump docker/setup-qemu-action from 3.6.0 to 3.7.0 (#92)
- build(deps): bump docker/metadata-action from 5.8.0 to 5.10.0 (#93)
- build(deps): bump actions/checkout from 5.0.0 to 6.0.0 (#94)
- build(deps): bump actions/setup-python from 6.0.0 to 6.1.0 (#95)

### Bug Fixes

## [0.7.8] - 2025-02-01

### New Features

### Enhancements

#### Build, CI, internal

- build(deps): bump docker/setup-buildx-action from 3.7.1 to 3.8.0 (#55)
- build(deps): bump python-telegram-bot from 21.7 to 21.9 (#57)
- build(deps): bump actions/upload-artifact from 4.4.3 to 4.5.0 (#56)
- build(deps): bump python-telegram-bot from 21.9 to 21.10 (#58)
- build(deps): bump actions/upload-artifact from 4.5.0 to 4.6.0 (#59)
- build(deps): bump actions/setup-python from 5.3.0 to 5.4.0 (#60)
- build(deps): bump docker/setup-qemu-action from 3.2.0 to 3.3.0 (#61)
- build(deps): bump docker/build-push-action from 6.10.0 to 6.13.0 (#62)

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
- style: fix flake8 findings
- style: fix pylint findings

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
- feat: update paho-mqtt dependency to 2.0.0
- chore: Bump python-telegram-bot from 13.5 to 21.0.1

### Bug Fixes

## [0.5.3] - 2021-05-05

### New Features

### Enhancements

- updated requirements

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

- store configuration in separate files, see #4
- possibility to exit with STRG+C
- bit better messages on connection

### Bug Fixes

## [0.2.0] - 2020-09-04

### New Features

### Enhancements

- Implementation in python, as there are libraries for mqtt and telegram bot available for cool features in the future

### Bug Fixes

## [0.1.0] - 2020-09-04

- Initial release with proof of concept, see #1

[Unreleased]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.9...v1.0.0
[0.7.9]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.8...v0.7.9
[0.7.8]: https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/compare/v0.7.7...v0.7.8
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
