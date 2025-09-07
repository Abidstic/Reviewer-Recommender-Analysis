from dataclasses import dataclass


@dataclass
class Review:
    id: int
    reviewer_username: str
    commit_id: str
    pull_number: int
    date: str
