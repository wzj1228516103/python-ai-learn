from __future__ import annotations

import json
import unittest

from beambox_agent.tools.beambox_tool import (
    BeamboxCompanyTool,
    ToolRegistry,
    _plain_text,
    _validate_public_url,
)


class FakeResponse:
    def __init__(self, text: str, url: str = "https://www.baidu.com/s"):
        self.text = text
        self.url = url
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.headers = {}
        self.responses = list(responses)
        self.calls = []

    def get(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class BeamboxCompanyToolTests(unittest.TestCase):
    def test_plain_text_removes_markup_and_scripts(self) -> None:
        html = "<p>AI <b>badge</b></p><script>bad()</script><p>Done</p>"
        self.assertEqual(_plain_text(html), "AI badge Done")

    def test_plain_text_prefers_main_content_over_store_navigation(self) -> None:
        html = (
            "<nav>Country list and store navigation</nav>"
            "<main id='MainContent'><h1>Beambox Nano</h1>"
            "<button>Add to cart</button><p>Animated GIF digital pin.</p></main>"
        )

        self.assertEqual(_plain_text(html), "Beambox Nano Animated GIF digital pin.")

    def test_private_url_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _validate_public_url("http://127.0.0.1/private")

    def test_search_scopes_company_and_parses_results(self) -> None:
        html = """
        <div class="result">
          <h3><a href="https://example.com/beambox">Beambox 融资动态</a></h3>
          <div class="c-abstract">深圳光胜人工智能科技完成融资。</div>
        </div>
        """
        session = FakeSession([FakeResponse(html)])
        tool = BeamboxCompanyTool(session=session)

        result = tool.search("融资", limit=3)

        self.assertIn("深圳光胜人工智能科技有限公司", result["searched_query"])
        self.assertEqual(result["results"][0]["title"], "Beambox 融资动态")
        self.assertEqual(result["results"][0]["url"], "https://example.com/beambox")
        self.assertEqual(session.calls[0][1]["params"]["wd"], result["searched_query"])

    def test_read_page_returns_final_url_and_clean_body(self) -> None:
        response = FakeResponse(
            "<html><title>品牌资料</title><body><p>AI 互动硬件</p></body></html>",
            url="https://media.example/article",
        )
        tool = BeamboxCompanyTool(session=FakeSession([response]))

        result = tool.read_page("https://www.baidu.com/link?url=abc")

        self.assertEqual(result["url"], "https://media.example/article")
        self.assertEqual(result["title"], "品牌资料")
        self.assertIn("AI 互动硬件", result["body"])

    def test_registry_returns_structured_error(self) -> None:
        registry = ToolRegistry(BeamboxCompanyTool(session=FakeSession([])))
        result = json.loads(registry.execute("missing_tool", "{}"))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
