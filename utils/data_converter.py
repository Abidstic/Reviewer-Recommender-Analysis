from models import PullRequest, Comment, Review, Commit, Developer, Contribution, File, ReviewFile
from .data_loader import DataLoader
from .logger import info_logger


class DataConverter:
    def __init__(self, folder_path):
        self._folder_path = folder_path
        self._data_loader = DataLoader(folder_path)

    def load_and_convert(self):
        all_raw_prs = self._data_loader.read_list_raw_data_from_json_files('pull')
        all_raw_commits = self._data_loader.read_list_raw_data_from_json_files('commit')

        all_converted_commits = []
        all_converted_developers = []
        all_converted_contributions = []
        all_raw_file_paths = set()

        for raw_commit in all_raw_commits:
            if raw_commit['author'] is not None:
                commit_author_username = raw_commit['author']['login']
            else:
                commit_author_username = raw_commit['commit']['author']['email']
            commit_date = raw_commit['commit']['author']['date']

            all_converted_commits.append(
                Commit(
                    id=raw_commit['sha'],
                    username=commit_author_username,
                    date=commit_date,
                )
            )

            all_converted_developers.append(
                Developer(
                    username=commit_author_username,
                )
            )

            commit_data = self._data_loader.read_raw_json_data_from_file('commit/all', raw_commit["sha"])

            for file in commit_data['files']:
                all_raw_file_paths.add(file['filename'])

                all_converted_contributions.append(
                    Contribution(
                        filename=file['filename'],
                        commit_id=raw_commit['sha'],
                        username=commit_author_username,
                        date=commit_date,
                    )
                )

        all_converted_files = [File(filepath=_) for _ in all_raw_file_paths]

        all_converted_comments = []
        all_converted_reviews = []
        all_converted_prs = []
        all_converted_review_files = []

        for raw_pr in all_raw_prs:
            raw_pr_comments = self._data_loader.read_list_raw_data_from_json_files(f'pull/{raw_pr["number"]}/comments')

            for raw_comment in raw_pr_comments:

                if raw_comment['user'] is None:
                    continue

                all_converted_comments.append(
                    Comment(
                        id=raw_comment['id'],
                        filename=raw_comment['path'],
                        reviewer_username=raw_comment['user']['login'],
                        date=raw_comment['created_at'],
                        review_id=raw_comment['pull_request_review_id'],
                    )
                )

            raw_pr_files = self._data_loader.read_list_raw_data_from_json_files(f'pull/{raw_pr["number"]}/files')

            current_pr_files = []
            for raw_pr_file in raw_pr_files:
                current_pr_files.append(
                    raw_pr_file['filename']
                )

            all_converted_prs.append(
                PullRequest(
                    number=raw_pr['number'],
                    file_paths=current_pr_files,
                    date=raw_pr['created_at'],
                    developer_username=raw_pr['user']['login'],
                )
            )

            raw_pr_reviews = self._data_loader.read_list_raw_data_from_json_files(f'pull/{raw_pr["number"]}/reviews')

            for raw_review in raw_pr_reviews:

                if raw_review['user'] is None:
                    continue

                if "commit_id" not in raw_review:
                    raw_review['commit_id'] = None

                all_converted_reviews.append(
                    Review(
                        id=raw_review['id'],
                        reviewer_username=raw_review['user']['login'],
                        commit_id=raw_review['commit_id'],
                        pull_number=raw_pr['number'],
                        date=raw_review['submitted_at'],
                    )
                )

                if raw_review['commit_id'] is None:
                    continue

                commit_data = self._data_loader.read_raw_json_data_from_file(
                    'commit/all',
                    raw_review['commit_id'],
                )

                for file in commit_data['files']:
                    all_raw_file_paths.add(file['filename'])

                    # TODO: Check review files with article
                    all_converted_review_files.append(
                        ReviewFile(
                            review_id=raw_review['id'],
                            reviewer_username=raw_review['user']['login'],
                            commit_id=raw_review['commit_id'],
                            filepath=file['filename'],
                            pull_number=raw_pr['number'],
                            date=raw_review['submitted_at'],
                        )
                    )

        info_logger.info(f'Number of commits: {len(all_converted_commits)}')
        info_logger.info(f'Number of developers: {len(all_converted_developers)}')
        info_logger.info(f'Number of contributions: {len(all_converted_contributions)}')
        info_logger.info(f'Number of files: {len(all_converted_files)}')
        info_logger.info(f'Number of comments: {len(all_converted_comments)}')
        info_logger.info(f'Number of reviews: {len(all_converted_reviews)}')
        info_logger.info(f'Number of pull requests: {len(all_converted_prs)}')
        info_logger.info(f'Number of review files: {len(all_converted_review_files)}')

        return dict(
            commits=all_converted_commits,
            developers=all_converted_developers,
            contributions=all_converted_contributions,
            files=all_converted_files,
            comments=all_converted_comments,
            reviews=all_converted_reviews,
            pull_requests=all_converted_prs,
            review_files=all_converted_review_files,
        )
