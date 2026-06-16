from typing import List, Dict

class RetrievalEvaluator:
    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = None) -> float:
        """
        Tính Hit Rate: ít nhất 1 expected_id nằm trong top_k retrieved_ids.
        Trả về 1.0 nếu hit, 0.0 nếu miss.
        """
        k = top_k if top_k is not None else self.top_k
        top_retrieved = retrieved_ids[:k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Tính Mean Reciprocal Rank cho 1 query.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        """
        Chạy retrieval eval cho toàn bộ dataset.
        Mỗi item trong dataset cần có:
          - 'expected_retrieval_ids': List[str] - ID ground truth
          - 'retrieved_ids': List[str] - ID do agent retrieval trả về
        """
        if not dataset:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0, "total_cases": 0}

        hit_rates: List[float] = []
        mrrs: List[float] = []

        for case in dataset:
            expected_ids = case.get("expected_retrieval_ids", [])
            retrieved_ids = case.get("retrieved_ids", [])

            hit_rates.append(self.calculate_hit_rate(expected_ids, retrieved_ids))
            mrrs.append(self.calculate_mrr(expected_ids, retrieved_ids))

        total = len(hit_rates)
        avg_hit_rate = sum(hit_rates) / total
        avg_mrr = sum(mrrs) / total

        return {
            "avg_hit_rate": round(avg_hit_rate, 4),
            "avg_mrr": round(avg_mrr, 4),
            "total_cases": total
        }
