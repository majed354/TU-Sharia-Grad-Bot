"""محرك RAG — البحث في المستندات وتوليد الإجابات"""

import logging
import json
import httpx
from dataclasses import dataclass
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RAGResult:
    """نتيجة البحث والتوليد"""
    answer: str
    confidence: str          # high / medium / low
    sources: list[str]       # المقاطع المُسترجعة
    similarity_scores: list[float]
    needs_escalation: bool


class RAGEngine:
    """محرك الاسترجاع والتوليد"""

    def __init__(self):
        self._embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self._vectorstore = Chroma(
            collection_name=settings.chroma_collection,
            embedding_function=self._embeddings,
            persist_directory=settings.chroma_persist_dir,
        )
        self._http_client = httpx.AsyncClient(timeout=60.0)
        logger.info("✅ محرك RAG جاهز")

    async def query(self, question: str) -> RAGResult:
        """معالجة سؤال المستخدم"""

        # --- 1. البحث في قاعدة المعرفة ---
        results = self._vectorstore.similarity_search_with_relevance_scores(
            question,
            k=settings.top_k_results,
        )

        if not results:
            logger.info(f"لم يتم العثور على نتائج للسؤال: {question[:50]}")
            return RAGResult(
                answer="",
                confidence="low",
                sources=[],
                similarity_scores=[],
                needs_escalation=True,
            )

        docs, scores = zip(*results)
        scores = list(scores)
        sources = [doc.page_content for doc in docs]
        metadata = [doc.metadata for doc in docs]

        # --- 2. فحص درجة التشابه ---
        best_score = max(scores)
        logger.info(f"أعلى درجة تشابه: {best_score:.3f} (عتبة: {settings.similarity_threshold})")

        if best_score < settings.similarity_threshold:
            return RAGResult(
                answer="عذراً، لم أتمكن من إيجاد معلومات كافية للإجابة على سؤالك.",
                confidence="low",
                sources=sources,
                similarity_scores=scores,
                needs_escalation=True,
            )

        # --- 3. تجهيز السياق ---
        context_parts = []
        for i, (doc, score) in enumerate(zip(docs, scores)):
            src = doc.metadata.get("source", "غير محدد")
            context_parts.append(
                f"[مقطع {i+1} | المصدر: {src} | التشابه: {score:.2f}]\n{doc.page_content}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # --- 4. توليد الإجابة عبر Kimi 2.5 ---
        answer, confidence = await self._generate_answer(question, context)

        needs_escalation = confidence == "low"

        return RAGResult(
            answer=answer,
            confidence=confidence,
            sources=sources,
            similarity_scores=scores,
            needs_escalation=needs_escalation,
        )

    async def _generate_answer(self, question: str, context: str) -> tuple[str, str]:
        """توليد الإجابة عبر OpenRouter (Kimi 2.5)"""

        system_prompt = """أنت مساعد ذكي متخصص في الإجابة عن تساؤلات الدراسات العليا.

## القواعد:
1. أجب **فقط** بناءً على المعلومات الموجودة في السياق المُقدم أدناه.
2. إذا لم تجد الإجابة في السياق، قل ذلك بوضوح ولا تختلق معلومات.
3. أجب بالعربية بأسلوب واضح ومباشر.
4. إذا كان السؤال يحتاج تفاصيل غير موجودة في السياق، اذكر ما تعرفه واقترح التواصل مع المختص.

## التقييم:
في نهاية إجابتك، أضف سطراً جديداً بالتنسيق التالي فقط:
CONFIDENCE: high أو medium أو low

- high: الإجابة كاملة وواضحة من السياق
- medium: الإجابة جزئية أو تحتاج تأكيد
- low: لم تجد معلومات كافية"""

        user_message = f"""## السياق من قاعدة المعرفة:
{context}

## سؤال المستخدم:
{question}

أجب على السؤال بناءً على السياق أعلاه فقط."""

        try:
            response = await self._http_client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openrouter_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
            )
            response.raise_for_status()
            data = response.json()
            full_answer = data["choices"][0]["message"]["content"].strip()

            # استخراج مستوى الثقة
            confidence = "medium"
            answer = full_answer
            for level in ["high", "medium", "low"]:
                tag = f"CONFIDENCE: {level}"
                if tag in full_answer:
                    confidence = level
                    answer = full_answer.replace(tag, "").strip()
                    break

            return answer, confidence

        except Exception as e:
            logger.error(f"خطأ في توليد الإجابة: {e}")
            return "حدث خطأ أثناء معالجة سؤالك. يرجى المحاولة لاحقاً.", "low"

    def get_collection_count(self) -> int:
        """عدد المقاطع في قاعدة المعرفة"""
        try:
            collection = self._vectorstore._collection
            return collection.count()
        except Exception:
            return 0

    async def close(self):
        await self._http_client.aclose()


# Singleton
_engine: RAGEngine | None = None


def get_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
