import os
import json
from glob import glob
from utils.logger import info_logger


class DataLoader:
    def __init__(self, folder_path):
        self._folder_path = folder_path
        info_logger.info(f"DataLoader initialized with path: {folder_path}")

    def read_list_raw_data_from_json_files(self, folder_name):
        """
        Read JSON data from folder. Handles both new crawled data format (single all_data.json)
        and legacy format (multiple .json files).
        """
        final_folder = os.path.join(self._folder_path, folder_name)
        
        if not os.path.exists(final_folder):
            info_logger.warning(f"Folder does not exist: {final_folder}")
            return []
        
        # Check for new crawled data format first (single all_data.json)
        all_data_file = os.path.join(final_folder, 'all_data.json')
        if os.path.exists(all_data_file):
            info_logger.info(f"Loading from new format: {all_data_file}")
            try:
                with open(all_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure we return a list (data could be empty list or None)
                    if data is None:
                        info_logger.warning(f"all_data.json contains null data: {all_data_file}")
                        return []
                    elif isinstance(data, list):
                        info_logger.info(f"Loaded {len(data)} items from {all_data_file}")
                        return data
                    else:
                        info_logger.error(f"Unexpected data type in {all_data_file}: {type(data)}")
                        return []
            except json.JSONDecodeError as e:
                info_logger.error(f"JSON decode error in {all_data_file}: {e}")
                return []
            except Exception as e:
                info_logger.error(f"Error reading {all_data_file}: {e}")
                return []
        
        # Fallback to legacy format (multiple .json files)
        info_logger.info(f"all_data.json not found, trying legacy format in: {final_folder}")
        json_files = glob(os.path.join(final_folder, '*.json'))
        
        if not json_files:
            info_logger.warning(f"No JSON files found in: {final_folder}")
            return []
        
        all_data = []
        for file_name in json_files:
            info_logger.info(f"Loading legacy file: {file_name}")
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        all_data.extend(file_data)
                    else:
                        all_data.append(file_data)
            except json.JSONDecodeError as e:
                info_logger.error(f"JSON decode error in {file_name}: {e}")
                continue
            except Exception as e:
                info_logger.error(f"Error reading {file_name}: {e}")
                continue
        
        info_logger.info(f"Loaded {len(all_data)} total items from {len(json_files)} legacy files")
        return all_data

    def read_raw_json_data_from_file(self, folder_name, file_name):
        """
        Read a single JSON file. This method is used for individual commit details.
        Path format: folder_name/file_name.json
        """
        final_path = os.path.join(self._folder_path, f'{folder_name}/{file_name}.json')
        
        if not os.path.exists(final_path):
            info_logger.warning(f"File does not exist: {final_path}")
            return {}
        
        try:
            with open(final_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                info_logger.debug(f"Loaded individual file: {final_path}")
                return data if data is not None else {}
        except json.JSONDecodeError as e:
            info_logger.error(f"JSON decode error in {final_path}: {e}")
            return {}
        except Exception as e:
            info_logger.error(f"Error reading {final_path}: {e}")
            return {}

    def check_data_structure(self):
        """
        Debug method to check and report on the data structure found in the folder.
        This helps identify any structural issues.
        """
        info_logger.info(f"Checking data structure in: {self._folder_path}")
        
        structure_report = {
            'base_path_exists': os.path.exists(self._folder_path),
            'folders_found': [],
            'pull_structure': {},
            'commit_structure': {}
        }
        
        if not structure_report['base_path_exists']:
            info_logger.error(f"Base path does not exist: {self._folder_path}")
            return structure_report
        
        # Check main folders
        for item in os.listdir(self._folder_path):
            item_path = os.path.join(self._folder_path, item)
            if os.path.isdir(item_path):
                structure_report['folders_found'].append(item)
        
        # Check pull structure
        pull_path = os.path.join(self._folder_path, 'pull')
        if os.path.exists(pull_path):
            structure_report['pull_structure']['all_data_exists'] = os.path.exists(
                os.path.join(pull_path, 'all_data.json')
            )
            structure_report['pull_structure']['pr_folders'] = [
                item for item in os.listdir(pull_path)
                if os.path.isdir(os.path.join(pull_path, item)) and item.isdigit()
            ][:5]  # Show first 5 PR folders
        
        # Check commit structure
        commit_path = os.path.join(self._folder_path, 'commit')
        if os.path.exists(commit_path):
            structure_report['commit_structure']['all_data_exists'] = os.path.exists(
                os.path.join(commit_path, 'all_data.json')
            )
            commit_all_path = os.path.join(commit_path, 'all')
            if os.path.exists(commit_all_path):
                commit_files = [f for f in os.listdir(commit_all_path) if f.endswith('.json')]
                structure_report['commit_structure']['individual_commits_count'] = len(commit_files)
                structure_report['commit_structure']['sample_commit_files'] = commit_files[:3]
        
        info_logger.info(f"Data structure report: {structure_report}")
        return structure_report

    def validate_crawled_data_compatibility(self):
        """
        Validate that the crawled data structure matches expected format.
        Returns tuple (is_compatible, issues_found)
        """
        issues = []
        
        # Check base structure
        if not os.path.exists(self._folder_path):
            issues.append(f"Base folder does not exist: {self._folder_path}")
            return False, issues
        
        # Check pull folder
        pull_path = os.path.join(self._folder_path, 'pull')
        if not os.path.exists(pull_path):
            issues.append("'pull' folder not found")
        else:
            pull_all_data = os.path.join(pull_path, 'all_data.json')
            if not os.path.exists(pull_all_data):
                issues.append("'pull/all_data.json' not found")
        
        # Check commit folder
        commit_path = os.path.join(self._folder_path, 'commit')
        if not os.path.exists(commit_path):
            issues.append("'commit' folder not found")
        else:
            commit_all_data = os.path.join(commit_path, 'all_data.json')
            if not os.path.exists(commit_all_data):
                issues.append("'commit/all_data.json' not found")
            
            commit_all_path = os.path.join(commit_path, 'all')
            if not os.path.exists(commit_all_path):
                issues.append("'commit/all' folder not found")
        
        is_compatible = len(issues) == 0
        
        if is_compatible:
            info_logger.info("Crawled data structure validation passed")
        else:
            info_logger.warning(f"Crawled data structure issues found: {issues}")
        
        return is_compatible, issues