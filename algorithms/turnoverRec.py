import bisect
from collections import defaultdict
from datetime import timedelta
from functools import cached_property
from typing import Dict, List, Tuple

from models import PullRequest
from utils.logger import info_logger
from .base_simulator import BaseSimulator
from .utils.knowledge import KnowledgeIndex


class TurnoverRec(BaseSimulator):
    WINDOW_DAYS = 365

    @cached_property
    def knowledge(self) -> KnowledgeIndex:
        return KnowledgeIndex(self._manager)

    @cached_property
    def _events(self) -> Tuple[List[object], List[str]]:
        """Project activity as (timestamp, developer), sorted by time.

        One event per commit, plus one event per (reviewer, PR) at that
        reviewer's first review on the PR (the PR author's own reviews excluded).
        Bot activity is excluded (paper Sec. 3.1).
        Returns parallel (timestamps, developers) lists for bisect slicing.
        """
        events: List[Tuple[object, str]] = []

        for commit in self._manager.commits_list:
            ts = self.parse_dt(commit.date)
            if ts is not None and not self.is_bot(commit.username):
                events.append((ts, commit.username))

        first_review: Dict[Tuple[str, int], object] = {}
        for review in self._manager.reviews_list:
            ts = self.parse_dt(review.date)
            if ts is None or self.is_bot(review.reviewer_username):
                continue
            pr = self._manager.pull_requests.get(review.pull_number)
            if pr is None or review.reviewer_username == pr.developer_username:
                continue
            key = (review.reviewer_username, review.pull_number)
            if key not in first_review or ts < first_review[key]:
                first_review[key] = ts
        for (reviewer, _pn), ts in first_review.items():
            events.append((ts, reviewer))

        events.sort(key=lambda e: e[0])
        timestamps = [e[0] for e in events]
        developers = [e[1] for e in events]
        return timestamps, developers

    def _retention_inputs(self, pr_dt):
        """Per-developer (event count, distinct (year,month) set) in the window."""
        timestamps, developers = self._events
        window_start = pr_dt - timedelta(days=self.WINDOW_DAYS)
        lo = bisect.bisect_left(timestamps, window_start)
        hi = bisect.bisect_left(timestamps, pr_dt)

        counts: Dict[str, int] = defaultdict(int)
        months: Dict[str, set] = defaultdict(set)
        for i in range(lo, hi):
            dev = developers[i]
            ts = timestamps[i]
            counts[dev] += 1
            months[dev].add((ts.year, ts.month))
        total = hi - lo
        return counts, months, total

    def _calc_scores(self, pr: PullRequest) -> Dict[str, float]:
        pr_dt = self.parse_dt(pr.date)
        scores: Dict[str, float] = {}
        if pr_dt is None or not pr.file_paths:
            return scores

        candidates = set()
        for path in pr.file_paths:
            candidates |= self.knowledge.knowledgeable(path, pr_dt)
        if not candidates:
            return scores

        counts, months, total = self._retention_inputs(pr_dt)
        n_files = len(pr.file_paths)

        for dev in candidates:
            known = self.knowledge.files_known_by(dev, pr.file_paths, pr_dt)
            if not known:
                continue
            learn = 1 - (len(known) / n_files)
            contribution = (counts[dev] / total) if total else 0.0
            consistency = min(len(months[dev]), 12) / 12
            scores[dev] = learn * consistency * contribution

        return scores

    def simulate(self):
        info_logger.info("Simulating TurnoverRec...")
        if self.cached_result:
            info_logger.info("TurnoverRec simulation loaded from cache")
            return self.cached_result

        result: Dict[int, Dict[str, float]] = {}
        pr_len = len(self._target_prs)
        for index, pr in enumerate(self._target_prs):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            scores = self._calc_scores(pr)
            result[pr.number] = self.finalize_candidates(scores, pr)

        self._store_result(result)
        info_logger.info("TurnoverRec simulation finished")
        return result
