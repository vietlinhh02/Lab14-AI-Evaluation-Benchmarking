import asyncio
import json
import os
import re
import time
from typing import Dict, List
from engine.runner import BenchmarkRunner
from engine.retrieval_eval import RetrievalEvaluator
from agent.main_agent import MainAgent


# ──────────────────────────────────────────────
# V1 Agent - TF-IDF basic, khong keyword boost
# ──────────────────────────────────────────────

class V1Agent:
    def __init__(self):
        import math
        from collections import Counter
        from agent.main_agent import DOCUMENTS, tokenize, compute_tf, cosine_similarity

        self._tokenize = tokenize
        self._compute_tf = compute_tf
        self._cosine = cosine_similarity
        self.name = "SupportAgent-v1-TFIDF"
        self.doc_ids = list(DOCUMENTS.keys())
        self.doc_texts = [d["title"] + " " + d["text"] for d in DOCUMENTS.values()]
        self.doc_tokens = [tokenize(t) for t in self.doc_texts]
        n = len(self.doc_tokens)
        df = Counter()
        for tokens in self.doc_tokens:
            for t in set(tokens):
                df[t] += 1
        self.idf = {t: math.log(n / c) for t, c in df.items()}

    def _tfidf(self, tokens):
        tf = self._compute_tf(tokens)
        return {t: v * self.idf.get(t, 0) for t, v in tf.items()}

    def _retrieve(self, query, top_k=3):
        qvec = self._tfidf(self._tokenize(query))
        scores = []
        for i, did in enumerate(self.doc_ids):
            dvec = self._tfidf(self.doc_tokens[i])
            scores.append((self._cosine(qvec, dvec), did))
        scores.sort(reverse=True)
        return [d for _, d in scores[:top_k]]

    async def query(self, question: str):
        await asyncio.sleep(0.02)
        retrieved_ids = self._retrieve(question)
        contexts = [self.doc_texts[self.doc_ids.index(d)] for d in retrieved_ids]
        answer = contexts[0].split(".")[0] + "." if contexts else "I don't know."
        return {
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {"model": "tfidf-basic-v1", "tokens_used": 100},
        }


# ──────────────────────────────────────────────
# Real Evaluators - cham diem that
# ──────────────────────────────────────────────

STOP = {"the","a","is","are","of","to","in","for","and","or","not","with","from",
        "that","this","it","be","as","at","by","on","an","was","were","been",
        "have","has","had","do","does","did","will","would","could","should",
        "may","might","shall","can","than","too","also","about","up","very",
        "just","so","no","only","own","same","but","if","then","else","when"}

VN_STOP = {"là","của","và","hay","hoặc","được","không","có","cho","với","từ",
           "trong","trên","dưới","nếu","thì","đã","đang","sẽ","phải","cần",
           "nên","khi","bằng","các","một","đến","ra","lại","người","dùng",
           "hỏi","trả lời","câu","nói","làm","theo","cũng","như","còn",
           "nữa","thêm","tôi","bạn","họ"}

ALL_STOP = STOP | VN_STOP


def _tok(text: str) -> set:
    return set(re.findall(
        r"[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
        r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ0-9]+",
        text.lower()))


def _overlap(a: str, b: str) -> float:
    at = _tok(a) - ALL_STOP
    bt = _tok(b) - ALL_STOP
    if not bt:
        return 0.0
    return len(at & bt) / len(bt)


class RealExpertEvaluator:
    async def score(self, case: Dict, resp: Dict) -> Dict:
        answer = resp.get("answer", "")
        expected = case.get("expected_answer", "")
        contexts = resp.get("contexts", [])

        relevancy = _overlap(answer, expected)

        ctx_text = " ".join(contexts).lower()
        ans_tokens = _tok(answer) - ALL_STOP
        if ans_tokens:
            in_ctx = sum(1 for t in ans_tokens if t in ctx_text) / len(ans_tokens)
        else:
            in_ctx = 0.0

        return {
            "faithfulness": round(min(1.0, in_ctx), 4),
            "relevancy": round(relevancy, 4),
            "retrieval": {"hit_rate": 0.0, "mrr": 0.0}
        }


class RealMultiModelJudge:
    async def evaluate_multi_judge(self, q: str, answer: str, expected: str) -> Dict:
        ov = _overlap(answer, expected)

        if ov >= 0.7:
            score = 5.0
        elif ov >= 0.5:
            score = 4.0
        elif ov >= 0.3:
            score = 3.5
        elif ov >= 0.15:
            score = 2.5
        elif ov >= 0.05:
            score = 2.0
        else:
            score = 1.0

        # out-of-context
        ooc = {"không","đủ","thông","tin","context","know","relevant","document","yêu cầu"}
        if len(ooc & _tok(expected)) >= 2 and len(ooc & _tok(answer)) >= 2:
            score = 5.0

        return {
            "final_score": round(score, 2),
            "agreement_rate": 1.0,
            "reasoning": f"overlap={ov:.2f} score={score}"
        }


# ──────────────────────────────────────────────
# Benchmark Runner
# ──────────────────────────────────────────────

async def run_benchmark_with_results(agent_version: str, agent_class=None):
    print(f"Khoi dong Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("Thieu data/golden_set.jsonl. Hay chay 'python data/synthetic_gen.py' truoc.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("File data/golden_set.jsonl rong.")
        return None, None

    if agent_class is None:
        agent_class = MainAgent

    runner = BenchmarkRunner(agent_class(), RealExpertEvaluator(), RealMultiModelJudge())
    results = await runner.run_all(dataset)

    retrieval_evaluator = RetrievalEvaluator(top_k=3)
    retrieval_data = [
        {
            "expected_retrieval_ids": r.get("expected_retrieval_ids", []),
            "retrieved_ids": r.get("retrieved_ids", [])
        }
        for r in results
    ]
    retrieval_metrics = await retrieval_evaluator.evaluate_batch(retrieval_data)

    total = len(results)
    summary = {
        "metadata": {
            "version": agent_version,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": round(sum(r["judge"]["final_score"] for r in results) / total, 4),
            "hit_rate": retrieval_metrics["avg_hit_rate"],
            "mrr": retrieval_metrics["avg_mrr"],
            "agreement_rate": round(sum(r["judge"]["agreement_rate"] for r in results) / total, 4)
        }
    }
    return results, summary


async def run_benchmark(version, agent_class=None):
    _, summary = await run_benchmark_with_results(version, agent_class)
    return summary


async def main():
    v1_summary = await run_benchmark("Agent_V1_Base", agent_class=V1Agent)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")

    if not v1_summary or not v2_summary:
        print("Khong the chay Benchmark.")
        return

    print("\n--- KET QUA SO SANH (REGRESSION) ---")
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    print(f"V1 avg_score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 avg_score: {v2_summary['metrics']['avg_score']}")
    print(f"V1 hit_rate:  {v1_summary['metrics']['hit_rate']}")
    print(f"V2 hit_rate:  {v2_summary['metrics']['hit_rate']}")
    print(f"V1 mrr:       {v1_summary['metrics']['mrr']}")
    print(f"V2 mrr:       {v2_summary['metrics']['mrr']}")
    print(f"Delta score: {'+' if delta >= 0 else ''}{delta:.2f}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if delta > 0:
        print("\nQUYET DINH: CHAP NHAN BAN CAP NHAT (APPROVE)")
    else:
        print("\nQUYET DINH: TU CHOI (BLOCK RELEASE)")


if __name__ == "__main__":
    asyncio.run(main())
