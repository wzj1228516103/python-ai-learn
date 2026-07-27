"""Beambox 本地知识库：采集公开网页、存入 SQLite，并提供可解释检索。"""

from __future__ import annotations

# argparse：提供 build/crawl-official/search/stats/export 知识库命令。
import argparse
# hashlib：生成稳定文档 ID 和正文内容哈希。
import hashlib
# re：把中英文问题拆成检索词。
import re
# sqlite3：Python 内置数据库，无需额外服务即可保存知识文档。
import sqlite3
# sys：统一 Windows 控制台编码。
import sys
# time：批量采集时控制搜索节奏，降低搜索端临时降级概率。
import time
# dataclass：定义结构明确的知识文档对象。
from dataclasses import asdict, dataclass
# closing：确保 sqlite3.Connection 在 Windows 上及时关闭并释放文件锁。
from contextlib import closing
# datetime：记录资料抓取时间，便于判断知识新鲜度。
from datetime import datetime, timezone
# Path：定位默认数据库、主题配置和 Markdown 导出文件。
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

# PyYAML：读取 config/knowledge_topics.yaml 的采集主题。
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "beambox_knowledge.sqlite3"
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "data" / "beambox_knowledge.md"
TOPICS_PATH = Path(__file__).with_name("config") / "knowledge_topics.yaml"

# 官网站点地图包含数千篇高度相似的 SEO 文章。这里仅保留产品、企业说明、
# 使用指南和真实更新/里程碑页面，防止模板化内容淹没高价值资料。
OFFICIAL_SITE_SOURCES: tuple[dict[str, str], ...] = (
    {
        "topic": "brand_positioning",
        "topic_name": "品牌定位",
        "url": "https://beambox.com.cn/",
    },
    {
        "topic": "brand_positioning",
        "topic_name": "品牌定位",
        "url": "https://beambox.com.cn/agents.md",
    },
    {
        "topic": "company_profile",
        "topic_name": "企业基本信息",
        "url": "https://beambox.com.cn/pages/about",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/products/beambox-e-badge-nano",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/products/beambox-nikko-e-badge",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/products/niji-e-badge",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/pages/beambox-e-badge-answer-hub",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/pages/beambox-pin-e-badge-guide",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/blogs/info/what-is-an-e-badge",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/blogs/magnetic-mount/magnetic-mount",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/blogs/magnetic-mount/pin-on-style",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/blogs/magnetic-mount/lanyard-style",
    },
    {
        "topic": "products_badge",
        "topic_name": "电子吧唧与可穿戴产品",
        "url": "https://beambox.com.cn/blogs/magnetic-mount/stand-placement",
    },
    {
        "topic": "products_companion",
        "topic_name": "AI Companion 与陪伴硬件",
        "url": "https://beambox.com.cn/products/beambot-ai-pet-companion",
    },
    {
        "topic": "products_companion",
        "topic_name": "AI Companion 与陪伴硬件",
        "url": "https://beambox.com.cn/pages/beampet-ai-ai-pet-companion",
    },
    {
        "topic": "products_companion",
        "topic_name": "AI Companion 与陪伴硬件",
        "url": "https://beambox.com.cn/pages/polly-ip-growth-system",
    },
    {
        "topic": "market_channels",
        "topic_name": "市场与渠道",
        "url": "https://beambox.com.cn/pages/event-team-electronic-badge-packs",
    },
    {
        "topic": "milestones",
        "topic_name": "品牌动态与里程碑",
        "url": "https://beambox.com.cn/blogs/info/update-announcement-beambox-app-version-1-0-7-release",
    },
    {
        "topic": "milestones",
        "topic_name": "品牌动态与里程碑",
        "url": "https://beambox.com.cn/blogs/info/crowdfunding-success-beambox-s-electronic-badge-nikko-officially-launches-on-makuake-and-shines-at-tokyo-comic-con",
    },
)


@dataclass(frozen=True)
class KnowledgeDocument:
    """一条可追溯知识文档；status 区分全文和仅搜索摘要。"""

    id: str
    topic: str
    topic_name: str
    title: str
    url: str
    source_url: str
    source_type: str
    content: str
    status: str
    retrieved_at: str
    content_hash: str


