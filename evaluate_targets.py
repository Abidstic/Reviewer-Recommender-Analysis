"""Target-set evaluation driver for the four baseline recommenders.

Phase 0: validate the fixed target-PR list against the crawl (abort if any
         target is missing).
Phase 1: score only the target PRs, using the full crawl as history/context.
Phase 2: compute Precision@3, Hit@3, MAP@3 and MRR@3 over the evaluable targets.
Phase 3: print a side-by-side table and save JSON + CSV to evaluation_results/.

Usage:
    DATA_BASE_DIR=/path/to/crawl python3 evaluate_targets.py --owner expressjs --name express
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime

from algorithms import RevFinder, ChRev, TurnoverRec, Sofia
from const import DATA_BASE_DIR
from utils import ManagerFactory
from utils.eval_targets import (
    load_targets, validate_targets, targets_path, last_target_date, trim_manager_before,
)
from utils.metrics import evaluate_models

BASELINES = [
    ('RevFinder', RevFinder),
    ('ChRev', ChRev),
    ('TurnoverRec', TurnoverRec),
    ('Sofia', Sofia),
]

RESULTS_DIR = 'evaluation_results'


def parse_args():
    p = argparse.ArgumentParser(description='Target-set evaluation for the baseline recommenders.')
    p.add_argument('--owner', required=True, help='GitHub repo owner, e.g. expressjs')
    p.add_argument('--name', required=True, help='GitHub repo name, e.g. express')
    p.add_argument('--targets-dir', default='eval_targets', help='Directory holding <owner>-<name>.txt')
    p.add_argument('--targets', default=None, help='Explicit path to the target list (overrides --targets-dir)')
    p.add_argument('--k', type=int, default=3, help='Cut-off k for Precision@k, Hit@k, MAP@k (default 3)')
    return p.parse_args()


def _print_table(metrics, k):
    cols = [f'precision@{k}', f'hit@{k}', f'map@{k}', f'mrr@{k}']
    header = f'{"Model":12s}' + ''.join(f'{c:>14s}' for c in cols)
    print('\n' + header)
    print('-' * len(header))
    for model in metrics:
        row = f'{model:12s}' + ''.join(f'{metrics[model][c]:>14.4f}' for c in cols)
        print(row)


def _routing_summary(routing, present, evaluable):
    """Which branch Sofia took for each target (paper Eq. 10)."""
    by_pr = {n: routing.get(n) for n in present}
    evaluable_set = set(evaluable)

    def counts(numbers):
        c = {}
        for n in numbers:
            c[by_pr[n]] = c.get(by_pr[n], 0) + 1
        return c

    return {
        'counts_all_targets': counts(present),
        'counts_evaluable': counts([n for n in present if n in evaluable_set]),
        'by_pr': {str(n): route for n, route in by_pr.items()},
    }


def _save_results(project, k, targets, present, evaluable, metrics, sofia_routing=None):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cols = [f'precision@{k}', f'hit@{k}', f'map@{k}', f'mrr@{k}']

    json_path = os.path.join(RESULTS_DIR, f'{project}_target_eval_{stamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'project': project,
            'k': k,
            'targets_total': len(targets),
            'targets_present': len(present),
            'evaluable': len(evaluable),
            'evaluable_pr_numbers': evaluable,
            'metrics': metrics,
            'sofia_routing': sofia_routing,
        }, f, indent=2)

    csv_path = os.path.join(RESULTS_DIR, f'{project}_target_eval_{stamp}.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['model'] + cols)
        for model in metrics:
            writer.writerow([model] + [f'{metrics[model][c]:.6f}' for c in cols])

    print(f'\nSaved:\n  {json_path}\n  {csv_path}')


def main():
    args = parse_args()
    if not DATA_BASE_DIR:
        print('ERROR: DATA_BASE_DIR is not set.')
        sys.exit(2)

    project = f'{args.owner}-{args.name}'
    target_file = args.targets or targets_path(args.targets_dir, project)

    print(f'Project: {project}')
    print(f'Target list: {target_file}')

    targets = load_targets(target_file)
    print(f'Loaded {len(targets)} target PRs from the list.')

    print('Building manager from the full crawl (first time can be slow)...')
    manager = ManagerFactory(DATA_BASE_DIR, project).get_manager()

    # ---- Phase 0: validation gate ----
    report = validate_targets(manager, targets)
    present, missing, evaluable = report['present'], report['missing'], report['evaluable']

    if missing:
        print(f'\nABORT: {len(missing)} of {len(targets)} target PRs are missing from the crawl.')
        print('Missing PR numbers (re-crawl or fix the list, then retry):')
        print('  ' + ', '.join(str(n) for n in missing))
        print('\nNo evaluation was run (the fixed test set must be complete).')
        sys.exit(1)

    print(f'\nValidation passed: all {len(present)} target PRs are present.')
    print(f'Evaluable (>=1 real reviewer): {len(evaluable)} of {len(present)}.')
    print(f'  (The other {len(present) - len(evaluable)} have no reviewer and will not contribute to metrics.)')

    # ---- Strict history cutoff: drop everything created after the last target ----
    cutoff = last_target_date(manager, present)
    history = trim_manager_before(manager, cutoff)
    dropped = len(manager.pull_requests) - len(history.pull_requests)
    print(f'\nHistory cutoff: {cutoff.isoformat()} (last target PR\'s creation date).')
    print(f'  History PRs kept: {len(history.pull_requests)}; dropped (created after last target): {dropped}.')

    # ---- Phase 1: target-restricted scoring (on the trimmed history) ----
    print('\nScoring the target PRs with each baseline (history <= cutoff as context)...')
    results = {}
    sofia_routing = None
    for name, Algo in BASELINES:
        sim = Algo(history, from_cache=False, target_pr_numbers=present)
        result = sim.simulate()
        results[name] = result
        scored = sum(1 for n in present if result.get(n))
        print(f'  {name:12s} scored {len(result)} PRs; {scored} produced >=1 candidate.')
        if isinstance(sim, Sofia):
            sofia_routing = sim.routing

    # ---- Phase 2: metrics over the evaluable targets ----
    metrics, metric_evaluable = evaluate_models(manager, present, results, k=args.k)
    routing_summary = _routing_summary(sofia_routing or {}, present, metric_evaluable)

    # ---- Phase 3: comparison table + saved results ----
    print(f'\nMetrics over {len(metric_evaluable)} evaluable target PRs (k={args.k}):')
    _print_table(metrics, args.k)
    print('\nSofia routing (all targets):', routing_summary['counts_all_targets'])
    print('Sofia routing (evaluable):  ', routing_summary['counts_evaluable'])
    _save_results(project, args.k, targets, present, metric_evaluable, metrics, routing_summary)

    print('\nDone.')
    return results, metrics


if __name__ == '__main__':
    main()
