import bisect
import posixpath
from collections import defaultdict
from functools import cached_property
from typing import Dict, List, Tuple

from utils.logger import info_logger
from .base_simulator import BaseSimulator
from models import PullRequest


class ChRev(BaseSimulator):
    CACHE_VERSION = 'v3'

    # one log entry = (timestamp, calendar_date, reviewer)
    Entry = Tuple[object, object, str]

    def _is_own_pr_reply(self, comment) -> bool:
        """True when the comment was written by the author of the PR it belongs to.

        The PR is resolved through the comment's review; comments with no known
        review cannot be resolved and are kept.
        """
        review = self._manager.reviews.get(comment.review_id)
        if review is None:
            return False
        pr = self._manager.pull_requests.get(review.pull_number)
        return pr is not None and comment.reviewer_username == pr.developer_username

    @cached_property
    def _indexes(self):
        by_file: Dict[str, List['ChRev.Entry']] = defaultdict(list)
        by_package: Dict[str, List['ChRev.Entry']] = defaultdict(list)
        by_system: Dict[str, List['ChRev.Entry']] = defaultdict(list)

        for comment in self._manager.comments_list:
            ts = self.parse_dt(comment.date)
            if ts is None:
                continue
            if self.is_bot(comment.reviewer_username) or self._is_own_pr_reply(comment):
                continue
            path = comment.filename
            entry = (ts, ts.date(), comment.reviewer_username)
            by_file[path].append(entry)
            by_package[posixpath.dirname(path)].append(entry)
            by_system[path.split('/')[0] if '/' in path else ''].append(entry)

        for index in (by_file, by_package, by_system):
            for entries in index.values():
                entries.sort(key=lambda e: e[0])

        return by_file, by_package, by_system

    @staticmethod
    def _entries_before(entries: List['ChRev.Entry'], pr_dt) -> List['ChRev.Entry']:
        keys = [e[0] for e in entries]
        cut = bisect.bisect_left(keys, pr_dt)
        return entries[:cut]

    @staticmethod
    def _xfactors(entries: List['ChRev.Entry']) -> Dict[str, float]:
        """xFactor (Eq. 2) for every reviewer appearing in ``entries``."""
        c_total = len(entries)
        all_dates = {e[1] for e in entries}
        w_total = len(all_dates)
        t_total = max(all_dates)

        per_reviewer_count: Dict[str, int] = defaultdict(int)
        per_reviewer_dates: Dict[str, set] = defaultdict(set)
        for _ts, cal_date, reviewer in entries:
            per_reviewer_count[reviewer] += 1
            per_reviewer_dates[reviewer].add(cal_date)

        scores = {}
        for reviewer, count in per_reviewer_count.items():
            dates = per_reviewer_dates[reviewer]
            c = count / c_total
            w = len(dates) / w_total
            gap = abs((t_total - max(dates)).days)
            recency = (1.0 / gap) if gap != 0 else 1.0
            scores[reviewer] = c + w + recency
        return scores

    def _calc_pr_scores(self, pr: PullRequest) -> Dict[str, float]:
        pr_dt = self.parse_dt(pr.date)
        by_file, by_package, by_system = self._indexes
        author = pr.developer_username
        scores: Dict[str, float] = defaultdict(float)

        if pr_dt is None:
            return scores

        for path in pr.file_paths:
            levels = (
                by_file.get(path, []),
                by_package.get(posixpath.dirname(path), []),
                by_system.get(path.split('/')[0] if '/' in path else '', []),
            )
            for level_entries in levels:
                entries = self._entries_before(level_entries, pr_dt)
                if not entries:
                    continue
                reviewers = {e[2] for e in entries}
                if not any(r != author for r in reviewers):
                    continue
                for reviewer, xfactor in self._xfactors(entries).items():
                    scores[reviewer] += xfactor
                break

        return scores

    def simulate(self):
        info_logger.info("Simulating ChRev...")
        if self.cached_result:
            info_logger.info("ChRev simulation loaded from cache")
            return self.cached_result

        result: Dict[int, Dict[str, float]] = {}
        pr_len = len(self._target_prs)
        for index, pr in enumerate(self._target_prs):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            scores = self._calc_pr_scores(pr)
            result[pr.number] = self.finalize_candidates(scores, pr)

        self._store_result(result)
        info_logger.info("ChRev simulation finished")
        return result
