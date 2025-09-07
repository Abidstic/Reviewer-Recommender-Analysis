import os
import json
from utils import ManagerFactory
from const import DATA_BASE_DIR
from utils.logger import info_logger

def debug_crawled_data_structure(repo_name):
    """
    Debug function to inspect the actual crawled data structure
    and compare it with what the system expects.
    """
    print(f"\n{'='*60}")
    print(f"DEBUGGING CRAWLED DATA STRUCTURE: {repo_name}")
    print(f"{'='*60}")
    
    repo_path = os.path.join(DATA_BASE_DIR, repo_name)
    
    if not os.path.exists(repo_path):
        print(f"ERROR: Repository path does not exist: {repo_path}")
        return
    
    print(f"Repository path: {repo_path}")
    
    # Check main folder structure
    print(f"\n1. MAIN FOLDER STRUCTURE:")
    print("-" * 30)
    
    for item in os.listdir(repo_path):
        item_path = os.path.join(repo_path, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}/")
        else:
            print(f"  📄 {item}")
    
    # Check pull folder structure
    pull_path = os.path.join(repo_path, 'pull')
    if os.path.exists(pull_path):
        print(f"\n2. PULL FOLDER STRUCTURE:")
        print("-" * 30)
        
        # Check for all_data.json
        all_data_file = os.path.join(pull_path, 'all_data.json')
        if os.path.exists(all_data_file):
            print(f"  ✅ pull/all_data.json exists")
            
            # Check file size and sample content
            file_size = os.path.getsize(all_data_file)
            print(f"  📊 File size: {file_size} bytes")
            
            try:
                with open(all_data_file, 'r') as f:
                    data = json.load(f)
                    print(f"  📊 Number of PRs: {len(data) if isinstance(data, list) else 'Not a list'}")
                    
                    if isinstance(data, list) and len(data) > 0:
                        print(f"  📋 Sample PR structure:")
                        sample_pr = data[0]
                        for key in sample_pr.keys():
                            print(f"    - {key}: {type(sample_pr[key])}")
            except Exception as e:
                print(f"  ❌ Error reading pull/all_data.json: {e}")
        else:
            print(f"  ❌ pull/all_data.json NOT found")
        
        # Check PR subdirectories
        pr_folders = [item for item in os.listdir(pull_path) 
                     if os.path.isdir(os.path.join(pull_path, item)) and item.isdigit()]
        print(f"  📊 PR subdirectories found: {len(pr_folders)}")
        
        if pr_folders:
            sample_pr_folder = pr_folders[0]
            sample_pr_path = os.path.join(pull_path, sample_pr_folder)
            print(f"  📋 Sample PR folder structure ({sample_pr_folder}):")
            
            for subitem in os.listdir(sample_pr_path):
                subitem_path = os.path.join(sample_pr_path, subitem)
                if os.path.isdir(subitem_path):
                    all_data_path = os.path.join(subitem_path, 'all_data.json')
                    exists = "✅" if os.path.exists(all_data_path) else "❌"
                    print(f"    📁 {subitem}/ {exists}")
    
    # Check commit folder structure
    commit_path = os.path.join(repo_path, 'commit')
    if os.path.exists(commit_path):
        print(f"\n3. COMMIT FOLDER STRUCTURE:")
        print("-" * 30)
        
        # Check for all_data.json
        all_data_file = os.path.join(commit_path, 'all_data.json')
        if os.path.exists(all_data_file):
            print(f"  ✅ commit/all_data.json exists")
            
            try:
                with open(all_data_file, 'r') as f:
                    data = json.load(f)
                    print(f"  📊 Number of commits: {len(data) if isinstance(data, list) else 'Not a list'}")
            except Exception as e:
                print(f"  ❌ Error reading commit/all_data.json: {e}")
        else:
            print(f"  ❌ commit/all_data.json NOT found")
        
        # Check commit/all folder
        commit_all_path = os.path.join(commit_path, 'all')
        if os.path.exists(commit_all_path):
            commit_files = [f for f in os.listdir(commit_all_path) if f.endswith('.json')]
            print(f"  📊 Individual commit files: {len(commit_files)}")
            print(f"  📋 Sample commit files: {commit_files[:3]}")
        else:
            print(f"  ❌ commit/all/ folder NOT found")

