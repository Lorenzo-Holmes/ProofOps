from __future__ import annotations

import json
from pathlib import Path
from threading import RLock

from .models import Incident


class IncidentStore:
    def save(self, incident: Incident) -> None:
        raise NotImplementedError

    def get(self, incident_id: str) -> Incident | None:
        raise NotImplementedError

    def list(self) -> list[Incident]:
        raise NotImplementedError


class MemoryIncidentStore(IncidentStore):
    def __init__(self) -> None:
        self._items: dict[str, Incident] = {}
        self._lock = RLock()

    def save(self, incident: Incident) -> None:
        with self._lock:
            self._items[incident.id] = Incident.from_dict(incident.to_dict())

    def get(self, incident_id: str) -> Incident | None:
        with self._lock:
            item = self._items.get(incident_id)
            return Incident.from_dict(item.to_dict()) if item else None

    def list(self) -> list[Incident]:
        with self._lock:
            items = [Incident.from_dict(item.to_dict()) for item in self._items.values()]
        return sorted(items, key=lambda item: item.created_at, reverse=True)


class JsonIncidentStore(IncidentStore):
    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def _path(self, incident_id: str) -> Path:
        safe_id = "".join(char for char in incident_id if char.isalnum() or char in "-_")
        return self.directory / f"{safe_id}.json"

    def save(self, incident: Incident) -> None:
        path = self._path(incident.id)
        temporary = path.with_suffix(".json.tmp")
        payload = json.dumps(incident.to_dict(), ensure_ascii=False, indent=2)
        with self._lock:
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(path)

    def get(self, incident_id: str) -> Incident | None:
        path = self._path(incident_id)
        with self._lock:
            if not path.exists():
                return None
            return Incident.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self) -> list[Incident]:
        with self._lock:
            items = [
                Incident.from_dict(json.loads(path.read_text(encoding="utf-8")))
                for path in self.directory.glob("*.json")
            ]
        return sorted(items, key=lambda item: item.created_at, reverse=True)

