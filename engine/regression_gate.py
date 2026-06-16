import json
from typing import Dict, Any, Tuple

class RegressionGate:
    def __init__(
        self,
        min_score_delta: float = 0.0,          # V2 score - V1 score must be >= this (e.g., 0.0 = no quality regression)
        min_hit_rate: float = 0.80,            # Retrieval hit rate must be >= this
        max_avg_latency: float = 2.0,          # Average latency per test case must be <= this
        max_cost_increase_pct: float = 20.0    # Cost increase of V2 compared to V1 must be <= this %
    ):
        self.min_score_delta = min_score_delta
        self.min_hit_rate = min_hit_rate
        self.max_avg_latency = max_avg_latency
        self.max_cost_increase_pct = max_cost_increase_pct

    def evaluate(self, v1_summary: Dict[str, Any], v2_summary: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Evaluate regression between V1 and V2 summaries.
        Returns:
            pass_gate (bool): True if V2 meets all gate criteria, False otherwise.
            report (dict): Structured breakdown of all checks.
            console_msg (str): Beautiful string representation of the gate results.
        """
        v1_metrics = v1_summary["metrics"]
        v2_metrics = v2_summary["metrics"]
        total_cases = v2_summary["metadata"]["total"]

        # 1. Quality Check (Average Score)
        v1_score = v1_metrics["avg_score"]
        v2_score = v2_metrics["avg_score"]
        score_delta = v2_score - v1_score
        score_ok = score_delta >= self.min_score_delta

        # 2. Retrieval Check (Hit Rate)
        v2_hit_rate = v2_metrics.get("hit_rate", 0.0)
        hit_rate_ok = v2_hit_rate >= self.min_hit_rate

        # 3. Performance Check (Average Latency)
        # Latency in metrics is total_latency, so calculate average latency
        v1_avg_latency = v1_metrics["total_latency"] / v1_summary["metadata"]["total"]
        v2_avg_latency = v2_metrics["total_latency"] / total_cases
        latency_delta_pct = ((v2_avg_latency - v1_avg_latency) / v1_avg_latency) * 100 if v1_avg_latency > 0 else 0.0
        latency_ok = v2_avg_latency <= self.max_avg_latency

        # 4. Cost Check (Average Cost)
        v1_avg_cost = v1_metrics.get("total_estimated_cost", 0.0) / v1_summary["metadata"]["total"]
        v2_avg_cost = v2_metrics.get("total_estimated_cost", 0.0) / total_cases
        cost_delta_pct = ((v2_avg_cost - v1_avg_cost) / v1_avg_cost) * 100 if v1_avg_cost > 0 else 0.0
        cost_ok = True
        if v1_avg_cost > 0:
            cost_ok = cost_delta_pct <= self.max_cost_increase_pct

        # Overall decision
        pass_gate = score_ok and hit_rate_ok and latency_ok and cost_ok

        # Build detailed report
        report = {
            "decision": "APPROVE" if pass_gate else "ROLLBACK",
            "checks": {
                "quality_avg_score": {
                    "v1": v1_score,
                    "v2": v2_score,
                    "delta": score_delta,
                    "target": f">= {self.min_score_delta}",
                    "passed": bool(score_ok)
                },
                "retrieval_hit_rate": {
                    "v1": v1_metrics.get("hit_rate", 0.0),
                    "v2": v2_hit_rate,
                    "delta": v2_hit_rate - v1_metrics.get("hit_rate", 0.0),
                    "target": f">= {self.min_hit_rate}",
                    "passed": bool(hit_rate_ok)
                },
                "performance_avg_latency": {
                    "v1": v1_avg_latency,
                    "v2": v2_avg_latency,
                    "delta_pct": latency_delta_pct,
                    "target": f"<= {self.max_avg_latency}s",
                    "passed": bool(latency_ok)
                },
                "cost_avg_cost": {
                    "v1": v1_avg_cost,
                    "v2": v2_avg_cost,
                    "delta_pct": cost_delta_pct,
                    "target": f"<= +{self.max_cost_increase_pct}%",
                    "passed": bool(cost_ok)
                }
            }
        }

        # Format console dashboard
        msg = []
        msg.append("┌──────────────────────────────────────────────────────────────────────────────┐")
        msg.append("│                         🤖 REGRESSION RELEASE GATE 🤖                        │")
        msg.append("├──────────────────────────────┬──────────┬──────────┬───────────┬─────────────┤")
        msg.append("│ Metric                       │ V1 Base  │ V2 Opt   │ Delta     │ Status      │")
        msg.append("├──────────────────────────────┼──────────┼──────────┼───────────┼─────────────┤")
        
        status_score = "✅ PASS" if score_ok else "❌ FAIL"
        msg.append(f"│ Avg Score (1-5)              │ {v1_score:8.2f} │ {v2_score:8.2f} │ {score_delta:+8.2f}  │ {status_score:11} │")
        
        status_hit = "✅ PASS" if hit_rate_ok else "❌ FAIL"
        msg.append(f"│ Retrieval Hit Rate           │ {v1_metrics.get('hit_rate', 0.0):8.2%} │ {v2_hit_rate:8.2%} │ {v2_hit_rate - v1_metrics.get('hit_rate', 0.0):+8.2%}  │ {status_hit:11} │")
        
        status_latency = "✅ PASS" if latency_ok else "❌ FAIL"
        msg.append(f"│ Avg Latency (seconds)        │ {v1_avg_latency:8.3f} │ {v2_avg_latency:8.3f} │ {latency_delta_pct:+7.1f}%  │ {status_latency:11} │")
        
        status_cost = "✅ PASS" if cost_ok else "❌ FAIL"
        msg.append(f"│ Avg Cost (USD)               │ ${v1_avg_cost:7.5f} │ ${v2_avg_cost:7.5f} │ {cost_delta_pct:+7.1f}%  │ {status_cost:11} │")
        
        msg.append("├──────────────────────────────┴──────────┴──────────┴───────────┴─────────────┤")
        
        decision_str = "🚀 APPROVED FOR RELEASE 🚀" if pass_gate else "🛑 BLOCKED - ROLLBACK REQUIRED 🛑"
        color_padding = 24 if pass_gate else 20
        msg.append(f"│ DECISION: {decision_str:^{76 - color_padding}} │")
        msg.append("└──────────────────────────────────────────────────────────────────────────────┘")
        
        return pass_gate, report, "\n".join(msg)
