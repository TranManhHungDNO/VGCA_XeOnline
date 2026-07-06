from dataclasses import dataclass


@dataclass
class SignPlacement:
    page_index: int
    x: float
    y: float
    w: float
    h: float
