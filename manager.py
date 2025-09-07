import argparse

from algorithms import Sofia, RevFinder, ChRev, TurnoverRec
from utils import ManagerFactory
from evaluation import Evaluation
from const import DATA_BASE_DIR
from utils.logger import info_logger

parser = argparse.ArgumentParser(description='Run algorithms on a GitHub project.')
parser.add_argument(
    '--r_owner',
    type=str,
    help="The owner of the GitHub project.",
    nargs=1,
)
parser.add_argument(
    '--r_name',
    type=str,
    help="The name of the GitHub project.",
    nargs=1,
)
parser.add_argument('--no-cache', action='store_true', help='If set, the cache will not be used.')


def validate(args):
    if args.r_owner is None or args.r_name is None:
        raise Exception('please provide both owner and name of your repo')

    if not DATA_BASE_DIR:
        raise Exception('DATA_BASE_DIR is not set.')


def run_algorithm(algorithm, args):
    validate(args)
    info_logger.info(f'algorithm {args.algorithm} for project={args.r_owner[0]}/{args.r_name[0]} started')
    manager = ManagerFactory(
        DATA_BASE_DIR,
        f'{args.r_owner[0]}-{args.r_name[0]}',
    ).get_manager()
    algorithm(manager, from_cache=not args.no_cache)


def run_evaluation(args):
    validate(args)
    info_logger.info(f'evaluation for project={args.r_owner[0]}/{args.r_name[0]} started')
    manager = ManagerFactory(
        DATA_BASE_DIR,
        f'{args.r_owner[0]}-{args.r_name[0]}',
    ).get_manager()
    simulators = [
        Sofia(manager, from_cache=not args.no_cache),
        RevFinder(manager, from_cache=not args.no_cache),
        ChRev(manager, from_cache=not args.no_cache),
        TurnoverRec(manager, from_cache=not args.no_cache),
    ]
    Evaluation(manager, simulators).evaluate()


FUNCTION_MAP = {
    'algo-revFinder': lambda args: run_algorithm(RevFinder, args),
    'algo-chRev': lambda args: run_algorithm(ChRev, args),
    'algo-turnoverRec': lambda args: run_algorithm(TurnoverRec, args),
    'algo-sofia': lambda args: run_algorithm(Sofia, args),
    'evaluate': lambda args: run_evaluation(args),
}

parser.add_argument('command', choices=FUNCTION_MAP.keys(), help='The command to run.')

global_args = parser.parse_args()
func = FUNCTION_MAP[global_args.command]
func(global_args)
