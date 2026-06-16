import asyncio
import re
import math
from typing import List, Dict, Tuple, Set
from collections import Counter


# ──────────────────────────────────────────────
# Document Store – 10 policy documents
# ──────────────────────────────────────────────

DOCUMENTS: Dict[str, Dict[str, str]] = {
    "doc_01": {
        "title": "Password reset policy",
        "text": (
            "Users reset passwords from Account Settings > Security. The reset "
            "link expires after 15 minutes. Support staff must never ask for or "
            "store a user's current password."
        ),
    },
    "doc_02": {
        "title": "Refund policy",
        "text": (
            "Customers can request a refund within 30 days of purchase if usage "
            "is below 20% of the monthly quota. Enterprise contracts follow the "
            "signed order form instead of the public refund policy."
        ),
    },
    "doc_03": {
        "title": "Data retention policy",
        "text": (
            "Chat logs are retained for 90 days by default. Audit logs are kept "
            "for 365 days. Enterprise customers may request shorter retention "
            "through a data processing addendum."
        ),
    },
    "doc_04": {
        "title": "Model routing policy",
        "text": (
            "Simple FAQ questions should use the small model. High-risk legal, "
            "medical, or financial questions must be escalated to a human or a "
            "specialized review workflow."
        ),
    },
    "doc_05": {
        "title": "Incident response policy",
        "text": (
            "Severity 1 incidents require acknowledgement within 15 minutes and "
            "customer updates every 30 minutes until mitigation. Severity 3 "
            "incidents require one business day response."
        ),
    },
    "doc_06": {
        "title": "Knowledge base boundaries",
        "text": (
            "The assistant may answer only from supplied product documentation. "
            "When the answer is not in context, it must say it does not know and "
            "ask for the relevant document."
        ),
    },
    "doc_07": {
        "title": "Billing plan policy",
        "text": (
            "The Starter plan includes 1,000 messages per month. The Pro plan "
            "includes 20,000 messages per month and email support. The Team plan "
            "adds SSO and shared audit exports."
        ),
    },
    "doc_08": {
        "title": "Conflicting legacy note",
        "text": (
            "Legacy memo from 2022: trial accounts were retained for 180 days. "
            "This memo was superseded by the 2025 data retention policy."
        ),
    },
    "doc_09": {
        "title": "Localization policy",
        "text": (
            "The product supports English and Vietnamese for end-user answers. "
            "Internal audit exports are currently English-only."
        ),
    },
    "doc_10": {
        "title": "File upload policy",
        "text": (
            "Uploaded PDFs must be under 25 MB. CSV files must be under 10 MB. "
            "Executable files are blocked and should never be accepted."
        ),
    },
}

