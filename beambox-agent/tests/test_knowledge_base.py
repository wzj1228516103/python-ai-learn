from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from beambox_agent.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseBuilder,
    KnowledgeDocument,
    OfficialSiteCrawler,
    _content_hash,
    _source_type,
    _stable_id,
)


def make_document(url: str, title: str, content: str) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=_stable_id(f"financing:{url}"),
        topic="financing",
        topic_name="融资动态",
        title=title,
        url=url,
        source_url=url,
        source_type="媒体报道",
        content=content,
        status="full_text",
        retrieved_at="2026-07-27T00:00:00+00:00",
        content_hash=_content_hash(content),
    )


class FakeSourceTool:
    def search(self, query: str, limit: int = 5) -> dict:
        return {
            "results": [
                {
                    "title": "Beambox 融资报道",
                    "url": "https://example.com/redirect",
                    "snippet": "光胜 Beambox 完成融资。",
                }
            ]
        }

    def read_page(self, url: str) -> dict:
        return {
            "url": "https://media.example/beambox",
            "title": "Beambox 完成融资",
            "body": "Beambox 完成新一轮融资。" * 30,
        }


class FakeOfficialSourceTool:
    def read_page(self, url: str) -> dict:
        return {
            "url": url,
            "title": "Beambox Nano E-Badge",
            "body": "Beambox Nano 是支持 GIF 的可穿戴电子徽章。" * 20,
        }


class KnowledgeBaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "knowledge.sqlite3"
        self.knowledge_base = KnowledgeBase(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_search_prefers_title_and_returns_document_id(self) -> None:
        financing = make_document(
            "https://example.com/financing",
            "Beambox 融资动态",
            "同创伟业投资 Beambox。",
        )
        product = make_document(
            "https://example.com/product",
            "Beambox 产品",
            "电子吧唧和可穿戴显示。",
        )
        self.knowledge_base.upsert(financing)
        self.knowledge_base.upsert(product)

        result = self.knowledge_base.search("融资", limit=2)

        self.assertEqual(result["results"][0]["document_id"], financing.id)
        self.assertEqual(result["results"][0]["source_type"], "媒体报道")

    def test_upsert_updates_same_url_without_duplicate(self) -> None:
        original = make_document("https://example.com/a", "旧标题", "旧内容")
        updated = make_document("https://example.com/a", "新标题", "新内容")
        self.knowledge_base.upsert(original)
        self.knowledge_base.upsert(updated)

        self.assertEqual(self.knowledge_base.stats()["document_count"], 1)
        self.assertEqual(
            self.knowledge_base.get_document(updated.id)["title"], "新标题"
        )

    def test_builder_stores_readable_full_text(self) -> None:
        builder = KnowledgeBaseBuilder(self.knowledge_base, FakeSourceTool())

        result = builder.build(
            [
                {
                    "id": "financing",
                    "name": "融资动态",
                    "query": "融资",
                    "max_results": 2,
                }
            ]
        )

        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["stats"]["by_status"], {"full_text": 1})

    def test_get_document_rejects_invalid_id(self) -> None:
        with self.assertRaises(ValueError):
            self.knowledge_base.get_document("../secret")

    def test_official_site_crawler_marks_first_party_source(self) -> None:
        crawler = OfficialSiteCrawler(self.knowledge_base, FakeOfficialSourceTool())
        result = crawler.crawl(
            [
                {
                    "topic": "products_badge",
                    "topic_name": "电子吧唧与可穿戴产品",
                    "url": "https://beambox.com.cn/products/beambox-e-badge-nano",
                }
            ]
        )

        self.assertEqual(result["processed"], 1)
        match = self.knowledge_base.search("Nano", limit=1)["results"][0]
        self.assertEqual(match["source_type"], "品牌官网（企业自述）")
        self.assertEqual(_source_type("https://www.beambox.com.cn/pages/about"), "品牌官网（企业自述）")


if __name__ == "__main__":
    unittest.main()
