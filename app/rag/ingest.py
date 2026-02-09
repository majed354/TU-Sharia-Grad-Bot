"""تجهيز المستندات — تقطيع وتخزين في ChromaDB"""

import os
import sys
import logging
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

# إضافة المسار الجذري
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DOCUMENTS_DIR = Path(__file__).resolve().parent.parent.parent / "documents"


def load_text_files() -> list[Document]:
    """تحميل جميع ملفات .txt من مجلد documents/"""
    documents = []

    if not DOCUMENTS_DIR.exists():
        logger.error(f"❌ مجلد المستندات غير موجود: {DOCUMENTS_DIR}")
        return documents

    txt_files = list(DOCUMENTS_DIR.glob("*.txt"))
    if not txt_files:
        logger.warning("⚠️ لا توجد ملفات .txt في مجلد documents/")
        return documents

    for filepath in txt_files:
        try:
            content = filepath.read_text(encoding="utf-8")
            if content.strip():
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": filepath.name,
                        "file_path": str(filepath),
                    }
                )
                documents.append(doc)
                logger.info(f"📄 تم تحميل: {filepath.name} ({len(content)} حرف)")
        except Exception as e:
            logger.error(f"❌ خطأ في قراءة {filepath.name}: {e}")

    logger.info(f"📚 إجمالي المستندات المُحمّلة: {len(documents)}")
    return documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    """تقطيع المستندات إلى مقاطع"""
    settings = get_settings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", "،", "؟", "!", " "],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)
    logger.info(f"✂️ تم التقطيع إلى {len(chunks)} مقطع")
    return chunks


def store_in_chromadb(chunks: list[Document]):
    """تخزين المقاطع في ChromaDB"""
    settings = get_settings()

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )

    # حذف المجموعة القديمة وإنشاء جديدة
    persist_dir = settings.chroma_persist_dir
    os.makedirs(persist_dir, exist_ok=True)

    logger.info("🧠 جارٍ إنشاء Embeddings وتخزينها...")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=settings.chroma_collection,
        persist_directory=persist_dir,
    )

    count = vectorstore._collection.count()
    logger.info(f"✅ تم تخزين {count} مقطع في ChromaDB بنجاح!")
    return vectorstore


def main():
    """تشغيل عملية التجهيز الكاملة"""
    logger.info("=" * 60)
    logger.info("🚀 بدء تجهيز قاعدة المعرفة")
    logger.info("=" * 60)

    # 1. تحميل المستندات
    documents = load_text_files()
    if not documents:
        logger.error("❌ لا توجد مستندات لمعالجتها. ضع ملفات .txt في مجلد documents/")
        sys.exit(1)

    # 2. تقطيع
    chunks = chunk_documents(documents)

    # 3. تخزين
    store_in_chromadb(chunks)

    logger.info("=" * 60)
    logger.info("🎉 تم تجهيز قاعدة المعرفة بنجاح!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