def debug_data_loader(repo_name):
    """
    Debug the DataLoader to see what it's actually loading.
    """
    print(f"\n{'='*60}")
    print(f"DEBUGGING DATA LOADER: {repo_name}")
    print(f"{'='*60}")
    
    from utils.data_loader import DataLoader
    
    repo_path = os.path.join(DATA_BASE_DIR, repo_name)
    loader = DataLoader(repo_path)
    
    # Test loading pull requests
    print("\n1. TESTING PULL REQUEST LOADING:")
    print("-" * 40)
    
    try:
        pulls = loader.read_list_raw_data_from_json_files('pull')
        print(f"  ✅ Loaded {len(pulls)} pull requests")
        
        if pulls:
            print(f"  📋 Sample PR keys: {list(pulls[0].keys()) if isinstance(pulls[0], dict) else 'Not a dict'}")
    except Exception as e:
        print(f"  ❌ Error loading pull requests: {e}")
    
    # Test loading commits
    print("\n2. TESTING COMMIT LOADING:")
    print("-" * 40)
    
    try:
        commits = loader.read_list_raw_data_from_json_files('commit')
        print(f"  ✅ Loaded {len(commits)} commits")
        
        if commits:
            print(f"  📋 Sample commit keys: {list(commits[0].keys()) if isinstance(commits[0], dict) else 'Not a dict'}")
    except Exception as e:
        print(f"  ❌ Error loading commits: {e}")
    
    # Test loading individual PR data
    if 'pulls' in locals() and pulls:
        sample_pr = pulls[0]
        pr_number = sample_pr.get('number')
        
        if pr_number:
            print(f"\n3. TESTING PR {pr_number} SUBDATA:")
            print("-" * 40)
            
            # Test files
            try:
                files = loader.read_list_raw_data_from_json_files(f'pull/{pr_number}/files')
                print(f"  ✅ PR {pr_number} files: {len(files)}")
            except Exception as e:
                print(f"  ❌ Error loading PR {pr_number} files: {e}")
            
            # Test reviews
            try:
                reviews = loader.read_list_raw_data_from_json_files(f'pull/{pr_number}/reviews')
                print(f"  ✅ PR {pr_number} reviews: {len(reviews)}")
            except Exception as e:
                print(f"  ❌ Error loading PR {pr_number} reviews: {e}")
            
            # Test comments
            try:
                comments = loader.read_list_raw_data_from_json_files(f'pull/{pr_number}/comments')
                print(f"  ✅ PR {pr_number} comments: {len(comments)}")
            except Exception as e:
                print(f"  ❌ Error loading PR {pr_number} comments: {e}")