# Keyword → doc_id mapping for direct lookup
KEYWORD_INDEX: Dict[str, List[str]] = {
    # doc_01 - Password
    "password": ["doc_01"], "mật khẩu": ["doc_01"], "reset": ["doc_01"],
    "đặt lại": ["doc_01"], "link": ["doc_01"], "hết hạn": ["doc_01"],
    "expired": ["doc_01"], "security": ["doc_01"], "account": ["doc_01"],
    # doc_02 - Refund
    "refund": ["doc_02"], "hoàn tiền": ["doc_02"], "hoàn": ["doc_02"],
    "30 ngày": ["doc_02"], "30 days": ["doc_02"], "20%": ["doc_02"],
    "quota": ["doc_02"], "enterprise": ["doc_02", "doc_03"],
    "order form": ["doc_02"], "purchase": ["doc_02"],
    # doc_03 - Retention
    "retention": ["doc_03"], "retained": ["doc_03"], "giữ": ["doc_03"],
    "90 ngày": ["doc_03"], "90 days": ["doc_03"], "365": ["doc_03"],
    "chat logs": ["doc_03"], "audit logs": ["doc_03"], "log": ["doc_03"],
    "data retention": ["doc_03"], "lưu trữ": ["doc_03"],
    # doc_04 - Model routing
    "model": ["doc_04"], "small model": ["doc_04"], "FAQ": ["doc_04"],
    "legal": ["doc_04"], "medical": ["doc_04"], "financial": ["doc_04"],
    "escalated": ["doc_04"], "rủi ro": ["doc_04"], "pháp lý": ["doc_04"],
    "review workflow": ["doc_04"],
    # doc_05 - Incident
    "incident": ["doc_05"], "severity": ["doc_05"], "sự cố": ["doc_05"],
    "15 phút": ["doc_05"], "15 minutes": ["doc_05"], "30 phút": ["doc_05"],
    "30 minutes": ["doc_05"], "acknowledge": ["doc_05"], "mitigation": ["doc_05"],
    "phản hồi": ["doc_05"], "response": ["doc_05"],
    # doc_06 - KB boundaries (out-of-context fallback)
    "không biết": ["doc_06"], "out of context": ["doc_06"],
    "not in context": ["doc_06"], "boundary": ["doc_06"],
    # doc_07 - Billing
    "plan": ["doc_07"], "gói": ["doc_07"], "starter": ["doc_07"],
    "pro": ["doc_07"], "team": ["doc_07"], "tin nhắn": ["doc_07"],
    "messages": ["doc_07"], "billing": ["doc_07"], "thanh toán": ["doc_07"],
    "SSO": ["doc_07"], "email support": ["doc_07"], "1,000": ["doc_07"],
    "20,000": ["doc_07"], "1000": ["doc_07"], "20000": ["doc_07"],
    # doc_08 - Legacy
    "legacy": ["doc_08"], "memo": ["doc_08"], "2022": ["doc_08"],
    "180 ngày": ["doc_08"], "180 days": ["doc_08"], "trial": ["doc_08"],
    "superseded": ["doc_08"], "cũ": ["doc_08"],
    # doc_09 - Localization
    "vietnamese": ["doc_09"], "tiếng việt": ["doc_09"], "tiếng Việt": ["doc_09"],
    "english": ["doc_09"], "ngôn ngữ": ["doc_09"], "language": ["doc_09"],
    "localization": ["doc_09"], "audit export": ["doc_09"],
    # doc_10 - File upload
    "upload": ["doc_10"], "PDF": ["doc_10"], "CSV": ["doc_10"],
    "MB": ["doc_10"], "file": ["doc_10"], "executable": ["doc_10"],
    ".exe": ["doc_10"], "25 MB": ["doc_10"], "10 MB": ["doc_10"],
    "tải lên": ["doc_10"], "tệp": ["doc_10"],
}


# ──────────────────────────────────────────────
# Text Processing Utilities
# ──────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    """Tokenize text: lowercase, keep Vietnamese diacritics, split on whitespace/punctuation."""
    text = text.lower()
    # Split on non-alphanumeric and non-Vietnamese chars
    tokens = re.findall(r"[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ0-9]+", text)
    return [t for t in tokens if len(t) > 1]


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Term frequency: count / total tokens."""
    counts = Counter(tokens)
    total = len(tokens)
    if total == 0:
        return {}
    return {term: count / total for term, count in counts.items()}


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vectors."""
    common_terms = set(vec_a.keys()) & set(vec_b.keys())
    dot = sum(vec_a[t] * vec_b[t] for t in common_terms)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ──────────────────────────────────────────────
# BM25 Retrieval Engine
# ──────────────────────────────────────────────

