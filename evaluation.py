from typing import List
from ranx import compare, Qrels, Run

from algorithms import BaseSimulator
from models import Manager


class Evaluation:
    _METRICS = [
        'mrr',
    ]

    def __init__(self, manager: Manager, simulators: List[BaseSimulator]):
        self._manager = manager
        self._simulators = simulators

    def evaluate(self):
        report = compare(
            qrels=self._qrels,
            runs=self._runs,
            make_comparable=True,
            metrics=self._METRICS,
        )

        print(report)

    @property
    def _qrels(self):
        data = {}
        for pr in self._manager.pull_requests_list:
            mapping = {
                _.reviewer_username: 1
                for _ in self._manager.reviews_list
                if _.pull_number == pr.number
            }
            if mapping:
                data[str(pr.number)] = mapping
        return Qrels(data)

    @property
    def _runs(self):
        runs = []
        for simulator in self._simulators:
            simulator_results = simulator.simulate()
            runs.append(
                Run(
                    name=simulator.__class__.__name__,
                    run={
                        str(key): val for key, val in simulator_results.items()
                    }
                )
            )

        return runs
