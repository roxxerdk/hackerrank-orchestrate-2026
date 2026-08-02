from typing import Dict, Any, List

class MetricsTracker:
    """
    Incremental metrics tracker holding run configurations and routing analytics.
    Avoids expensive file lookups or re-aggregations per request.
    """
    def __init__(self):
        self.messages_processed: int = 0
        self.notify_count: int = 0
        self.digest_count: int = 0
        self.mute_count: int = 0
        
        self.total_latency_ms: float = 0.0
        self.total_feature_latency_ms: float = 0.0
        self.total_decision_latency_ms: float = 0.0
        
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        
        self.rule_fire_counts: Dict[str, int] = {}

    def record_route(
        self,
        action: str,
        latency_ms: float,
        feature_latency_ms: float,
        decision_latency_ms: float,
        rules: List[str],
        media_hit: bool = False
    ) -> None:
        self.messages_processed += 1
        
        if action == "notify":
            self.notify_count += 1
        elif action == "digest":
            self.digest_count += 1
        elif action == "mute":
            self.mute_count += 1
            
        self.total_latency_ms += latency_ms
        self.total_feature_latency_ms += feature_latency_ms
        self.total_decision_latency_ms += decision_latency_ms
        
        if media_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            
        for rule_id in rules:
            self.rule_fire_counts[rule_id] = self.rule_fire_counts.get(rule_id, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        avg_latency = self.total_latency_ms / self.messages_processed if self.messages_processed > 0 else 0.0
        avg_feat = self.total_feature_latency_ms / self.messages_processed if self.messages_processed > 0 else 0.0
        avg_dec = self.total_decision_latency_ms / self.messages_processed if self.messages_processed > 0 else 0.0
        
        return {
            "messages_processed": self.messages_processed,
            "notify_count": self.notify_count,
            "digest_count": self.digest_count,
            "mute_count": self.mute_count,
            "average_latency_ms": avg_latency,
            "average_feature_latency_ms": avg_feat,
            "average_decision_latency_ms": avg_dec,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "rule_fire_counts": self.rule_fire_counts
        }
