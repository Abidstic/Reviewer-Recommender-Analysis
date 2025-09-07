from dataclasses import dataclass


@dataclass
class Developer:
    username: str

    def __hash__(self):
        return hash(self.username)