def _stable_id(url: str) -> str:
    """根据最终 URL 生成短而稳定的文档 ID。"""

    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _content_hash(content: str) -> str:
    """记录正文版本；更新时可判断页面内容是否发生变化。"""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _search_tokens(text: str) -> set[str]:
    """提取英文单词、数字、中文词串和中文双字组合。"""

    normalized = text.lower()
    tokens = set(re.findall(r"[a-z0-9]+", normalized))
    for sequence in re.findall(r"[\u4e00-\u9fff]+", normalized):
        tokens.add(sequence)
        if len(sequence) > 1:
            tokens.update(sequence[index : index + 2] for index in range(len(sequence) - 1))
    return {token for token in tokens if token.strip()}


def _source_type(url: str) -> str:
    """按域名粗分来源性质，回答时可提示证据等级。"""

    host = (urlparse(url).hostname or "").lower()
    if host == "beambox.com.cn" or host.endswith(".beambox.com.cn"):
        return "品牌官网（企业自述）"
    if host.endswith("gov.cn"):
        return "政府或监管资料"
    if any(name in host for name in ("aiqicha", "qcc.com", "tianyancha", "qizhidao")):
        return "企业信息平台"
    if "zhipin.com" in host:
        return "招聘平台"
    if "china-toy-expo.com" in host:
        return "展会资料"
    if "1688.com" in host:
        return "电商或供应链平台"
    media_hosts = (
        "10jqka.com.cn",
        "iyiou.com",
        "toutiao.com",
        "qq.com",
        "163.com",
        "chinadaily.com.cn",
        "china.com.cn",
    )
    if any(name in host for name in media_hosts):
        return "媒体报道"
    return "公开网页"


