from __future__ import annotations

import unittest
from unittest.mock import patch

from beambox_agent.main import _configure_console_encoding
from beambox_agent.crew import _markdown_urls


class ReconfigurableStream:
    def __init__(self) -> None:
        self.options = None

    def reconfigure(self, **kwargs) -> None:
        self.options = kwargs


class MainTests(unittest.TestCase):
    def test_console_is_configured_for_utf8(self) -> None:
        stdout = ReconfigurableStream()
        stderr = ReconfigurableStream()
        with patch("beambox_agent.main.sys.stdout", stdout), patch(
            "beambox_agent.main.sys.stderr", stderr
        ):
            _configure_console_encoding()

        self.assertEqual(stdout.options, {"encoding": "utf-8", "errors": "replace"})
        self.assertEqual(stderr.options, {"encoding": "utf-8", "errors": "replace"})

    def test_markdown_urls_only_returns_citation_targets(self) -> None:
        text = (
            "See [source](https://media.example/a) and "
            "plain https://example.com is not a Markdown citation."
        )
        self.assertEqual(
            _markdown_urls(text),
            {"https://media.example/a"},
        )


if __name__ == "__main__":
    unittest.main()
