from functools import cached_property
from typing import Dict, Set

from models import PullRequest
from utils import Cache
from utils.logger import info_logger
from .base_simulator import BaseSimulator
from .chrev import ChRev
from .turnoverRec import TurnoverRec


class Sofia(BaseSimulator):
    _d = 2

    @cached_property
    def _chRev_simulator(self):
        return ChRev(self._manager, from_cache=self._from_cache)

    @cached_property
    def _turnoverRec_simulator(self):
        return TurnoverRec(self._manager, from_cache=self._from_cache)

    def _calc_knowledgeable(self, pr: PullRequest):
        result: Dict[str, Set[str]] = {}
        for filepath in pr.file_paths:
            if filepath not in self._manager.contributions.keys():
                continue

            files_reviewer_username = [
                _.reviewer_username for _ in self._manager.review_files_list if
                filepath == _.filepath and pr.date > _.date
            ]

            contributors = [
                _.username for _ in self._manager.contributions[filepath] if
                _.filename == filepath and pr.date > _.date
            ]

            result[filepath] = {*files_reviewer_username, *contributors}

        return result

    def simulate(self):
        info_logger.info("Simulating Sofia...")
        if self.cached_result:
            info_logger.info("Sofia: Using cached result...")
            return self.cached_result

        chRev_result = self._chRev_simulator.simulate()
        turnoverRec_result = self._turnoverRec_simulator.simulate()

        # {[pr_number]: { [dev_username]: score }}
        result: Dict[int, Dict[str, float]] = {}

        pr_len = len(self._manager.pull_requests_list)
        for index, pr in enumerate(self._manager.pull_requests_list):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            result[pr.number] = {}
            knowledgeable = self._calc_knowledgeable(pr=pr)
            knowledgeable_list = list(knowledgeable.values())
            for developer in self._manager.developers_list:
                if all(len(_) <= self._d for _ in knowledgeable_list):
                    result[pr.number][developer.username] = chRev_result[pr.number][developer.username]
                else:
                    result[pr.number][developer.username] = turnoverRec_result[pr.number][developer.username]

        Cache.store(self._cache_filename, result, chunk=True)
        info_logger.info("Sofia: Simulation finished")
        return result
