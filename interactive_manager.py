import os
from algorithms import Sofia, RevFinder, ChRev, TurnoverRec
from utils import ManagerFactory
from evaluation import Evaluation
from const import DATA_BASE_DIR
from utils.logger import info_logger


def discover_repositories():
    """Find available crawled repositories"""
    repositories = []
    
    if not DATA_BASE_DIR or not os.path.exists(DATA_BASE_DIR):
        print("ERROR: DATA_BASE_DIR not set or directory doesn't exist")
        return repositories
    
    for item in os.listdir(DATA_BASE_DIR):
        item_path = os.path.join(DATA_BASE_DIR, item)
        if os.path.isdir(item_path):
            # Check if it looks like a repository folder
            if (os.path.exists(os.path.join(item_path, 'pull')) and 
                os.path.exists(os.path.join(item_path, 'commit'))):
                repositories.append(item)
    
    return repositories


def select_repository():
    """Interactive repository selection"""
    repositories = discover_repositories()
    
    if not repositories:
        print("No crawled repositories found!")
        return None
    
    print("\nAvailable repositories:")
    for i, repo in enumerate(repositories, 1):
        print(f"{i}. {repo}")
    
    while True:
        try:
            choice = int(input(f"\nSelect repository (1-{len(repositories)}): "))
            if 1 <= choice <= len(repositories):
                selected = repositories[choice - 1]
                print(f"Selected: {selected}")
                return selected
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def check_repository_data(repo_name):
    """Check repository data quality before running algorithms"""
    try:
        factory = ManagerFactory(DATA_BASE_DIR, repo_name)
        summary = factory.get_data_summary()
        
        print(f"\nRepository Summary for {repo_name}:")
        
        if not summary.get('structure_compatible', False):
            print("  ❌ Data structure not compatible")
            return False
        
        if 'data_counts' in summary:
            counts = summary['data_counts']
            pr_count = counts.get('pull_requests', 0)
            review_count = counts.get('reviews', 0)
            dev_count = counts.get('developers', 0)
            
            print(f"  Pull Requests: {pr_count}")
            print(f"  Reviews: {review_count}")
            print(f"  Developers: {dev_count}")
            
            # Check for minimum data requirements
            if pr_count == 0:
                print("  ❌ No pull requests found")
                return False
            
            if dev_count == 0:
                print("  ❌ No developers found")
                return False
            
            if review_count == 0:
                print("  ⚠️  Warning: No reviews found - algorithms may not work properly")
                response = input("  Continue anyway? (y/n): ").strip().lower()
                return response == 'y'
            
            # Calculate review coverage
            coverage = (review_count / pr_count) * 100 if pr_count > 0 else 0
            print(f"  Review Coverage: {coverage:.1f}%")
            
            if coverage < 5:
                print("  ⚠️  Warning: Very low review coverage - results may be unreliable")
                response = input("  Continue anyway? (y/n): ").strip().lower()
                return response == 'y'
            
            print("  ✅ Repository looks good for analysis")
            return True
        
        return True
        
    except Exception as e:
        print(f"  Error checking repository: {e}")
        return False


def select_action():
    """Select what to run"""
    print("\nWhat would you like to run?")
    print("1. Single Algorithm")
    print("2. Full Evaluation (All Algorithms)")
    
    while True:
        try:
            choice = int(input("Select option (1-2): "))
            if choice in [1, 2]:
                return choice
            else:
                print("Invalid choice. Please enter 1 or 2.")
        except ValueError:
            print("Please enter a valid number.")


