from typing import Dict

from utils import Cache
from utils.logger import info_logger
from .base_simulator import BaseSimulator
from models import Developer, PullRequest


class ChRev(BaseSimulator):

    @classmethod
    def _day(cls, date_str):
        return cls._parse_date_string(date_str).date()

    def _calc_xFactor(self, developer: Developer, pr: PullRequest) -> float:
        total = 0.0
        for filepath in pr.file_paths:
            file_comments = [
                c for c in self._manager.comments.get(filepath, [])
                if c.date < pr.date
            ]
            if not file_comments:
                continue
            dev_comments = [
                c for c in file_comments
                if c.reviewer_username == developer.username
            ]
            if not dev_comments:
                continue

            term1 = len(dev_comments) / len(file_comments)

            dev_days = {self._day(c.date) for c in dev_comments}
            file_days = {self._day(c.date) for c in file_comments}
            term2 = len(dev_days) / len(file_days)

            dev_last = max(c.date for c in dev_comments)
            file_last = max(c.date for c in file_comments)
            # PAPER Eq. 3 (Zanjani, Kagdi & Bird, TSE 2016): recency term
            # 1 / (|Tf - Tf'| + 1), in days. Equals 1.0 when the developer
            # made the most recent comment on the file.
            gap = self.calc_diff_date(dev_last, file_last)
            term3 = 1.0 / (gap + 1)

            total += term1 + term2 + term3
        return total

    def simulate(self):
        info_logger.info("Simulating ChRev...")
        if self.cached_result:
            info_logger.info("ChRev simulation loaded from cache")
            return self.cached_result

        # {[pr_number]: { [dev_username]: score }}
        result: Dict[int, Dict[str, float]] = {}

        pr_len = len(self._manager.pull_requests_list)
        for index, pr in enumerate(self._manager.pull_requests_list):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            result[pr.number] = {}
            for developer in self._manager.developers_list:
                score = self._calc_xFactor(developer=developer, pr=pr)
                if score > 0:
                    result[pr.number][developer.username] = score

        Cache.store(self._cache_filename, result, chunk=True)
        info_logger.info("ChRev simulation stored in cache")
        return result
