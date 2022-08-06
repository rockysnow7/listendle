from dataclasses import dataclass


@dataclass
class Song:
    name: str
    artist: str
    id: str
    date: str | None

    def __str__(self) -> str:
        return f"{self.name} – {self.artist}"


class HistoryEntry:
    ...

class Skip(HistoryEntry):
    ...

@dataclass
class Guess(HistoryEntry):
    name: str
    artist: str

class Blank(HistoryEntry):
    ...
