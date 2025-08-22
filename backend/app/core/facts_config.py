"""
Configuration for Phase 2.3 Facts Computation
"""
import os


class FactsConfig:
    """Configuration for facts computation phase"""
    
    def __init__(self):
        # Maximum tuple estimate before marking as capped
        self.MAX_TUPLE_ESTIMATE_CAP = int(os.getenv("FACTS_MAX_TUPLE_ESTIMATE_CAP", "1000000000"))
        
        # Batch size for processing rules to avoid memory spikes
        self.FACTS_BATCH_SIZE = int(os.getenv("FACTS_BATCH_SIZE", "1000"))


# Global instance
facts_config = FactsConfig()
