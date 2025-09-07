from copy import deepcopy
from typing import Dict, Union

from utils import Cache
from utils.logger import info_logger
from .base_simulator import BaseSimulator
from models import Developer, PullRequest


class ChRev(BaseSimulator):

    def _calc_xFactor(
            self,
            developer: Developer,
            pr: PullRequest,
            prev_pr: Union[PullRequest, None],
    ) -> Dict[str, float]:
        file_scores = {}
        for file in self._manager.files_list:
            if file.filepath not in pr.file_paths or file.filepath not in self._manager.comments.keys():
                continue
            score = 0
            all_file_comments = self._manager.comments[file.filepath]
            developer_comments = [
                _ for _ in all_file_comments if
                _.reviewer_username == developer.username and self.obj_time_is_between_prs(_, prev_pr=prev_pr, pr=pr)
            ]
            score += len(developer_comments) / len(all_file_comments)

            all_file_contributions = self._manager.contributions[file.filepath]
            all_developer_contributions = [
                _ for _ in all_file_contributions if
                _.username == developer.username and self.obj_time_is_between_prs(_, prev_pr=prev_pr, pr=pr)
            ]

            if len(all_developer_contributions) == 0 or len(all_file_contributions) == 0:
                continue

            total_most_recent_comment_date = self.get_max_date(all_file_contributions)
            developer_most_recent_comment_date = self.get_max_date(all_developer_contributions)

            total_diff = self.calc_diff_date(
                self.get_min_date(all_file_contributions),
                total_most_recent_comment_date,
            )
            developer_diff = self.calc_diff_date(
                self.get_min_date(all_developer_contributions),
                developer_most_recent_comment_date,
            )

            score += (developer_diff / total_diff) if total_diff else 1

            diff_date = self.calc_diff_date(
                total_most_recent_comment_date,
                developer_most_recent_comment_date,
            )

            score += 1 / (diff_date + 1)

            file_scores[file.filepath] = score

        return file_scores

    def simulate(self):
        info_logger.info("Simulating ChRev...")
        if self.cached_result:
            info_logger.info("ChRev simulation loaded from cache")
            return self.cached_result

        # {[pr_number]: { [dev_username]: score }}
        result: Dict[int, Dict[str, float]] = {}
        # {[username]: { [filepath]: score }}
        scores: Dict[str, Dict[str, float]] = {}

        pr_len = len(self._manager.pull_requests_list)
        prev_pr = None
        for index, pr in enumerate(self._manager.pull_requests_list):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            result[pr.number] = {}
            for developer in self._manager.developers_list:
                dev_scores = self._calc_xFactor(developer=developer, pr=pr, prev_pr=prev_pr)
                if developer.username not in scores:
                    scores[developer.username] = deepcopy(dev_scores)
                else:
                    for filepath, score in dev_scores.items():
                        if filepath not in scores[developer.username]:
                            scores[developer.username][filepath] = score
                        else:
                            scores[developer.username][filepath] += score
                result[pr.number][developer.username] = sum(list(scores[developer.username].values()))
            prev_pr = pr

        Cache.store(self._cache_filename, result, chunk=True)
        info_logger.info("ChRev simulation stored in cache")
        return result
