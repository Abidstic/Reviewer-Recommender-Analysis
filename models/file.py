from dataclasses import dataclass


@dataclass
class File:
    filepath: str

    def __hash__(self):
        return hash(self.filepath)
