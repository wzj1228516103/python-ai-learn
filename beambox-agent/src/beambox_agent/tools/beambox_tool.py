"""公开资料工具：搜索目标公司、读取网页，并阻止访问本机或内网地址。"""

from __future__ import annotations

# ipaddress：判断 URL 是否指向私有/保留 IP，降低 SSRF 风险。
import ipaddress
# json：工具注册表与模型之间统一使用 JSON 字符串传递结构化结果。
import json
# dataclass：简化工具客户端的初始化参数声明。
from dataclasses import dataclass
# Any：描述搜索结果等动态字典结构。
from typing import Any
# urljoin/urlparse：补全搜索结果链接并拆解 URL 做安全校验。
from urllib.parse import urljoin, urlparse

# requests：复用 HTTP 会话，完成搜索和网页读取。
import requests
# BeautifulSoup：使用 HTML 解析器提取标题、摘要和可读正文。
from bs4 import BeautifulSoup

# KnowledgeBase：本地 SQLite 知识库；在线工具与本地工具共享同一注册表。
from ..knowledge_base import KnowledgeBase


# 固定搜索入口和目标实体名称，防止模型把同名 Beambox 搜成其他产品。
SEARCH_URL = "https://www.baidu.com/s"
COMPANY_NAME = "深圳光胜人工智能科技有限公司"
BRAND_NAME = "Beambox"


def _plain_text(html: str | None) -> str:
    """删除脚本、样式等非正文节点，并把 HTML 压缩成模型可读纯文本。"""

    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # 主动移除不可见、交互控件或可能包含提示注入噪声的节点。
    for element in soup(["script", "style", "noscript", "svg", "form", "dialog"]):
        element.decompose()
    # Shopify 等商城会在页头放入全部国家/地区选项；优先读取 main 可显著减少噪声。
    content_root = soup.select_one("main#MainContent") or soup.select_one("main") or soup
    for element in content_root.select("button, [hidden], .visually-hidden"):
        element.decompose()
    return " ".join(content_root.get_text(" ", strip=True).split())


def _validate_public_url(url: str) -> str:
    """只允许公开 HTTP(S) URL，拒绝 localhost、私网和保留 IP。"""

    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("只允许读取公开的 HTTP 或 HTTPS 网页")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("不允许访问本机地址")
    # 域名无法直接交给 ip_address；只有字面 IP 才进入地址范围判断。
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ValueError("不允许访问内网或保留地址")
    return url.strip()


