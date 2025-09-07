from dataclasses import dataclass


@dataclass
class Commit:
    id: str
    username: str
    date: str
