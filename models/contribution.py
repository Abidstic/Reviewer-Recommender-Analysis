from dataclasses import dataclass


@dataclass
class Contribution:
    filename: str
    username: str
    commit_id: str
    date: str
