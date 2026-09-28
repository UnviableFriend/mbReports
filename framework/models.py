from dataclasses import dataclass, field
from typing import Any


@dataclass
class Column:
    key: str
    title: str
    sort: bool = True


@dataclass
class Stat:
    label: str
    value: Any


@dataclass
class ReportResult:
    report_id: str
    title: str
    description: str = ""
    columns: list[Column] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    stats: list[Stat] = field(default_factory=list)
    filename: str = ""
    category: str = "Other"