class KnowledgeBase:
    """SQLite 存储与本地加权检索层。"""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        """创建表，并把早期“URL 唯一”结构迁移为“主题 + URL 唯一”。"""

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            existing = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='documents'"
            ).fetchone()
            legacy_rows: list[dict[str, Any]] = []
            if existing and "url TEXT NOT NULL UNIQUE" in existing["sql"]:
                # 迁移前先完整读入内存；后续 DDL 和插入在同一事务中提交。
                legacy_rows = [
                    dict(row) for row in connection.execute("SELECT * FROM documents")
                ]
                connection.execute("DROP TABLE documents")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    topic_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    UNIQUE(url, topic)
                )
                """
            )
            for row in legacy_rows:
                row["id"] = _stable_id(f"{row['topic']}:{row['url']}")
                connection.execute(
                    """
                    INSERT OR IGNORE INTO documents (
                        id, topic, topic_name, title, url, source_url,
                        source_type, content, status, retrieved_at, content_hash
                    ) VALUES (
                        :id, :topic, :topic_name, :title, :url, :source_url,
                        :source_type, :content, :status, :retrieved_at, :content_hash
                    )
                    """,
                    row,
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_topic ON documents(topic)"
            )
            connection.commit()

    def upsert(self, document: KnowledgeDocument) -> None:
        """按最终 URL 插入或更新，重复采集不会制造重复文档。"""

        self.initialize()
        values = asdict(document)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, topic, topic_name, title, url, source_url,
                    source_type, content, status, retrieved_at, content_hash
                ) VALUES (
                    :id, :topic, :topic_name, :title, :url, :source_url,
                    :source_type, :content, :status, :retrieved_at, :content_hash
                )
                ON CONFLICT(url, topic) DO UPDATE SET
                    topic_name=excluded.topic_name,
                    title=excluded.title,
                    source_url=excluded.source_url,
                    source_type=excluded.source_type,
                    content=excluded.content,
                    status=excluded.status,
                    retrieved_at=excluded.retrieved_at,
                    content_hash=excluded.content_hash
                """,
                values,
            )
            connection.commit()

    def _all_documents(self) -> list[KnowledgeDocument]:
        if not self.db_path.exists():
            return []
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT * FROM documents").fetchall()
        return [KnowledgeDocument(**dict(row)) for row in rows]

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """使用标题/主题/正文加权评分，返回最相关文档和局部摘要。"""

        query = query.strip()
        if not query:
            raise ValueError("query 不能为空")
        selected_limit = max(1, min(int(limit), 10))
        query_lower = query.lower()
        tokens = _search_tokens(query)
        scored: list[tuple[int, KnowledgeDocument]] = []

        for document in self._all_documents():
            title = document.title.lower()
            topic = f"{document.topic} {document.topic_name}".lower()
            content = document.content.lower()
            score = 0
            if query_lower in title:
                score += 20
            if query_lower in content:
                score += 10
            for token in tokens:
                score += title.count(token) * 5
                score += topic.count(token) * 3
                score += min(content.count(token), 5)
            if score:
                # 官网全文是第一方资料，适合确认产品规格和品牌自述；小幅加权但不压过相关性。
                if document.source_type == "品牌官网（企业自述）":
                    score += 5
                if document.status == "full_text":
                    score += 2
                scored.append((score, document))

        scored.sort(key=lambda item: (item[0], item[1].retrieved_at), reverse=True)
        results = []
        for score, document in scored[:selected_limit]:
            content_lower = document.content.lower()
            positions = [content_lower.find(token) for token in tokens if token in content_lower]
            start = max(0, min(positions) - 120) if positions else 0
            excerpt = document.content[start : start + 900]
            results.append(
                {
                    "document_id": document.id,
                    "topic": document.topic_name,
                    "title": document.title,
                    "source_type": document.source_type,
                    "status": document.status,
                    "url": document.url,
                    "retrieved_at": document.retrieved_at,
                    "score": score,
                    "excerpt": excerpt,
                }
            )
        return {"query": query, "result_count": len(results), "results": results}

    def get_document(self, document_id: str) -> dict[str, Any]:
        """按搜索结果中的 ID 读取完整知识文档。"""

        if not re.fullmatch(r"[0-9a-f]{16}", document_id):
            raise ValueError("document_id 格式错误")
        if not self.db_path.exists():
            raise ValueError("知识库尚未构建，请先运行 beambox-kb build")
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
        if row is None:
            raise ValueError(f"知识库中不存在文档: {document_id}")
        return dict(row)

    def stats(self) -> dict[str, Any]:
        """统计总文档数、全文/摘要数量和各主题覆盖量。"""

        if not self.db_path.exists():
            return {"document_count": 0, "by_status": {}, "by_topic": {}}
        with closing(sqlite3.connect(self.db_path)) as connection:
            total = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            status_rows = connection.execute(
                "SELECT status, COUNT(*) FROM documents GROUP BY status"
            ).fetchall()
            topic_rows = connection.execute(
                "SELECT topic_name, COUNT(*) FROM documents GROUP BY topic_name"
            ).fetchall()
        return {
            "document_count": total,
            "by_status": dict(status_rows),
            "by_topic": dict(topic_rows),
        }

    def export_markdown(self, output_path: str | Path = DEFAULT_EXPORT_PATH) -> Path:
        """导出人类可阅读的目录、来源和内容摘要。"""

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        documents = sorted(
            self._all_documents(), key=lambda item: (item.topic_name, item.title)
        )
        lines = [
            "# Beambox 本地知识库",
            "",
            f"生成时间：{datetime.now(timezone.utc).isoformat()}",
            "",
            "> 目标对象：深圳光胜人工智能科技有限公司及旗下 Beambox 品牌。",
            "",
        ]
        current_topic = ""
        for document in documents:
            if document.topic_name != current_topic:
                current_topic = document.topic_name
                lines.extend([f"## {current_topic}", ""])
            # split/join 同时清除网页正文中的换行、回车和尾部空格。
            safe_title = " ".join(document.title.split())
            excerpt = " ".join(document.content[:600].split())
            lines.extend(
                [
                    f"### {safe_title}",
                    "",
                    f"- 来源类型：{document.source_type}",
                    f"- 抓取状态：{document.status}",
                    f"- 更新时间：{document.retrieved_at}",
                    f"- 来源链接：{document.url}",
                    f"- 文档 ID：`{document.id}`",
                    "",
                    excerpt,
                    "",
                ]
            )
        # 固定 LF，避免 Windows 的 CRLF 在 Git 差异检查中被误报为行尾空白。
        with output.open("w", encoding="utf-8", newline="\n") as file:
            file.write("\n".join(lines))
        return output


