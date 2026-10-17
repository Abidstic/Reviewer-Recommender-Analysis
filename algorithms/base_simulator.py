import abc
from datetime import datetime
from functools import cached_property
from typing import Dict, Optional, Iterable, List

from models import Manager, PullRequest
from utils import Cache
from utils.bots import is_bot


class BaseSimulator:
    _manager: Manager
    CACHE_VERSION = 'v3'

    def __init__(self, manager: Manager, from_cache=True, target_pr_numbers: Optional[Iterable[int]] = None):
        self._manager = manager
        self._from_cache = from_cache
        self._target_pr_numbers = set(target_pr_numbers) if target_pr_numbers is not None else None

    @cached_property
    def _target_prs(self) -> List[PullRequest]:
        """PRs to score, in chronological order. All of them, or just the targets."""
        prs = self._manager.pull_requests_list
        if self._target_pr_numbers is None:
            return prs
        return [pr for pr in prs if pr.number in self._target_pr_numbers]

    @staticmethod
    def parse_dt(date_str: Optional[str]) -> Optional[datetime]:
        if date_str is None:
            return None
        return datetime.fromisoformat(date_str.replace('Z', ''))

    @staticmethod
    def is_bot(username: Optional[str]) -> bool:
        return is_bot(username)

    def finalize_candidates(self, scores: Dict[str, float], pr: PullRequest) -> Dict[str, float]:
        """Shared output step for every algorithm:"""
        author = pr.developer_username
        cleaned = {
            user: score for user, score in scores.items()
            if user != author and not self.is_bot(user) and score > 0
        }
        return dict(
            sorted(cleaned.items(), key=lambda kv: (-kv[1], kv[0]))
        )

    @property
    def _cache_filename(self):
        return f'{self._manager.project}.{self.__class__.__name__}.{self.CACHE_VERSION}.simulation'

    @cached_property
    def cached_result(self):
        if self._from_cache and self._target_pr_numbers is None:
            result = Cache.load(self._cache_filename)
            if result:
                return result
        return None

    def _store_result(self, result):
        if self._target_pr_numbers is None:
            Cache.store(self._cache_filename, result, chunk=True)

    @abc.abstractmethod
    def simulate(self) -> Dict[int, Dict[str, float]]:
        pass
