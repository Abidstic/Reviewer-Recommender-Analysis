from models import Manager
from .string_compare import METHODOLOGIES


class ProjectFilesSimilarity:

    def __init__(self, manager: Manager = None, from_cache=True):
        self._manager = manager
        self._from_cache = from_cache
        self._cache = {}

    def calculate_scores(self):
        return

    @staticmethod
    def _components(path: str):
        return path.split('/')

    def get_file_similarity(self, f1, f2, methodology) -> float:
        a, b = (f1, f2) if f1 <= f2 else (f2, f1)
        key = (methodology.__name__, a, b)
        if key in self._cache:
            return self._cache[key]
        denom = max(len(self._components(f1)), len(self._components(f2)))
        score = (methodology(f1, f2) / denom) if denom else 0.0
        self._cache[key] = score
        return score
