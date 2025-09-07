from dataclasses import dataclass
from typing import List


# todo: complete
@dataclass
class PullRequest:
    number: int
    file_paths: List[str]
    date: str
    developer_username: str
