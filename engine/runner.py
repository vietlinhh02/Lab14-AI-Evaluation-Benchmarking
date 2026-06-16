import asyncio
import time
from typing import List, Dict
# Import other components...

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict) -> Dict:
        start_time = time.perf_counter()
        
        # 1. Gọi Agent
        response = await self.agent.query(test_case["question"])
        latency = time.perf_counter() - start_time
        
        # 2. Chạy RAGAS metrics
        ragas_scores = await self.evaluator.score(test_case, response)
        
        # 3. Chạy Multi-Judge
        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"], 
            response["answer"], 
            test_case["expected_answer"]
        )
        
        return {
            "test_case": test_case["question"],
            "agent_response": response["answer"],
            "latency": latency,
            "ragas": ragas_scores,
            "judge": judge_result,
            "status": "fail" if judge_result["final_score"] < 3 else "pass"
        }

    async def run_all(self, dataset: List[Dict], max_concurrent: int = 10) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather kết hợp với Semaphore để tối ưu Rate Limit thay vì chunking tĩnh.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def sem_task(case):
            async with semaphore:
                return await self.run_single_test(case)
                
        tasks = [sem_task(case) for case in dataset]
        results = await asyncio.gather(*tasks)
        return results
