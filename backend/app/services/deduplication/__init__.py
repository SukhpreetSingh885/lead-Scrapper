from app.services.deduplication.normalizer import DataNormalizer
from app.services.deduplication.matcher import BranchDeduplicationMatcher, MatchResult
from app.services.deduplication.resolver import DeduplicationResolver

__all__ = [
    "DataNormalizer",
    "BranchDeduplicationMatcher",
    "MatchResult",
    "DeduplicationResolver",
]

