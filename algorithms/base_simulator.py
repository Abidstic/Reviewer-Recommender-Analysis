import abc
from datetime import datetime
from functools import cached_property
from typing import Union, Dict

from models import Manager, PullRequest
from utils import Cache


class BaseSimulator:
    _manager: Manager

    def __init__(self, manager: Manager, from_cache=True):
        self._manager = manager
        self._from_cache = from_cache

    @staticmethod
    def _parse_date_string(date_str: str):
        return datetime.fromisoformat(date_str.replace('Z', ''))

    @classmethod
    def calc_diff_date(cls, start: str, end: str):
        start_date = cls._parse_date_string(start)
        end_date = cls._parse_date_string(end)
        return abs((end_date - start_date).days)

    @classmethod
    def get_date_month(cls, date_str: str):
        return cls._parse_date_string(date_str).month

    @staticmethod
    def get_max_date(data_list):
        return max(data_list, key=lambda c: c.date).date

    @staticmethod
    def get_min_date(data_list):
        return min(data_list, key=lambda c: c.date).date

    @staticmethod
    def obj_time_is_between_prs(obj, prev_pr: Union[PullRequest, None], pr: PullRequest):
        if prev_pr is None:
            return obj.date <= pr.date
        return prev_pr.date <= obj.date <= pr.date

    @property
    def _cache_filename(self):
        return f'{self._manager.project}.{self.__class__.__name__}.simulation'

    @cached_property
    def cached_result(self):
        if self._from_cache:
            result = Cache.load(self._cache_filename)
            if result:
                return result
        return None

    @abc.abstractmethod
    def simulate(self) -> Dict[int, Dict[str, float]]:
        pass
