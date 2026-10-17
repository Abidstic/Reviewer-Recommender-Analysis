from collections import defaultdict
from functools import cached_property
from typing import Dict, List, Tuple

from models import PullRequest
from utils.logger import info_logger
from .base_simulator import BaseSimulator
from .utils.rev_finder import ProjectFilesSimilarity, METHODOLOGIES


class RevFinder(BaseSimulator):

    CACHE_VERSION = 'v4'

    def __init__(self, manager, from_cache=True, target_pr_numbers=None):
        super().__init__(manager, from_cache, target_pr_numbers)
        self.file_similarity = ProjectFilesSimilarity(self._manager, from_cache=self._from_cache)

    @cached_property
    def _past_reviews(self) -> List[Tuple[PullRequest, 'object', List[Tuple['object', str]]]]:
       
        reviews_by_pr: Dict[int, List[Tuple[object, str]]] = defaultdict(list)
        for review in self._manager.reviews_list:
            ts = self.parse_dt(review.date)
            if ts is None:
                continue
            pr = self._manager.pull_requests.get(review.pull_number)
            if pr is None:
                continue
            if review.reviewer_username == pr.developer_username or self.is_bot(review.reviewer_username):
                continue
            reviews_by_pr[review.pull_number].append((ts, review.reviewer_username))

        result = []
        for pr_number, rev_list in reviews_by_pr.items():
            pr = self._manager.pull_requests[pr_number]
            if not pr.file_paths:
                continue
            created = self.parse_dt(pr.date)
            if created is None:
                continue
            rev_list.sort(key=lambda x: x[0])
            result.append((pr, created, rev_list))

        result.sort(key=lambda x: x[1])
        return result

    def _candidates_per_technique(self, pr: PullRequest) -> Dict[str, Dict[str, float]]:
        target_dt = self.parse_dt(pr.date)
        new_files = pr.file_paths
        candidates = {m.__name__: defaultdict(float) for m in METHODOLOGIES}

        if not new_files or target_dt is None:
            return candidates

        for past_pr, created, rev_list in self._past_reviews:
            if created >= target_dt or past_pr.number == pr.number:
                continue
            reviewers = {who for ts, who in rev_list if ts < target_dt}
            if not reviewers:
                continue

            past_files = past_pr.file_paths
            denom = len(new_files) * len(past_files)
            for methodology in METHODOLOGIES:
                total = 0.0
                for fn in new_files:
                    for fp in past_files:
                        total += self.file_similarity.get_file_similarity(fn, fp, methodology)
                score = total / denom
                if score > 0:
                    bucket = candidates[methodology.__name__]
                    for reviewer in reviewers:
                        bucket[reviewer] += score

        return candidates

    def _borda(self, candidates_per_technique: Dict[str, Dict[str, float]], pr: PullRequest) -> Dict[str, float]:
        """Borda count over the four technique lists (paper Section IV-D).

        M is the number of non-zero candidates in a list. Points follow the
        paper's text ("the first rank gets M"), i.e. M - rank + 1; Eq. 2 as
        printed (M - rank) would give the last candidate 0 points. Tied scores
        share the average of the ranks they span, so equal candidates earn
        equal points regardless of username.
        """
        points: Dict[str, float] = defaultdict(float)
        author = pr.developer_username
        for bucket in candidates_per_technique.values():
            ranked = sorted(
                ((user, round(score, 9)) for user, score in bucket.items()
                 if user != author and score > 0),
                key=lambda kv: -kv[1],
            )
            m = len(ranked)
            start = 0
            while start < m:
                end = start
                while end + 1 < m and ranked[end + 1][1] == ranked[start][1]:
                    end += 1
                # Positions start..end hold 1-based ranks start+1 .. end+1.
                avg_rank = (start + end) / 2 + 1
                for user, _score in ranked[start:end + 1]:
                    points[user] += m - avg_rank + 1
                start = end + 1
        return points

    def simulate(self):
        info_logger.info("Simulating RevFinder...")
        if self.cached_result:
            info_logger.info("RevFinder simulation loaded from cache")
            return self.cached_result

        result: Dict[int, Dict[str, float]] = {}
        pr_len = len(self._target_prs)
        for index, pr in enumerate(self._target_prs):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            per_technique = self._candidates_per_technique(pr)
            points = self._borda(per_technique, pr)
            result[pr.number] = self.finalize_candidates(points, pr)

        self._store_result(result)
        info_logger.info("RevFinder simulation finished")
        return result
