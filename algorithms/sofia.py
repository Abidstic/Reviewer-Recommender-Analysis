from functools import cached_property
from typing import Dict, Set

from models import PullRequest
from utils import Cache
from utils.logger import info_logger
from .base_simulator import BaseSimulator
from .chrev import ChRev
from .turnoverRec import TurnoverRec


class Sofia(BaseSimulator):
    # PAPER Eq. 13 (Mirsaeedi & Rigby 2020): k = 2 is the smallest number of
    # knowledgeable developers at which knowledge is distributed. A file with
    # <= k knowledgeable developers is abandoned (0) or hoarded (1).
    _k = 2

    @cached_property
    def _chRev_simulator(self):
        return ChRev(self._manager, from_cache=self._from_cache)

    @cached_property
    def _turnoverRec_simulator(self):
        return TurnoverRec(self._manager, from_cache=self._from_cache)

    def _calc_knowledgeable(self, filepath: str, pr: PullRequest) -> Set[str]:
        # Knowledgeable(f): developers who reviewed or modified f before the PR.
        reviewers = {
            rf.reviewer_username for rf in self._manager.review_files_list
            if rf.filepath == filepath and rf.date < pr.date
        }
        contributors = {
            c.username for c in self._manager.contributions.get(filepath, [])
            if c.date < pr.date
        }
        return reviewers | contributors

    def _pr_at_risk(self, pr: PullRequest) -> bool:
        # PAPER Eq. 13: route the whole review to TurnoverRec when ANY file
        # under review has <= k knowledgeable developers; otherwise cHRev.
        return any(
            len(self._calc_knowledgeable(filepath, pr)) <= self._k
            for filepath in pr.file_paths
        )

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
            if self._pr_at_risk(pr):
                result[pr.number] = dict(turnoverRec_result.get(pr.number, {}))
            else:
                result[pr.number] = dict(chRev_result.get(pr.number, {}))

        Cache.store(self._cache_filename, result, chunk=True)
        info_logger.info("Sofia: Simulation finished")
        return result
