"""
文档加载示例
"""

from pathlib import Path

from langchain_community.document_loaders import (
    DirectoryLoader,
    Docx2txtLoader,
    PDFMinerLoader,
    TextLoader,
)

DOCUMENT_DIR = Path(__file__).parent / "doc"

# 加载 PDF 文件。
pdf_loader = PDFMinerLoader(str(DOCUMENT_DIR / "test_document.pdf"))
pdf_docs = pdf_loader.load()

# 加载 DOCX 文件。
docx_loader = Docx2txtLoader(str(DOCUMENT_DIR / "test_document.docx"))
docx_docs = docx_loader.load()

# 加载 UTF-8 文本文件。
text_loader = TextLoader(str(DOCUMENT_DIR / "test_document.txt"), encoding="utf-8")
text_docs = text_loader.load()

# 批量加载目录下所有 TXT 文件。
dir_loader = DirectoryLoader(
    str(DOCUMENT_DIR),
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
)
all_docs = dir_loader.load()

for name, documents in {
    "PDF": pdf_docs,
    "DOCX": docx_docs,
    "TXT": text_docs,
    "目录 TXT": all_docs,
}.items():
    preview = documents[0].page_content[:80].replace("\n", " ") if documents else ""
    print(f"{name}: {len(documents)} 个文档，预览：{preview}")
