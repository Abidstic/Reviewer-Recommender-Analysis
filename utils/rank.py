from typing import Dict


def calc_sorted_candidates(all_candidates: Dict[str, float]):
    return {k: v for k, v in sorted(all_candidates.items(), key=lambda _: _[1], reverse=True)}


def calc_rank_from_score(candidate: str, all_candidates: Dict[str, float]):
    sorted_candidates = calc_sorted_candidates(all_candidates)
    index = list(sorted_candidates.keys()).index(candidate)
    return index
