from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.dataset_service import dataset_service


@dataclass
class DatasetSession:
    dataset_id: str
    filename: str
    dataframe: pd.DataFrame
    operations: list[str] = field(default_factory=list)


class DatasetRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, DatasetSession] = {}

    def get(self, dataset_id: str) -> DatasetSession:
        if dataset_id in self._sessions:
            return self._sessions[dataset_id]

        source = self._resolve_dataset_path(dataset_id)
        dataframe = dataset_service.load_dataframe(source)
        session = DatasetSession(dataset_id=dataset_id, filename=source.name, dataframe=dataframe)
        self._sessions[dataset_id] = session
        return session

    def update(self, dataset_id: str, dataframe: pd.DataFrame, operation: str) -> DatasetSession:
        session = self.get(dataset_id)
        session.dataframe = dataframe.copy()
        session.operations.append(operation)
        self._persist_working_copy(session)
        return session

    def _resolve_dataset_path(self, dataset_id: str) -> Path:
        working_copy = settings.upload_path / f"{dataset_id}.working.csv"
        if working_copy.exists():
            return working_copy

        matches = [
            path for path in settings.upload_path.iterdir()
            if path.is_file() and path.stem == dataset_id and path.suffix.lower() in {".csv", ".xls", ".xlsx"}
        ]
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found. Upload a dataset before using the agent.",
            )
        return matches[0]

    def _persist_working_copy(self, session: DatasetSession) -> None:
        destination = settings.upload_path / f"{session.dataset_id}.working.csv"
        session.dataframe.to_csv(destination, index=False)


dataset_repository = DatasetRepository()
