from models import Manager
from .cache import Cache
from .data_converter import DataConverter
from .logger import info_logger


class ManagerFactory:
    def __init__(self, crawled_data_folder_path, project_name, from_cache=True):
        self._crawled_data_folder_path = crawled_data_folder_path
        self._project_name = project_name
        self._from_cache = from_cache
        
        # Initialize data converter with full project path
        self._project_path = f'{crawled_data_folder_path}/{project_name}'
        self._data_converter = DataConverter(self._project_path)
        
        info_logger.info(f'ManagerFactory initialized for project: {project_name}')
        info_logger.info(f'Project data path: {self._project_path}')

    def get_manager(self):
        """
        Create and return a Manager instance with comprehensive data validation.
        """
        # Check cache first if enabled
        if self._from_cache:
            cached_manager = Cache.load(self._cache_file_name)
            if cached_manager is not None:
                info_logger.info('Manager loaded from cache')
                self._validate_cached_manager(cached_manager)
                return cached_manager

        # Validate data structure before processing
        self._validate_data_structure()

        # Create new manager and load data
        manager = Manager(self._project_name)
        info_logger.info('Creating new Manager instance')
        
        try:
            # Load and convert data
            info_logger.info('Starting data conversion process...')
            converted_data = self._data_converter.load_and_convert()
            
            # Validate converted data
            self._validate_converted_data(converted_data)
            
            # Populate manager with converted data
            self._populate_manager(manager, converted_data)
            
            # Validate final manager state
            self._validate_manager_completeness(manager)
            
            info_logger.info('Manager created successfully')
            
            # Cache the manager
            Cache.store(self._cache_file_name, manager)
            info_logger.info('Manager stored in cache')
            
            return manager
            
        except Exception as e:
            info_logger.error(f'Error creating manager: {str(e)}')
            raise RuntimeError(f'Failed to create manager for project {self._project_name}: {str(e)}')

    def _validate_data_structure(self):
        """
        Validate that the crawled data structure is compatible.
        """
        info_logger.info('Validating crawled data structure...')
        
        # Get data loader from converter to check structure
        data_loader = self._data_converter._data_loader
        
        # Run compatibility check
        is_compatible, issues = data_loader.validate_crawled_data_compatibility()
        
        if not is_compatible:
            error_msg = f'Crawled data structure validation failed for {self._project_name}. Issues: {issues}'
            info_logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Log structure report for debugging
        structure_report = data_loader.check_data_structure()
        info_logger.info(f'Data structure validation passed. Report: {structure_report}')

    def _validate_converted_data(self, converted_data):
        """
        Validate the converted data contains expected components.
        """
        info_logger.info('Validating converted data...')
        
        expected_keys = [
            'commits', 'developers', 'contributions', 'files', 
            'comments', 'reviews', 'pull_requests', 'review_files'
        ]
        
        missing_keys = [key for key in expected_keys if key not in converted_data]
        if missing_keys:
            error_msg = f'Missing expected data components: {missing_keys}'
            info_logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check for empty critical components
        critical_components = ['pull_requests', 'developers']
        for component in critical_components:
            if not converted_data[component]:
                info_logger.warning(f'Critical component {component} is empty')
        
        # Log data statistics
        data_stats = {key: len(value) for key, value in converted_data.items()}
        info_logger.info(f'Converted data statistics: {data_stats}')
        
        # Check for reasonable data relationships
        self._validate_data_relationships(converted_data)

    def _validate_data_relationships(self, converted_data):
        """
        Validate logical relationships between different data components.
        """
        info_logger.info('Validating data relationships...')
        
        pr_count = len(converted_data['pull_requests'])
        review_count = len(converted_data['reviews'])
        comment_count = len(converted_data['comments'])
        
        # Check if we have any reviews for PRs
        if pr_count > 0 and review_count == 0:
            info_logger.warning('No reviews found despite having pull requests')
        
        # Check review-to-PR ratio
        if pr_count > 0:
            review_ratio = review_count / pr_count
            info_logger.info(f'Review coverage ratio: {review_ratio:.2f} reviews per PR')
            
            if review_ratio < 0.1:
                info_logger.warning(f'Low review coverage: {review_ratio:.2f} reviews per PR')

    def _populate_manager(self, manager, converted_data):
        """
        Populate the manager with converted data and track progress.
        """
        info_logger.info('Populating manager with converted data...')
        
        # Track population progress
        population_stats = {}
        
        # Add pull requests
        for pr in converted_data['pull_requests']:
            manager.add_pull_request(pr)
        population_stats['pull_requests'] = len(converted_data['pull_requests'])
        
        # Add comments
        for comment in converted_data['comments']:
            manager.add_comment(comment)
        population_stats['comments'] = len(converted_data['comments'])
        
        # Add reviews
        for review in converted_data['reviews']:
            manager.add_review(review)
        population_stats['reviews'] = len(converted_data['reviews'])
        
        # Add commits
        for commit in converted_data['commits']:
            manager.add_commit(commit)
        population_stats['commits'] = len(converted_data['commits'])
        
        # Add developers
        for developer in converted_data['developers']:
            manager.add_developer(developer)
        population_stats['developers'] = len(converted_data['developers'])
        
        # Add contributions
        for contribution in converted_data['contributions']:
            manager.add_contribution(contribution)
        population_stats['contributions'] = len(converted_data['contributions'])
        
        # Add files
        for file in converted_data['files']:
            manager.add_file(file)
        population_stats['files'] = len(converted_data['files'])
        
        # Add review files
        for review_file in converted_data['review_files']:
            manager.add_review_file(review_file)
        population_stats['review_files'] = len(converted_data['review_files'])
        
        info_logger.info(f'Manager population completed: {population_stats}')

    def _validate_manager_completeness(self, manager):
        """
        Validate that the manager was populated correctly.
        """
        info_logger.info('Validating manager completeness...')
        
        # Check manager dictionaries are populated
        manager_stats = {
            'files': len(manager.files),
            'developers': len(manager.developers),
            'pull_requests': len(manager.pull_requests),
            'reviews': len(manager.reviews),
            'commits': len(manager.commits),
            'comments_files': len(manager.comments),
            'contributions_files': len(manager.contributions),
            'review_files': len(manager.review_files)
        }
        
        info_logger.info(f'Final manager statistics: {manager_stats}')
        
        # Check for critical empty collections
        if manager_stats['pull_requests'] == 0:
            raise ValueError('Manager has no pull requests - this indicates a data loading problem')
        
        if manager_stats['developers'] == 0:
            raise ValueError('Manager has no developers - this indicates a data loading problem')
        
        # Validate cached properties work
        try:
            _ = len(manager.pull_requests_list)
            _ = len(manager.developers_list)
            info_logger.info('Manager cached properties validation passed')
        except Exception as e:
            raise ValueError(f'Manager cached properties validation failed: {str(e)}')

    def _validate_cached_manager(self, manager):
        """
        Validate a manager loaded from cache.
        """
        info_logger.info('Validating cached manager...')
        
        if not hasattr(manager, 'project') or manager.project != self._project_name:
            info_logger.warning('Cached manager project mismatch')
            
        # Quick validation of cached manager
        try:
            pr_count = len(manager.pull_requests_list)
            dev_count = len(manager.developers_list)
            info_logger.info(f'Cached manager contains {pr_count} PRs and {dev_count} developers')
        except Exception as e:
            info_logger.error(f'Cached manager validation failed: {str(e)}')
            raise ValueError('Cached manager is corrupted')

    @property
    def _cache_file_name(self):
        return f'{self._project_name}.data-manager'

    def get_data_summary(self):
        """
        Get a summary of the data structure without creating a full manager.
        Useful for debugging data issues.
        """
        info_logger.info('Generating data summary...')
        
        try:
            # Check data structure
            data_loader = self._data_converter._data_loader
            is_compatible, issues = data_loader.validate_crawled_data_compatibility()
            structure_report = data_loader.check_data_structure()
            
            summary = {
                'project_name': self._project_name,
                'project_path': self._project_path,
                'structure_compatible': is_compatible,
                'structure_issues': issues,
                'structure_report': structure_report
            }
            
            if is_compatible:
                # Try to get basic data counts
                try:
                    converted_data = self._data_converter.load_and_convert()
                    summary['data_counts'] = {key: len(value) for key, value in converted_data.items()}
                except Exception as e:
                    summary['data_conversion_error'] = str(e)
            
            return summary
            
        except Exception as e:
            return {
                'project_name': self._project_name,
                'error': str(e)
            }