def load_topics(path: str | Path = TOPICS_PATH) -> list[dict[str, Any]]:
    """读取并校验采集主题列表。"""

    with Path(path).open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)
    topics = payload.get("topics", []) if isinstance(payload, dict) else []
    if not topics:
        raise ValueError("knowledge_topics.yaml 中没有可用主题")
    return topics


class KnowledgeBaseBuilder:
    """把在线搜索工具的结果转为可更新的本地知识文档。"""

    def __init__(self, knowledge_base: KnowledgeBase, source_tool: Any) -> None:
        self.knowledge_base = knowledge_base
        self.source_tool = source_tool

    def build(self, topics: Iterable[dict[str, Any]]) -> dict[str, Any]:
        """逐主题采集；无法读取正文时降级保存搜索摘要。"""

        processed = 0
        skipped = 0
        for topic in topics:
            # 真实网页工具支持重建会话；测试替身没有该方法时直接跳过。
            reset_session = getattr(self.source_tool, "reset_session", None)
            if callable(reset_session):
                reset_session()
            result = self.source_tool.search(
                topic["query"], limit=int(topic.get("max_results", 3))
            )
            # 长检索词无结果时退回短主题名，避免搜索引擎过度收窄。
            if not result.get("results"):
                time.sleep(0.4)
                result = self.source_tool.search(
                    topic["name"], limit=int(topic.get("max_results", 3))
                )
            # seed_urls 是人工确认过的稳定来源，搜索不可用时仍能保证核心主题覆盖。
            seed_candidates = [
                {
                    "title": f"{topic['name']}核心来源",
                    "url": url,
                    "snippet": f"Beambox 光胜 {topic['name']}",
                }
                for url in topic.get("seed_urls", [])
            ]
            candidates = seed_candidates + result.get("results", [])
            seen_candidate_urls: set[str] = set()
            for candidate in candidates:
                if candidate["url"] in seen_candidate_urls:
                    continue
                seen_candidate_urls.add(candidate["url"])
                relevance_text = f"{candidate.get('title', '')} {candidate.get('snippet', '')}".lower()
                if "beambox" not in relevance_text and "光胜" not in relevance_text:
                    skipped += 1
                    continue

                source_url = candidate["url"]
                title = candidate.get("title") or source_url
                final_url = source_url
                content = candidate.get("snippet", "")
                status = "search_snippet"
                try:
                    page = self.source_tool.read_page(source_url)
                    if len(page.get("body", "")) >= 200:
                        final_url = page["url"]
                        title = page.get("title") or title
                        content = page["body"]
                        status = "full_text"
                except Exception:
                    # 页面反爬或临时不可用时保留摘要，状态会提醒模型降低证据权重。
                    pass

                if not content.strip():
                    skipped += 1
                    continue
                retrieved_at = datetime.now(timezone.utc).isoformat()
                document = KnowledgeDocument(
                    # 同一来源可同时属于多个主题，因此 ID 同时包含 topic 和 URL。
                    id=_stable_id(f"{topic['id']}:{final_url}"),
                    topic=topic["id"],
                    topic_name=topic["name"],
                    title=title,
                    url=final_url,
                    source_url=source_url,
                    source_type=_source_type(final_url),
                    content=content,
                    status=status,
                    retrieved_at=retrieved_at,
                    content_hash=_content_hash(content),
                )
                self.knowledge_base.upsert(document)
                processed += 1

            # 批量任务主动降速，减少搜索服务返回验证页或空白结果页。
            time.sleep(0.5)

        return {
            "processed": processed,
            "skipped": skipped,
            "stats": self.knowledge_base.stats(),
        }


