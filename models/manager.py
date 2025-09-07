from functools import cached_property
from typing import Dict, List

from .commit import Commit
from .pull_request import PullRequest
from .comment import Comment
from .file import File
from .developer import Developer
from .contribution import Contribution
from .review import Review
from .review_file import ReviewFile


class Manager:
    files: Dict[str, File]
    developers: Dict[str, Developer]
    contributions: Dict[str, List[Contribution]]
    comments: Dict[str, List[Comment]]
    pull_requests: Dict[int, PullRequest]
    reviews: Dict[int, Review]
    review_files: List[ReviewFile]
    commits: Dict[str, Commit]

    def __init__(self, project: str):
        self.project = project
        self.files = {}
        self.developers = {}
        self.contributions = {}
        self.comments = {}
        self.pull_requests = {}
        self.commits = {}
        self.reviews = {}
        self.review_files = []

    @cached_property
    def developers_list(self):
        return list(self.developers.values())

    @cached_property
    def files_list(self):
        return list(self.files.values())

    @cached_property
    def comments_list(self):
        return list(comment for file_comments in self.comments.values() for comment in file_comments)

    @cached_property
    def pull_requests_list(self):
        return list(self.pull_requests.values())

    @cached_property
    def reviews_list(self):
        return list(self.reviews.values())

    @cached_property
    def commits_list(self):
        return list(self.commits.values())

    @cached_property
    def review_files_list(self):
        return list(self.review_files)

    def add_comment(self, comment: Comment):
        k = comment.filename
        if k not in self.comments:
            self.comments[k] = []
        self.comments[k].append(comment)

    def add_file(self, file: File):
        self.files[file.filepath] = file

    def add_developer(self, developer: Developer):
        self.developers[developer.username] = developer

    def add_contribution(self, contribution: Contribution):
        k = contribution.filename
        if k not in self.contributions:
            self.contributions[k] = []
        self.contributions[k].append(contribution)

    def add_pull_request(self, pr: PullRequest):
        self.pull_requests[pr.number] = pr

    def add_commit(self, commit: Commit):
        self.commits[commit.id] = commit

    def add_review(self, review: Review):
        self.reviews[review.id] = review

    def add_review_file(self, review_file: ReviewFile):
        self.review_files.append(review_file)