@dataclass
class BeamboxCompanyTool:
    """封装公司搜索和网页读取；session 参数允许测试时注入模拟 HTTP。"""

    # 单次 HTTP 请求超时秒数。
    timeout: float = 20.0
    # Session 复用连接和请求头；默认由 __post_init__ 创建。
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        """创建会话，并设置中文偏好与常见浏览器 User-Agent。"""

        if self.session is None:
            self.session = requests.Session()
        self._configure_session_headers()

    def _configure_session_headers(self) -> None:
        """集中设置请求头，供初始化和批量采集重建会话时复用。"""

        self.session.headers.update(
            {
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
                ),
            }
        )

    def reset_session(self) -> None:
        """为下一个采集主题创建无 Cookie 的独立 HTTP 会话。"""

        self.session = requests.Session()
        self._configure_session_headers()

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """把用户检索词限定到目标公司，解析最多 8 条百度网页结果。"""

        # 先验证模型传入参数，避免空查询或异常超长请求。
        query = query.strip()
        if not query:
            raise ValueError("query 不能为空")
        if len(query) > 200:
            raise ValueError("query 不能超过 200 个字符")

        # 即使模型传入越界数字，也把结果数收敛到 1~8。
        selected_limit = max(1, min(int(limit), 8))
        # 每次都附加公司全称和品牌名，降低搜索到同名产品的概率。
        scoped_query = f"{COMPANY_NAME} {BRAND_NAME} {query}"
        response = self.session.get(
            SEARCH_URL,
            params={"wd": scoped_query},
            timeout=self.timeout,
        )
        response.raise_for_status()
        # 部分站点未声明中文编码，requests 会误判为 ISO-8859-1。
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []
        # 百度每条自然搜索结果通常使用 .result，标题链接位于 h3 a。
        for item in soup.select(".result"):
            anchor = item.select_one("h3 a")
            if not anchor or not anchor.get("href"):
                continue
            title = " ".join(anchor.get_text(" ", strip=True).split())
            url = urljoin(response.url, anchor["href"])
            snippet_element = item.select_one(".c-abstract")
            snippet_source = snippet_element or item
            snippet = " ".join(snippet_source.get_text(" ", strip=True).split())
            if title and snippet.startswith(title):
                snippet = snippet[len(title) :].strip()
            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet[:800],
                }
            )
            if len(results) >= selected_limit:
                break

        return {
            "query": query,
            "searched_query": scoped_query,
            "result_count": len(results),
            "results": results,
        }

    def read_page(self, url: str) -> dict[str, Any]:
        """跟随搜索跳转链接，返回最终来源 URL、标题和清洗后的正文。"""

        # 请求前和重定向后各校验一次，防止公开 URL 跳入内网。
        requested_url = _validate_public_url(url)
        response = self.session.get(
            requested_url,
            timeout=self.timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        final_url = _validate_public_url(response.url)
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")
        title = ""
        if soup.title:
            title = " ".join(soup.title.get_text(" ", strip=True).split())
        body = _plain_text(response.text)
        # 限制正文长度，避免单页内容耗尽模型上下文窗口。
        max_length = 18_000
        return {
            "source_url": requested_url,
            "url": final_url,
            "title": title,
            "body": body[:max_length],
            "truncated": len(body) > max_length,
        }


# OpenAI function calling 的 JSON Schema；模型通过它理解工具名和参数。
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_beambox_knowledge_base",
            "description": (
                "优先搜索本地 Beambox 知识库，返回文档 ID、主题、来源类型、更新时间和摘要。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用户问题或检索关键词"},
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_knowledge_document",
            "description": "按本地知识库搜索结果中的 document_id 读取完整文档和来源元数据。",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "search_beambox_knowledge_base 返回的 16 位文档 ID",
                    }
                },
                "required": ["document_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_beambox_company_info",
            "description": (
                "搜索深圳光胜人工智能科技有限公司及旗下 Beambox 品牌的公开信息，"
                "包括企业、产品、融资、团队、招聘、市场和媒体资料。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "具体资料问题或检索词"},
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 8,
                        "default": 5,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_public_page",
            "description": (
                "读取搜索结果中的公开网页正文。传入 search_beambox_company_info "
                "真实返回的 URL，不得自行拼接地址。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "搜索结果返回的公开网页 URL",
                    }
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
]


class ToolRegistry:
    """把模型返回的函数名路由到真实 Python 方法，并统一异常格式。"""

    def __init__(
        self,
        company: BeamboxCompanyTool,
        knowledge_base: KnowledgeBase | None = None,
    ):
        self.company = company
        self.knowledge_base = knowledge_base or KnowledgeBase()

    @property
    def definitions(self) -> list[dict[str, Any]]:
        """提供给 Chat Completions API 的工具定义列表。"""

        return TOOL_DEFINITIONS

    def execute(self, name: str, arguments_json: str) -> str:
        """解析模型参数、执行对应工具，并始终返回 JSON 字符串。"""

        try:
            arguments = json.loads(arguments_json or "{}")
            if name == "search_beambox_knowledge_base":
                result = self.knowledge_base.search(**arguments)
            elif name == "get_knowledge_document":
                result = self.knowledge_base.get_document(**arguments)
            elif name == "search_beambox_company_info":
                result = self.company.search(**arguments)
            elif name == "read_public_page":
                result = self.company.read_page(**arguments)
            else:
                raise ValueError(f"未知工具: {name}")
            return json.dumps(result, ensure_ascii=False)
        # 把可预期错误返回给模型，让模型有机会改参数或说明资料不可用。
        except (ValueError, TypeError, KeyError, requests.RequestException) as exc:
            return json.dumps(
                {"error": str(exc), "tool": name},
                ensure_ascii=False,
            )


# Backward-compatible import for existing integrations.
BeamboxDocsTool = BeamboxCompanyTool
