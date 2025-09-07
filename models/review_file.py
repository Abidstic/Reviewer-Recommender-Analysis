from dataclasses import dataclass


@dataclass
class ReviewFile:
    review_id: int
    reviewer_username: str
    commit_id: str
    filepath: str
    pull_number: int
    date: str
