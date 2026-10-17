"""Focused ranking metrics for the target-set evaluation.

Metrics (default k = 3), averaged over the evaluable targets (the target PRs
that have at least one real reviewer). The same evaluable set is used for every
model, so the numbers are directly comparable.

    Precision@k : (correct in top-k) / k
    Hit@k       : 1 if any of the top-k is a real reviewer, else 0
    MAP@k       : (1/|A_p|) * sum_{i=1..k} Precision@i(p) * rel_p(i),  averaged over p
                  (|A_p| = number of actual reviewers of PR p; rel_p(i) = 1 if the
                   i-th recommendation is an actual reviewer)
    MRR@k       : 1 / rank of the first actual reviewer WITHIN THE TOP k; 0 if none
                  of the top-k recommendations is an actual reviewer
"""
from typing import Dict, List, Set, Tuple

from utils.bots import is_bot


def build_ground_truth(manager, numbers: List[int]) -> Dict[int, Set[str]]:
    """Real reviewers (non-author, non-bot) for each PR that has any."""
    reviewers_by_pr: Dict[int, List[str]] = {}
    for review in manager.reviews_list:
        reviewers_by_pr.setdefault(review.pull_number, []).append(review.reviewer_username)

    ground_truth: Dict[int, Set[str]] = {}
    for number in numbers:
        pr = manager.pull_requests.get(number)
        if pr is None:
            continue
        reviewers = {
            u for u in reviewers_by_pr.get(number, [])
            if u != pr.developer_username and not is_bot(u)
        }
        if reviewers:
            ground_truth[number] = reviewers
    return ground_truth


def precision_at_k(ranked: List[str], relevant: Set[str], k: int) -> float:
    top_k = ranked[:k]
    correct = sum(1 for u in top_k if u in relevant)
    return correct / k


def hit_at_k(ranked: List[str], relevant: Set[str], k: int) -> float:
    return 1.0 if any(u in relevant for u in ranked[:k]) else 0.0


def average_precision_at_k(ranked: List[str], relevant: Set[str], k: int) -> float:
    # AP@k(p) = (1/|A_p|) * sum_{i=1..k} Precision@i(p) * rel_p(i)   [Eq. 2]
    # At each relevant position i, hits/i == Precision@i and rel_p(i) == 1.
    hits = 0
    running = 0.0
    for i, user in enumerate(ranked[:k], start=1):
        if user in relevant:
            hits += 1
            running += hits / i
    denom = len(relevant)
    return running / denom if denom else 0.0


def reciprocal_rank(ranked: List[str], relevant: Set[str], k: int) -> float:
    # Paper Eq. 3: first actual reviewer within the top k; 0 if none in top k.
    for i, user in enumerate(ranked[:k], start=1):
        if user in relevant:
            return 1.0 / i
    return 0.0


def evaluate_models(
    manager,
    target_numbers: List[int],
    results_by_model: Dict[str, Dict[int, Dict[str, float]]],
    k: int = 3,
) -> Tuple[Dict[str, Dict[str, float]], List[int]]:
    """Return (metrics_by_model, evaluable_pr_numbers)."""
    ground_truth = build_ground_truth(manager, target_numbers)
    evaluable = sorted(ground_truth.keys())
    n = len(evaluable) or 1

    metrics: Dict[str, Dict[str, float]] = {}
    for model, result in results_by_model.items():
        p = h = ap = rr = 0.0
        for number in evaluable:
            ranked = list(result.get(number, {}).keys())  # already score-desc ordered
            relevant = ground_truth[number]
            p += precision_at_k(ranked, relevant, k)
            h += hit_at_k(ranked, relevant, k)
            ap += average_precision_at_k(ranked, relevant, k)
            rr += reciprocal_rank(ranked, relevant, k)
        metrics[model] = {
            f'precision@{k}': p / n,
            f'hit@{k}': h / n,
            f'map@{k}': ap / n,
            f'mrr@{k}': rr / n,
        }
    return metrics, evaluable
