from typing import Dict

from models import Developer, PullRequest
from utils import Cache
from utils.logger import info_logger
from .base_simulator import BaseSimulator


class TurnoverRec(BaseSimulator):
    def _calc_ReviewerKnows(self, developer: Developer, pr: PullRequest):
        if not pr.file_paths:
            return 0

        known_files = set()

        for filepath in pr.file_paths:
            reviewed = any(
                rf.filepath == filepath
                and rf.reviewer_username == developer.username
                and rf.date < pr.date
                for rf in self._manager.review_files_list
            )
            if reviewed:
                known_files.add(filepath)
                continue

            contributed = any(
                c.username == developer.username and c.date < pr.date
                for c in self._manager.contributions.get(filepath, [])
            )
            if contributed:
                known_files.add(filepath)

        return len(known_files) / len(pr.file_paths)

    def _calc_learnRec(self, developer: Developer, pr: PullRequest):
        # PAPER Eq. 5 (Mirsaeedi & Rigby 2020): LearnRec = 1 - ReviewerKnows,
        # restricted to candidates that know at least one file under review.
        # A developer who knows no file is not a candidate (score 0).
        knows = self._calc_ReviewerKnows(developer=developer, pr=pr)
        if knows == 0:
            return 0.0
        return 1 - knows

    def _is_in_past_year(self, pr_date, record_date):
        # One-year retention window ending at the PR date. Backward-looking
        # only: records dated after the PR are future data and excluded.
        delta = (
            self._parse_date_string(pr_date) - self._parse_date_string(record_date)
        ).days
        return 0 <= delta <= 365

    def _calc_totalCommitReview(self, pr: PullRequest):
        return len([
            _ for _ in self._manager.reviews_list if self._is_in_past_year(pr.date, _.date)
        ]) + len([
            _ for _ in self._manager.commits_list if self._is_in_past_year(pr.date, _.date)
        ])

    def _calc_RetentionRec(self, pr: PullRequest):
        # {[dev_username]: float}
        retention: Dict[str, float] = {}
        totalCommitReviews = self._calc_totalCommitReview(pr=pr)

        for developer in self._manager.developers_list:
            past_year_reviews = [
                _ for _ in self._manager.reviews_list
                if self._is_in_past_year(pr.date, _.date) and _.reviewer_username == developer.username
            ]
            past_year_commits = [
                _ for _ in self._manager.commits_list
                if self._is_in_past_year(pr.date, _.date) and _.username == developer.username
            ]
            # PAPER Eq. 6: ContributionRatio = (dev reviews + commits in last
            # year) / (all reviews + commits in last year, project-wide).
            contribution = (
                (len(past_year_reviews) + len(past_year_commits)) / totalCommitReviews
                if totalCommitReviews else 0.0
            )
            past_year_active_months = {
                *[self.get_date_month(_.date) for _ in past_year_reviews],
                *[self.get_date_month(_.date) for _ in past_year_commits],
            }
            # PAPER Eq. (ConsistencyRatio): active months in last year / 12.
            consistency = len(past_year_active_months) / 12
            # PAPER Eq. 8: RetentionRec = ConsistencyRatio * ContributionRatio.
            retention[developer.username] = contribution * consistency

        return retention

    def simulate(self):
        info_logger.info("Simulating TurnoverRec...")
        if self.cached_result:
            info_logger.info("TurnoverRec simulation loaded from cache")
            return self.cached_result

        # {[pr_number]: { [dev_username]: score }}
        result: Dict[int, Dict[str, float]] = {}

        pr_len = len(self._manager.pull_requests_list)
        for index, pr in enumerate(self._manager.pull_requests_list):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            result[pr.number] = {}
            retentionRec = self._calc_RetentionRec(pr=pr)
            for developer in self._manager.developers_list:
                # PAPER Eq. 9: TurnoverRec(D,R) = LearnRec(D,R) * RetentionRec(D)
                # with coefficients C1 = C2 = 1.
                result[pr.number][developer.username] = self._calc_learnRec(
                    developer=developer,
                    pr=pr
                ) * retentionRec[developer.username]

        Cache.store(self._cache_filename, result, chunk=True)
        info_logger.info("TurnoverRec simulation finished")
        return result