class OfficialSiteCrawler:
    """采集官网精选页面；跳过站点地图中的模板化 SEO 页面和多语言重复页。"""

    def __init__(self, knowledge_base: KnowledgeBase, source_tool: Any) -> None:
        self.knowledge_base = knowledge_base
        self.source_tool = source_tool

    def crawl(
        self,
        sources: Iterable[dict[str, str]] = OFFICIAL_SITE_SOURCES,
    ) -> dict[str, Any]:
        """读取官网正文并增量写入数据库，失败页面会单独列出而不中断批次。"""

        processed = 0
        skipped = 0
        skipped_urls: list[str] = []
        errors: list[dict[str, str]] = []
        reset_session = getattr(self.source_tool, "reset_session", None)
        if callable(reset_session):
            reset_session()

        for source in sources:
            source_url = source["url"]
            try:
                page = self.source_tool.read_page(source_url)
            except Exception as exc:
                errors.append({"url": source_url, "error": str(exc)})
                continue

            content = page.get("body", "").strip()
            if len(content) < 200:
                skipped += 1
                skipped_urls.append(source_url)
                continue
            final_url = page.get("url") or source_url
            title = page.get("title") or final_url
            retrieved_at = datetime.now(timezone.utc).isoformat()
            self.knowledge_base.upsert(
                KnowledgeDocument(
                    id=_stable_id(f"{source['topic']}:{final_url}"),
                    topic=source["topic"],
                    topic_name=source["topic_name"],
                    title=title,
                    url=final_url,
                    source_url=source_url,
                    source_type=_source_type(final_url),
                    content=content,
                    status="full_text",
                    retrieved_at=retrieved_at,
                    content_hash=_content_hash(content),
                )
            )
            processed += 1
            # 对同一站点主动降速，避免给官网造成突发请求压力。
            time.sleep(0.15)

        return {
            "processed": processed,
            "skipped": skipped,
            "skipped_urls": skipped_urls,
            "errors": errors,
            "stats": self.knowledge_base.stats(),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建和查询 Beambox 本地知识库")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite 数据库路径")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="根据主题配置采集并更新知识库")
    subparsers.add_parser(
        "crawl-official",
        help="抓取 beambox.com.cn 的精选官网页面并更新知识库",
    )
    search_parser = subparsers.add_parser("search", help="搜索本地知识库")
    search_parser.add_argument("query", help="检索问题或关键词")
    search_parser.add_argument("--limit", type=int, default=5)
    subparsers.add_parser("stats", help="显示知识库统计")
    export_parser = subparsers.add_parser("export", help="导出 Markdown 目录")
    export_parser.add_argument("--output", default=str(DEFAULT_EXPORT_PATH))
    return parser


def main() -> None:
    """知识库维护命令入口。"""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args()
    knowledge_base = KnowledgeBase(args.db)

    if args.command == "build":
        # 延迟导入避免 knowledge_base 与 tools 模块互相循环依赖。
        from .config import Settings
        from .tools import BeamboxCompanyTool

        settings = Settings.from_env()
        source_tool = BeamboxCompanyTool(timeout=settings.request_timeout)
        builder = KnowledgeBaseBuilder(knowledge_base, source_tool)
        print(builder.build(load_topics()))
        print(f"Markdown: {knowledge_base.export_markdown()}")
    elif args.command == "crawl-official":
        # 官网采集不调用大模型，因此不要求配置 API Key。
        from .tools import BeamboxCompanyTool

        crawler = OfficialSiteCrawler(
            knowledge_base,
            BeamboxCompanyTool(timeout=30),
        )
        print(crawler.crawl())
        print(f"Markdown: {knowledge_base.export_markdown()}")
    elif args.command == "search":
        print(knowledge_base.search(args.query, args.limit))
    elif args.command == "stats":
        print(knowledge_base.stats())
    elif args.command == "export":
        print(knowledge_base.export_markdown(args.output))


if __name__ == "__main__":
    main()
