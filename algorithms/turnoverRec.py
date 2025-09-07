from typing import Dict

from models import Developer, PullRequest
from utils import Cache
from utils.logger import info_logger
from .base_simulator import BaseSimulator


class TurnoverRec(BaseSimulator):
    def _calc_ReviewerKnows(self, developer: Developer, pr: PullRequest):
        files_paths = [
            _.filepath for _ in self._manager.review_files_list if
            _.filepath in pr.file_paths and _.reviewer_username == developer.username and pr.date > _.date
        ]

        if len(files_paths) == 0:
            return 0

        for filepath in pr.file_paths:
            if filepath not in self._manager.contributions.keys():
                continue

            all_file_contributions = self._manager.contributions[filepath]
            if len([
                _ for _ in all_file_contributions if
                _.username == developer.username and pr.date > _.date and _.filename == filepath
                # last condition is trivial
            ]) > 0:
                files_paths.append(filepath)

        return len(set(files_paths)) / len(pr.file_paths)

    def _calc_learnRec(self, developer: Developer, pr: PullRequest):
        # todo: check with article
        return 1 - self._calc_ReviewerKnows(developer=developer, pr=pr)

    def _is_diff_under_year(self, f_date, e_date):
        return self.calc_diff_date(f_date, e_date) <= 365

    def _calc_totalCommitReview(self, pr: PullRequest):
        return len([
            _ for _ in self._manager.reviews_list if self._is_diff_under_year(pr.date, _.date)
        ]) + len([
            _ for _ in self._manager.commits_list if self._is_diff_under_year(pr.date, _.date)
        ])

    def _calc_RetentionRec(self, pr: PullRequest):
        # {[dev_username]: float}
        retention: Dict[str, float] = {}
        totalCommitReviews = self._calc_totalCommitReview(pr=pr)

        for developer in self._manager.developers_list:
            past_year_reviews = [
                _ for _ in self._manager.reviews_list
                if self._is_diff_under_year(pr.date, _.date) and _.reviewer_username == developer.username
            ]
            past_year_commits = [
                _ for _ in self._manager.commits_list
                if self._is_diff_under_year(pr.date, _.date) and _.username == developer.username
            ]
            contribution = len(past_year_reviews) + len(past_year_commits) / totalCommitReviews
            past_year_active_months = {
                *[self.get_date_month(_.date) for _ in past_year_reviews],
                *[self.get_date_month(_.date) for _ in past_year_commits],
            }
            consistency = len(past_year_active_months) / 12
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
                # TurnoverRec
                result[pr.number][developer.username] = self._calc_learnRec(
                    developer=developer,
                    pr=pr
                ) * retentionRec[developer.username]

        Cache.store(self._cache_filename, result, chunk=True)
        info_logger.info("TurnoverRec simulation finished")
        return result