class BM25Retriever:
    """BM25 retriever with keyword boosting and out-of-context fallback."""

    def __init__(self, documents: Dict[str, Dict[str, str]]):
        self.doc_ids: List[str] = list(documents.keys())
        self.documents = documents
        self.doc_texts: List[str] = [
            f"{doc['title']} {doc['title']} {doc['text']}" for doc in documents.values()
        ]
        self.doc_tokens: List[List[str]] = [tokenize(t) for t in self.doc_texts]
        self.avg_dl = sum(len(t) for t in self.doc_tokens) / len(self.doc_tokens)
        self.idf: Dict[str, float] = self._compute_idf()
        self.k1 = 1.5
        self.b = 0.75

    def _compute_idf(self) -> Dict[str, float]:
        """BM25 IDF: log((N - n + 0.5) / (n + 0.5) + 1)."""
        n_docs = len(self.doc_tokens)
        df: Counter = Counter()
        for tokens in self.doc_tokens:
            unique = set(tokens)
            for term in unique:
                df[term] += 1
        idf = {}
        for term, n in df.items():
            idf[term] = math.log((n_docs - n + 0.5) / (n + 0.5) + 1)
        return idf

    def _bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """BM25 score for a single document."""
        doc_tokens = self.doc_tokens[doc_idx]
        doc_len = len(doc_tokens)
        tf = Counter(doc_tokens)
        score = 0.0
        for term in query_tokens:
            if term not in tf:
                continue
            term_freq = tf[term]
            idf_val = self.idf.get(term, 0)
            numerator = term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_dl)
            score += idf_val * numerator / denominator
        return score

    def _keyword_boost(self, query: str, doc_id: str) -> float:
        """Boost score if query contains keywords mapped to this doc."""
        query_lower = query.lower()
        boost = 0.0
        for keyword, doc_ids in KEYWORD_INDEX.items():
            if keyword.lower() in query_lower and doc_id in doc_ids:
                # Longer keywords get higher boost
                boost += len(keyword) * 0.5
        return boost

    def retrieve(self, query: str, top_k: int = 3) -> Tuple[List[str], List[str]]:
        """
        Retrieve top_k documents using BM25 + keyword boosting.
        Returns (doc_ids, context_texts).
        """
        query_tokens = tokenize(query)

        scores: List[Tuple[float, str]] = []
        for i, doc_id in enumerate(self.doc_ids):
            bm25 = self._bm25_score(query_tokens, i)
            kw_boost = self._keyword_boost(query, doc_id)
            # Also check title match
            title_tokens = tokenize(self.documents[doc_id]["title"])
            title_overlap = len(set(query_tokens) & set(title_tokens)) * 2.0
            total_score = bm25 + kw_boost + title_overlap
            scores.append((total_score, doc_id))

        scores.sort(key=lambda x: x[0], reverse=True)

        # Out-of-context detection: if top score is very low, fallback to doc_06
        if scores[0][0] < 1.0:
            # Check if any keyword maps to a doc
            has_keyword_match = False
            query_lower = query.lower()
            for keyword, doc_ids in KEYWORD_INDEX.items():
                if keyword.lower() in query_lower:
                    has_keyword_match = True
                    break
            if not has_keyword_match:
                # Likely out-of-context question
                doc_06_idx = self.doc_ids.index("doc_06")
                contexts = [self.doc_texts[doc_06_idx]]
                return ["doc_06"], contexts

        top = scores[:top_k]
        retrieved_ids = [doc_id for _, doc_id in top]
        contexts = [
            f"[{self.doc_ids.index(doc_id)}] {self.documents[doc_id]['title']}: {self.documents[doc_id]['text']}"
            for doc_id in retrieved_ids
        ]
        return retrieved_ids, contexts


# ──────────────────────────────────────────────
# Answer Generator (extractive + smart)
# ──────────────────────────────────────────────

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "and", "but", "or", "nor",
    "not", "so", "very", "just", "than", "too", "also", "about", "up",
    "it", "its", "this", "that", "these", "those", "i", "me", "my", "we",
    "our", "you", "your", "he", "him", "his", "she", "her", "they", "them",
    "their", "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "only", "own", "same",
    # Vietnamese stop words
    "ne", "na", "gì", "nào", "ai", "bao", "lâu", "nhiều", "là", "của",
    "và", "hay", "hoặc", "được", "không", "có", "cho", "với", "từ",
    "trong", "trên", "dưới", "nếu", "thì", "đã", "đang", "sẽ", "phải",
    "cần", "nên", "khi", "bằng", "các", "một", "đến", "ra", "lại",
    "người", "dùng", "hỏi", "trả lời", "câu", "hỏi", "nói", "làm",
    "theo", "cũng", "như", "hay", "hoặc", "còn", "nữa", "thêm",
    "turn", "tôi", "bạn", "chúng", "họ",
}


