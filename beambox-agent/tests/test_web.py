from __future__ import annotations

import unittest
from unittest.mock import patch

from beambox_agent.web import _conversation_context, build_demo, chat


class WebTests(unittest.TestCase):
    def test_conversation_context_keeps_recent_messages(self) -> None:
        history = [
            {"role": "user", "content": "相机超时"},
            {"role": "assistant", "content": "请确认机型"},
            {"role": "user", "content": "BeamBox"},
        ]

        context = _conversation_context(history)

        self.assertIn("用户：相机超时", context)
        self.assertIn("助手：请确认机型", context)
        self.assertTrue(context.endswith("用户：BeamBox"))

    def test_build_demo_returns_chat_interface(self) -> None:
        demo = build_demo()
        try:
            self.assertEqual(demo.title, "Beambox 企业资料助手")
        finally:
            demo.close()

    def test_chat_yields_accumulated_stream_content(self) -> None:
        with patch("beambox_agent.web.Settings.from_env") as settings, patch(
            "beambox_agent.web.BeamboxAgent"
        ) as agent_class:
            agent_class.return_value.ask_stream.return_value = iter(["第一段", "，第二段"])

            output = list(chat("问题", []))

        settings.assert_called_once()
        self.assertEqual(output, ["第一段", "第一段，第二段"])


if __name__ == "__main__":
    unittest.main()
