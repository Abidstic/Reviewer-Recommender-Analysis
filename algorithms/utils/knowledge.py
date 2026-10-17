from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional, Set

from models import Manager
from utils.bots import is_bot


class KnowledgeIndex:
    MEGA_FILES = 100

    def __init__(self, manager: Manager):
        self._manager = manager
        self.first_known: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self._build()

    @staticmethod
    def _parse(date_str: Optional[str]) -> Optional[datetime]:
        if date_str is None:
            return None
        return datetime.fromisoformat(date_str.replace('Z', ''))

    def _learn(self, path: str, dev: str, ts: Optional[datetime]):
        # Paper Sec. 3.1: changes made by bots are excluded, so bots know nothing.
        if ts is None or is_bot(dev):
            return
        current = self.first_known[path].get(dev)
        if current is None or ts < current:
            self.first_known[path][dev] = ts

    def _build(self):
        # Modified: one row per (commit, file); skip mega commits.
        files_per_commit: Dict[str, int] = defaultdict(int)
        for contribs in self._manager.contributions.values():
            for contribution in contribs:
                files_per_commit[contribution.commit_id] += 1

        for path, contribs in self._manager.contributions.items():
            for contribution in contribs:
                if files_per_commit[contribution.commit_id] >= self.MEGA_FILES:
                    continue
                self._learn(path, contribution.username, self._parse(contribution.date))

        pull_requests = self._manager.pull_requests
        for review in self._manager.reviews_list:
            ts = self._parse(review.date)
            if ts is None:
                continue
            pr = pull_requests.get(review.pull_number)
            if pr is None:
                continue
            if review.reviewer_username == pr.developer_username:
                continue
            if len(pr.file_paths) >= self.MEGA_FILES:
                continue
            for path in pr.file_paths:
                self._learn(path, review.reviewer_username, ts)

    def knowledgeable(self, path: str, before_ts: datetime) -> Set[str]:
        return {
            dev for dev, ts in self.first_known.get(path, {}).items()
            if ts < before_ts
        }

    def files_known_by(self, dev: str, paths, before_ts: datetime) -> Set[str]:
        known = set()
        for path in paths:
            ts = self.first_known.get(path, {}).get(dev)
            if ts is not None and ts < before_ts:
                known.add(path)
        return known
