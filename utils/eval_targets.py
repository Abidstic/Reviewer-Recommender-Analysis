"""Load and validate the fixed evaluation target-PR list for a repository.

The evaluation is run against a fixed set of "target" PRs (the test set). All
PRs created before each target are still used as history/context; only the
targets are scored and evaluated. To keep results comparable across the four
baseline models and across repositories, the target set must be present in the
crawl in full — if any target PR is missing, the run is aborted.
"""
import os
from datetime import datetime
from typing import Dict, List, Optional

from models import Manager
from utils.bots import is_bot


def targets_path(base_dir: str, project: str) -> str:
    return os.path.join(base_dir, f'{project}.txt')


def load_targets(path: str) -> List[int]:
    """Read PR numbers from a target file (one per line, '#' comments allowed).

    Accepts a bare number (``6734``) or a prefixed form (``express-6734``).
    Order is preserved and duplicates are dropped.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f'Target list not found: {path}')

    numbers: List[int] = []
    seen = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            for token in line.replace(',', ' ').split():
                if '-' in token:
                    token = token.rsplit('-', 1)[-1]
                if token.isdigit():
                    n = int(token)
                    if n not in seen:
                        seen.add(n)
                        numbers.append(n)
    return numbers


def _parse(date_str: Optional[str]) -> Optional[datetime]:
    if date_str is None:
        return None
    return datetime.fromisoformat(date_str.replace('Z', ''))


def last_target_date(manager, present: List[int]) -> Optional[datetime]:
    """Creation date of the latest target PR (the strict history cutoff)."""
    dates = [_parse(manager.pull_requests[n].date) for n in present]
    dates = [d for d in dates if d is not None]
    return max(dates) if dates else None


def trim_manager_before(manager, cutoff: datetime) -> Manager:
    """Return a new Manager holding only PRs/events created on or before ``cutoff``.

    This enforces the rule that the target list is the *last* set of PRs: nothing
    created after the last target is kept as history. It does NOT change results
    (per-target scoring already ignores anything dated >= each target), but it
    makes the protocol explicit and robust to re-crawls.

    NOTE: use this ONLY for scoring/history. Ground truth must still be taken
    from the full manager, because a target PR's own reviews can post-date the
    cutoff and are needed to know who actually reviewed it.
    """
    trimmed = Manager(manager.project)

    for pr in manager.pull_requests.values():
        d = _parse(pr.date)
        if d is not None and d <= cutoff:
            trimmed.add_pull_request(pr)

    for review in manager.reviews_list:
        d = _parse(review.date)
        if d is not None and d <= cutoff:
            trimmed.add_review(review)

    for comments in manager.comments.values():
        for comment in comments:
            d = _parse(comment.date)
            if d is not None and d <= cutoff:
                trimmed.add_comment(comment)

    for contribs in manager.contributions.values():
        for contribution in contribs:
            d = _parse(contribution.date)
            if d is not None and d <= cutoff:
                trimmed.add_contribution(contribution)

    for commit in manager.commits_list:
        d = _parse(commit.date)
        if d is not None and d <= cutoff:
            trimmed.add_commit(commit)

    # Files are path-only (date-independent); keep them all.
    for file in manager.files_list:
        trimmed.add_file(file)

    return trimmed


def validate_targets(manager, targets: List[int]) -> Dict[str, List[int]]:
    """Check targets against the crawl.

    Returns a dict with:
      - ``present``:   targets found in the crawl (in given order)
      - ``missing``:   targets NOT found in the crawl (abort the run if non-empty)
      - ``evaluable``: present targets that have >=1 non-author, non-bot reviewer
                       (the PRs that actually contribute to the metrics)
    """
    present, missing, evaluable = [], [], []

    reviewers_by_pr: Dict[int, List[str]] = {}
    for review in manager.reviews_list:
        reviewers_by_pr.setdefault(review.pull_number, []).append(review.reviewer_username)

    for number in targets:
        pr = manager.pull_requests.get(number)
        if pr is None:
            missing.append(number)
            continue
        present.append(number)
        real_reviewers = {
            u for u in reviewers_by_pr.get(number, [])
            if u != pr.developer_username and not is_bot(u)
        }
        if real_reviewers:
            evaluable.append(number)

    return {'present': present, 'missing': missing, 'evaluable': evaluable}