def debug_data_converter(repo_name):
    """
    Debug the DataConverter to see what it's producing.
    """
    print(f"\n{'='*60}")
    print(f"DEBUGGING DATA CONVERTER: {repo_name}")
    print(f"{'='*60}")
    
    try:
        from utils.data_converter import DataConverter
        
        repo_path = os.path.join(DATA_BASE_DIR, repo_name)
        converter = DataConverter(repo_path)
        
        print("Running data conversion...")
        converted_data = converter.load_and_convert()
        
        print(f"\n📊 CONVERSION RESULTS:")
        print("-" * 30)
        
        for key, value in converted_data.items():
            print(f"  {key}: {len(value)} items")
        
        # Check for empty critical components
        critical_empty = []
        for key in ['pull_requests', 'developers', 'files']:
            if not converted_data.get(key, []):
                critical_empty.append(key)
        
        if critical_empty:
            print(f"\n⚠️  CRITICAL EMPTY COMPONENTS: {critical_empty}")
        
        # Sample some data
        if converted_data.get('pull_requests'):
            pr = converted_data['pull_requests'][0]
            print(f"\n📋 SAMPLE PULL REQUEST:")
            print(f"  Number: {pr.number}")
            print(f"  Developer: {pr.developer_username}")
            print(f"  Files: {len(pr.file_paths)}")
            print(f"  Date: {pr.date}")
        
        if converted_data.get('reviews'):
            review = converted_data['reviews'][0]
            print(f"\n📋 SAMPLE REVIEW:")
            print(f"  ID: {review.id}")
            print(f"  Reviewer: {review.reviewer_username}")
            print(f"  PR Number: {review.pull_number}")
            print(f"  Date: {review.date}")
        
        return converted_data
        
    except Exception as e:
        print(f"❌ Error in data conversion: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def debug_manager_creation(repo_name):
    """
    Debug the Manager creation process.
    """
    print(f"\n{'='*60}")
    print(f"DEBUGGING MANAGER CREATION: {repo_name}")
    print(f"{'='*60}")
    
    try:
        factory = ManagerFactory(DATA_BASE_DIR, repo_name, from_cache=False)  # Force no cache
        manager = factory.get_manager()
        
        print(f"\n📊 MANAGER CONTENTS:")
        print("-" * 30)
        print(f"  Pull Requests: {len(manager.pull_requests)}")
        print(f"  Reviews: {len(manager.reviews)}")
        print(f"  Comments: {len(manager.comments)}")
        print(f"  Developers: {len(manager.developers)}")
        print(f"  Files: {len(manager.files)}")
        print(f"  Commits: {len(manager.commits)}")
        print(f"  Contributions: {len(manager.contributions)}")
        print(f"  Review Files: {len(manager.review_files)}")
        
        # Check if lists work
        try:
            pr_list = manager.pull_requests_list
            print(f"  PR List Length: {len(pr_list)}")
        except Exception as e:
            print(f"  ❌ Error accessing PR list: {e}")
        
        return manager
        
    except Exception as e:
        print(f"❌ Error creating manager: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def run_complete_debug(repo_name):
    """
    Run all debugging functions in sequence.
    """
    print(f"🔍 COMPLETE DEBUG ANALYSIS FOR: {repo_name}")
    print("=" * 80)
    
    # Step 1: Check crawled data structure
    debug_crawled_data_structure(repo_name)
    
    # Step 2: Test data loader
    debug_data_loader(repo_name)
    
    # Step 3: Test data converter
    converted_data = debug_data_converter(repo_name)
    
    # Step 4: Test manager creation
    manager = debug_manager_creation(repo_name)
    
    # Step 5: Summary
    print(f"\n{'='*60}")
    print("DEBUG SUMMARY")
    print(f"{'='*60}")
    
    if converted_data and manager:
        print("✅ Data pipeline appears to be working")
        
        # If manager has data but algorithms return empty, the issue is in algorithm logic
        if len(manager.pull_requests) > 0:
            print("✅ Manager has pull requests")
            print("🔍 Issue likely in algorithm simulation logic")
        else:
            print("❌ Manager has no pull requests - data conversion issue")
    else:
        print("❌ Data pipeline has fundamental issues")
    
    return manager

# Add this function to your interactive_manager.py
def debug_mode():
    """
    Interactive debug mode for diagnosing data issues.
    """
    print("\n🔍 DEBUG MODE")
    print("-" * 20)
    
    # Discover repositories
    repositories = []
    if DATA_BASE_DIR and os.path.exists(DATA_BASE_DIR):
        for item in os.listdir(DATA_BASE_DIR):
            item_path = os.path.join(DATA_BASE_DIR, item)
            if os.path.isdir(item_path):
                if (os.path.exists(os.path.join(item_path, 'pull')) and 
                    os.path.exists(os.path.join(item_path, 'commit'))):
                    repositories.append(item)
    
    if not repositories:
        print("No repositories found for debugging.")
        return
    
    print("Available repositories:")
    for i, repo in enumerate(repositories, 1):
        print(f"{i}. {repo}")
    
    try:
        choice = int(input(f"\nSelect repository to debug (1-{len(repositories)}): "))
        if 1 <= choice <= len(repositories):
            selected_repo = repositories[choice - 1]
            return run_complete_debug(selected_repo)
        else:
            print("Invalid choice.")
            return None
    except ValueError:
        print("Please enter a valid number.")
        return None

if __name__ == "__main__":
    debug_mode()