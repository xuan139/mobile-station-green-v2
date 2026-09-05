from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ServiceStatus:
    service: str
    status: str
    version: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