class SmartGenerator:
    """Generate answers by extracting relevant sentences, with Vietnamese support."""

    def generate(self, question: str, contexts: List[str], retrieved_ids: List[str]) -> str:
        """
        Pick the sentence from contexts that best matches the question keywords.
        Special handling for out-of-context (doc_06).
        """
        # Special case: out-of-context
        if retrieved_ids == ["doc_06"]:
            return (
                "Không có đủ thông tin trong context để trả lời; "
                "cần yêu cầu tài liệu liên quan."
            )

        question_tokens = set(tokenize(question)) - STOP_WORDS
        keywords = {t for t in question_tokens if len(t) > 1}

        best_score = 0
        best_sentence = ""

        full_text = " ".join(contexts)
        # Split into sentences
        sentences = re.split(r"[.!?\n]+", full_text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 5:
                continue
            sentence_tokens = set(tokenize(sentence))
            # Count keyword overlap
            overlap = len(keywords & sentence_tokens)
            # Bonus for containing numbers (often factual answers)
            has_number = bool(re.search(r"\d+", sentence))
            score = overlap + (0.5 if has_number else 0)

            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_score == 0:
            # Try to find any relevant sentence from the context
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:
                    best_sentence = sentence
                    break

        if not best_sentence:
            return (
                "Không có đủ thông tin trong context để trả lời; "
                "cần yêu cầu tài liệu liên quan."
            )

        # Clean up: remove doc ID prefix if present
        best_sentence = re.sub(r"^\[\d+\]\s*[^:]+:\s*", "", best_sentence)
        return best_sentence.strip().rstrip(".") + "."


# ──────────────────────────────────────────────
# Main Agent
# ──────────────────────────────────────────────

class MainAgent:
    """
    RAG Agent với BM25 retrieval + keyword boosting + extractive generation.
    """

    def __init__(self):
        self.name = "SupportAgent-v3-BM25"
        self.retriever = BM25Retriever(DOCUMENTS)
        self.generator = SmartGenerator()

    async def query(self, question: str) -> Dict:
        """
        Pipeline RAG:
        1. Retrieval: BM25 + keyword boost tìm top-3 documents.
        2. Generation: Extractive sinh câu trả lời từ context.
        3. Trả về schema: answer, contexts, retrieved_ids, metadata.
        """
        await asyncio.sleep(0.02)

        # Step 1: Retrieval
        retrieved_ids, contexts = self.retriever.retrieve(question, top_k=3)

        # Step 2: Generation
        answer = self.generator.generate(question, contexts, retrieved_ids)

        # Step 3: Return structured response
        return {
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "bm25-extractive",
                "tokens_used": sum(len(tokenize(c)) for c in contexts),
                "retrieval_method": "bm25_keyword_boost",
            },
        }


# ──────────────────────────────────────────────
# Quick test
# ──────────────────────────────────────────────

if __name__ == "__main__":
    agent = MainAgent()

    async def test():
        questions = [
            "Link đặt lại mật khẩu hết hạn sau bao lâu?",
            "Điều kiện hoàn tiền của khách hàng thường là gì?",
            "Gói Pro bao gồm bao nhiêu tin nhắn mỗi tháng?",
            "Assistant có thể trả lời người dùng bằng tiếng Việt không?",
            "CEO của công ty sinh năm bao nhiêu?",
            "File PDF upload tối đa bao nhiêu MB?",
            "Trial accounts nên dùng retention 180 ngày hay 90 ngày?",
        ]
        for q in questions:
            resp = await agent.query(q)
            print(f"Q: {q}")
            print(f"IDs: {resp['retrieved_ids']}")
            print(f"A: {resp['answer'][:100]}")
            print()

    asyncio.run(test())