def select_algorithm():
    """Select a single algorithm"""
    algorithms = {
        1: ("Sofia", Sofia),
        2: ("RevFinder", RevFinder),
        3: ("ChRev", ChRev),
        4: ("TurnoverRec", TurnoverRec)
    }
    
    print("\nAvailable algorithms:")
    for num, (name, _) in algorithms.items():
        print(f"{num}. {name}")
    
    while True:
        try:
            choice = int(input(f"Select algorithm (1-{len(algorithms)}): "))
            if choice in algorithms:
                return algorithms[choice]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def run_single_algorithm(repo_name, algorithm_name, algorithm_class):
    """Run a single algorithm"""
    print(f"\nRunning {algorithm_name} on {repo_name}...")
    
    try:
        # Create manager
        manager = ManagerFactory(DATA_BASE_DIR, repo_name).get_manager()
        
        # Run algorithm
        algorithm_instance = algorithm_class(manager)
        result = algorithm_instance.simulate()
        
        print(f"\n{algorithm_name} completed successfully!")
        print(f"Generated recommendations for {len(result)} pull requests")
        
        # Show some sample results
        if result:
            print("\nSample recommendations (first 3 PRs):")
            count = 0
            for pr_num, scores in result.items():
                if count >= 3:
                    break
                print(f"\nPR #{pr_num}:")
                # Sort developers by score and show top 3
                sorted_devs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                for i, (dev, score) in enumerate(sorted_devs, 1):
                    print(f"  {i}. {dev}: {score:.3f}")
                count += 1
        
        return result
        
    except ZeroDivisionError as e:
        print(f"❌ Error: Division by zero in {algorithm_name}")
        print("This usually happens when there's insufficient data for the algorithm.")
        info_logger.error(f"Division by zero in {algorithm_name} for {repo_name}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error running {algorithm_name}: {e}")
        info_logger.error(f"Error running {algorithm_name} for {repo_name}: {e}")
        return None


def run_evaluation(repo_name):
    """Run comprehensive evaluation with all algorithms"""
    print(f"\nRunning comprehensive evaluation for {repo_name}...")
    
    try:
        # Create manager
        manager = ManagerFactory(DATA_BASE_DIR, repo_name).get_manager()
        
        # Initialize algorithms and track results
        algorithms = [
           
            ("RevFinder", RevFinder), 
            ("ChRev", ChRev),
            ("TurnoverRec", TurnoverRec),
            ("Sofia", Sofia),
        ]
        
        successful_results = {}
        failed_algorithms = []
        
        for algo_name, algo_class in algorithms:
            try:
                print(f"  Running {algo_name}...")
                simulator = algo_class(manager)
                result = simulator.simulate()
                if result:
                    successful_results[algo_name] = result
                    print(f"  ✅ {algo_name} completed ({len(result)} PRs)")
                else:
                    failed_algorithms.append(algo_name)
                    print(f"  ❌ {algo_name} returned no results")
            except Exception as e:
                failed_algorithms.append(algo_name)
                print(f"  ❌ {algo_name} failed: {e}")
        
        if not successful_results:
            print("\n❌ No algorithms completed successfully. Cannot run evaluation.")
            return
        
        if failed_algorithms:
            print(f"\n⚠️  Warning: {len(failed_algorithms)} algorithms failed: {failed_algorithms}")
            print(f"Continuing with {len(successful_results)} successful algorithms.")
        
        # Show detailed evaluation using advanced evaluation module
        from advanced_evaluation import run_advanced_evaluation
        detailed_results = run_advanced_evaluation(manager, successful_results)
        
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        info_logger.error(f"Error during evaluation for {repo_name}: {e}")


def main():
    """Main function"""
    print("GitHub Reviewer Recommendation System")
    print("=" * 50)
    
    # Select repository
    repo_name = select_repository()
    if not repo_name:
        return
    
    # Check repository data quality
    if not check_repository_data(repo_name):
        print("Cannot proceed with current repository.")
        return
    
    # Select action
    action = select_action()
    
    if action == 1:
        # Single algorithm
        algo_name, algo_class = select_algorithm()
        run_single_algorithm(repo_name, algo_name, algo_class)
    else:
        # Full evaluation
        run_evaluation(repo_name)


if __name__ == "__main__":
    main()