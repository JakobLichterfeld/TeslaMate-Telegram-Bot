"""Tests for what the logging configuration lets through.

The Telegram API carries the bot token in the URL path, and httpx logs every
request it makes at INFO. With the root logger at INFO that puts the token
into `docker logs` and into whatever collects them.
"""

import logging

TOKEN = "1234567:AAH-fake-token-that-must-not-appear"
REQUEST_LINE = "HTTP Request: POST https://api.telegram.org/bot%s/sendMessage"


def test_the_http_client_cannot_log_the_bot_token(caplog):
    """The logger name is httpx's own, checked against the version in uv.lock."""
    with caplog.at_level(logging.DEBUG):
        logging.getLogger("httpx").info(REQUEST_LINE, TOKEN)

    assert TOKEN not in caplog.text
    assert caplog.text == ""


def test_the_http_client_still_reports_failures(caplog):
    """Silenced, not muted: a failing request must still be visible."""
    with caplog.at_level(logging.WARNING):
        logging.getLogger("httpx").warning("Retrying request")

    assert "Retrying request" in caplog.text


def test_the_bots_own_messages_are_not_affected(module, caplog):
    with caplog.at_level(logging.INFO):
        module.logger.info("Starting the Teslamate Telegram Bot.")

    assert "Starting the Teslamate Telegram Bot." in caplog.text
