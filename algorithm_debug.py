import os
from utils import ManagerFactory
from const import DATA_BASE_DIR
from algorithms import Sofia, RevFinder, ChRev, TurnoverRec

def debug_algorithm_step_by_step(repo_name, algorithm_class, algorithm_name):
    """
    Debug an algorithm step by step to see where it fails.
    """
    print(f"\n{'='*60}")
    print(f"DEBUGGING {algorithm_name} ALGORITHM")
    print(f"{'='*60}")
    
    try:
        # Create manager
        manager = ManagerFactory(DATA_BASE_DIR, repo_name, from_cache=False).get_manager()
        print(f"Manager loaded: {len(manager.pull_requests_list)} PRs")
        
        # Create algorithm instance
        algorithm = algorithm_class(manager)
        print(f"Algorithm instance created: {algorithm_name}")
        
        # Debug specific algorithm logic
        if algorithm_name == "Sofia":
            debug_sofia(algorithm, manager)
        elif algorithm_name == "ChRev":
            debug_chrev(algorithm, manager)
        elif algorithm_name == "TurnoverRec":
            debug_turnover_rec(algorithm, manager)
        elif algorithm_name == "RevFinder":
            debug_rev_finder(algorithm, manager)
        
    except Exception as e:
        print(f"Error in {algorithm_name} debug: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def debug_sofia(sofia, manager):
    """Debug Sofia algorithm specifically"""
    print(f"\n--- SOFIA DEBUG ---")
    
    try:
        # Sofia uses ChRev and TurnoverRec internally
        print("1. Testing ChRev dependency...")
        chrev_result = sofia._chRev_simulator.simulate()
        print(f"   ChRev returned: {len(chrev_result) if chrev_result else 0} PRs")
        
        print("2. Testing TurnoverRec dependency...")
        turnover_result = sofia._turnoverRec_simulator.simulate()
        print(f"   TurnoverRec returned: {len(turnover_result) if turnover_result else 0} PRs")
        
        # Test knowledgeable calculation for a sample PR
        if manager.pull_requests_list:
            sample_pr = manager.pull_requests_list[0]
            print(f"3. Testing knowledgeable calculation for PR {sample_pr.number}...")
            
            knowledgeable = sofia._calc_knowledgeable(sample_pr)
            print(f"   Knowledgeable files: {len(knowledgeable)}")
            for filepath, experts in list(knowledgeable.items())[:3]:
                print(f"   {filepath}: {len(experts)} experts")
                
    except Exception as e:
        print(f"Sofia debug error: {e}")

def debug_chrev(chrev, manager):
    """Debug ChRev algorithm specifically"""
    print(f"\n--- CHREV DEBUG ---")
    
    try:
        # Test with first few PRs
        pr_list = manager.pull_requests_list[:3]
        prev_pr = None
        
        for i, pr in enumerate(pr_list):
            print(f"{i+1}. Testing PR {pr.number}...")
            print(f"   Files in PR: {len(pr.file_paths)}")
            
            # Check if PR files exist in manager.comments
            files_with_comments = []
            for filepath in pr.file_paths:
                if filepath in manager.comments:
                    files_with_comments.append(filepath)
            
            print(f"   Files with comments: {len(files_with_comments)}")
            
            # Test xFactor calculation for a sample developer
            if manager.developers_list:
                sample_dev = manager.developers_list[0]
                print(f"   Testing xFactor for developer: {sample_dev.username}")
                
                try:
                    x_factor = chrev._calc_xFactor(sample_dev, pr, prev_pr)
                    print(f"   xFactor result: {len(x_factor)} files scored")
                except Exception as e:
                    print(f"   xFactor error: {e}")
            
            prev_pr = pr
            
    except Exception as e:
        print(f"ChRev debug error: {e}")

def debug_turnover_rec(turnover, manager):
    """Debug TurnoverRec algorithm specifically"""
    print(f"\n--- TURNOVER REC DEBUG ---")
    
    try:
        # Test with a sample PR
        if manager.pull_requests_list:
            sample_pr = manager.pull_requests_list[0]
            print(f"1. Testing with PR {sample_pr.number}...")
            
            # Test ReviewerKnows calculation
            if manager.developers_list:
                sample_dev = manager.developers_list[0]
                print(f"2. Testing ReviewerKnows for {sample_dev.username}...")
                
                try:
                    knows_score = turnover._calc_ReviewerKnows(sample_dev, sample_pr)
                    print(f"   ReviewerKnows score: {knows_score}")
                except Exception as e:
                    print(f"   ReviewerKnows error: {e}")
                
                # Test learnRec
                try:
                    learn_score = turnover._calc_learnRec(sample_dev, sample_pr)
                    print(f"   LearnRec score: {learn_score}")
                except Exception as e:
                    print(f"   LearnRec error: {e}")
            
            # Test totalCommitReview
            try:
                total_commit_review = turnover._calc_totalCommitReview(sample_pr)
                print(f"3. Total commit/review count: {total_commit_review}")
            except Exception as e:
                print(f"   TotalCommitReview error: {e}")
                
            # Test RetentionRec
            try:
                retention = turnover._calc_RetentionRec(sample_pr)
                print(f"4. RetentionRec calculated for {len(retention)} developers")
                if retention:
                    sample_retention = list(retention.items())[0]
                    print(f"   Sample retention: {sample_retention}")
            except Exception as e:
                print(f"   RetentionRec error: {e}")
                
    except Exception as e:
        print(f"TurnoverRec debug error: {e}")

def debug_rev_finder(rev_finder, manager):
    """Debug RevFinder algorithm specifically"""
    print(f"\n--- REV FINDER DEBUG ---")
    
    try:
        # Test file similarity calculation
        print("1. Testing file similarity...")
        try:
            rev_finder.file_similarity.calculate_scores()
            print("   File similarity scores calculated")
        except Exception as e:
            print(f"   File similarity error: {e}")
        
        # Test with a sample PR
        if manager.pull_requests_list:
            sample_pr = manager.pull_requests_list[0]
            print(f"2. Testing with PR {sample_pr.number}...")
            print(f"   Files in PR: {sample_pr.file_paths}")
            
            # Test candidates calculation
            try:
                candidates = rev_finder.calc_candidates_with_methodologies(sample_pr)
                print(f"   Candidates calculated: {len(candidates)} methodologies")
                for method_name, method_candidates in candidates.items():
                    print(f"   {method_name}: {len(method_candidates)} candidates")
            except Exception as e:
                print(f"   Candidates calculation error: {e}")
                
    except Exception as e:
        print(f"RevFinder debug error: {e}")

def debug_all_algorithms(repo_name):
    """Debug all algorithms for a repository"""
    print(f"🔍 DEBUGGING ALL ALGORITHMS FOR: {repo_name}")
    print("=" * 80)
    
    algorithms = [
        (Sofia, "Sofia"),
        (ChRev, "ChRev"), 
        (TurnoverRec, "TurnoverRec"),
        (RevFinder, "RevFinder")
    ]
    
    for algo_class, algo_name in algorithms:
        debug_algorithm_step_by_step(repo_name, algo_class, algo_name)
        print("\n" + "="*60 + "\n")

def debug_data_relationships(repo_name):
    """Debug the relationships between different data components"""
    print(f"\n{'='*60}")
    print(f"DEBUGGING DATA RELATIONSHIPS: {repo_name}")
    print(f"{'='*60}")
    
    try:
        manager = ManagerFactory(DATA_BASE_DIR, repo_name, from_cache=False).get_manager()
        
        # Check PR-Review relationships
        prs_with_reviews = 0
        prs_without_reviews = 0
        
        for pr in manager.pull_requests_list:
            pr_reviews = [r for r in manager.reviews_list if r.pull_number == pr.number]
            if pr_reviews:
                prs_with_reviews += 1
            else:
                prs_without_reviews += 1
        
        print(f"PR-Review Relationships:")
        print(f"  PRs with reviews: {prs_with_reviews}")
        print(f"  PRs without reviews: {prs_without_reviews}")
        
        # Check File-Comment relationships
        files_with_comments = len(manager.comments)
        total_files = len(manager.files)
        
        print(f"\nFile-Comment Relationships:")
        print(f"  Files with comments: {files_with_comments}")
        print(f"  Total files: {total_files}")
        
        # Check Review-File relationships  
        review_files_count = len(manager.review_files)
        print(f"\nReview-File Relationships:")
        print(f"  Review files: {review_files_count}")
        
        # Sample some relationships
        if manager.pull_requests_list:
            sample_pr = manager.pull_requests_list[0]
            pr_reviews = [r for r in manager.reviews_list if r.pull_number == sample_pr.number]
            
            print(f"\nSample PR {sample_pr.number}:")
            print(f"  Files: {len(sample_pr.file_paths)}")
            print(f"  Reviews: {len(pr_reviews)}")
            
            if sample_pr.file_paths:
                sample_file = sample_pr.file_paths[0]
                file_comments = manager.comments.get(sample_file, [])
                print(f"  Comments on '{sample_file}': {len(file_comments)}")
        
    except Exception as e:
        print(f"Error debugging relationships: {e}")

if __name__ == "__main__":
    # Interactive debug mode
    repositories = []
    if DATA_BASE_DIR and os.path.exists(DATA_BASE_DIR):
        for item in os.listdir(DATA_BASE_DIR):
            item_path = os.path.join(DATA_BASE_DIR, item)
            if os.path.isdir(item_path):
                if (os.path.exists(os.path.join(item_path, 'pull')) and 
                    os.path.exists(os.path.join(item_path, 'commit'))):
                    repositories.append(item)
    
    print("Available repositories:")
    for i, repo in enumerate(repositories, 1):
        print(f"{i}. {repo}")
    
    try:
        choice = int(input(f"\nSelect repository (1-{len(repositories)}): "))
        if 1 <= choice <= len(repositories):
            selected_repo = repositories[choice - 1]
            
            print("\nDebug options:")
            print("1. Debug data relationships")
            print("2. Debug all algorithms")
            print("3. Debug specific algorithm")
            
            debug_choice = int(input("Select option (1-3): "))
            
            if debug_choice == 1:
                debug_data_relationships(selected_repo)
            elif debug_choice == 2:
                debug_all_algorithms(selected_repo)
            elif debug_choice == 3:
                print("\nAlgorithms:")
                print("1. Sofia")
                print("2. ChRev") 
                print("3. TurnoverRec")
                print("4. RevFinder")
                
                algo_choice = int(input("Select algorithm (1-4): "))
                algorithms = [
                    (Sofia, "Sofia"),
                    (ChRev, "ChRev"),
                    (TurnoverRec, "TurnoverRec"), 
                    (RevFinder, "RevFinder")
                ]
                
                if 1 <= algo_choice <= 4:
                    algo_class, algo_name = algorithms[algo_choice - 1]
                    debug_algorithm_step_by_step(selected_repo, algo_class, algo_name)
                    
    except ValueError:
        print("Please enter a valid number.")