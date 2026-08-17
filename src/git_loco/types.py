from dataclasses import dataclass


@dataclass
class Coordinates:
    latitude: float | None
    longitude: float | None
    accuracy: float | None
