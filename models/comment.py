from dataclasses import dataclass


@dataclass
class Comment:
    id: str
    filename: str
    reviewer_username: str
    date: str
    review_id: int
