from functools import cached_property
from typing import Dict

from utils.logger import info_logger
from .base_simulator import BaseSimulator
from .chrev import ChRev
from .turnoverRec import TurnoverRec


class Sofia(BaseSimulator):

    _d = 2

    def __init__(self, manager, from_cache=True, target_pr_numbers=None):
        super().__init__(manager, from_cache, target_pr_numbers)
        self.routing: Dict[int, str] = {}

    @cached_property
    def _turnoverRec(self) -> TurnoverRec:
        return TurnoverRec(self._manager, from_cache=self._from_cache,
                           target_pr_numbers=self._target_pr_numbers)

    @cached_property
    def _chRev(self) -> ChRev:
        return ChRev(self._manager, from_cache=self._from_cache,
                     target_pr_numbers=self._target_pr_numbers)

    def _pr_at_risk(self, pr, pr_dt) -> bool:
        knowledge = self._turnoverRec.knowledge
        return any(
            len(knowledge.knowledgeable(path, pr_dt)) <= self._d
            for path in pr.file_paths
        )

    def simulate(self):
        info_logger.info("Simulating Sofia...")
        if self.cached_result:
            info_logger.info("Sofia: Using cached result...")
            return self.cached_result

        turnover_result = self._turnoverRec.simulate()
        chrev_result = self._chRev.simulate()

        result: Dict[int, Dict[str, float]] = {}
        pr_len = len(self._target_prs)
        for index, pr in enumerate(self._target_prs):
            info_logger.info(f'Calculating candidates: {index + 1}/{pr_len}')
            pr_dt = self.parse_dt(pr.date)
            turnover = turnover_result.get(pr.number, {})
            chrev = chrev_result.get(pr.number, {})

            if pr_dt is not None and self._pr_at_risk(pr, pr_dt):
                if turnover:
                    result[pr.number] = dict(turnover)
                    self.routing[pr.number] = 'TurnoverRec'
                else:
                    result[pr.number] = dict(chrev)
                    self.routing[pr.number] = 'cHRev (fallback)'
            else:
                result[pr.number] = dict(chrev)
                self.routing[pr.number] = 'cHRev'

        self._store_result(result)
        info_logger.info("Sofia: Simulation finished")
        return result
