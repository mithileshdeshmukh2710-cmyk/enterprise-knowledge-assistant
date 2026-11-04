import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


class DocumentMetadataStore:

    def __init__(self):
        default_path = (
            Path(__file__).resolve().parents[2] / "data" / "document_metadata.json"
        )
        self.path = Path(
            os.getenv("DOCUMENT_METADATA_PATH", str(default_path))
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

        if not self.path.exists():
            self._write({})

    def _read(self):
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if not isinstance(data, dict):
                    raise ValueError("Metadata file must contain a JSON object.")
                return data
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Document metadata JSON is corrupted."
            ) from error

    def _write(self, data):
        temporary_path = self.path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        os.replace(temporary_path, self.path)

    def save(self, filename, metadata):
        with self.lock:
            data = self._read()
            data[filename] = {
                **metadata,
                "filename": filename,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self._write(data)

    def get(self, filename):
        with self.lock:
            data = self._read()
            return data.get(filename)

    def get_all(self):
        with self.lock:
            return self._read()

    def delete(self, filename):
        with self.lock:
            data = self._read()
            if filename in data:
                del data[filename]
                self._write(data)

