from __future__ import annotations

import math
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.schemas import ChartRecommendation, ColumnProfile, DatasetProfile


ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}
MAX_CATEGORY_COLUMNS = 6
MAX_NUMERIC_COLUMNS = 8


class DatasetService:
    async def save_upload(self, file: UploadFile) -> Path:
        extension = Path(file.filename or "").suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV, XLS, and XLSX files are supported.",
            )

        dataset_id = uuid.uuid4().hex
        safe_name = f"{dataset_id}{extension}"
        destination = settings.upload_path / safe_name

        total_bytes = 0
        with destination.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_bytes:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds {settings.max_upload_mb} MB upload limit.",
                    )
                buffer.write(chunk)

        return destination

    def load_dataframe(self, file_path: Path) -> pd.DataFrame:
        try:
            if file_path.suffix.lower() == ".csv":
                return pd.read_csv(file_path)
            return pd.read_excel(file_path)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not parse dataset: {exc}",
            ) from exc

    def build_profile(self, dataframe: pd.DataFrame, dataset_id: str, filename: str) -> DatasetProfile:
        if dataframe.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The uploaded dataset is empty.",
            )

        df = dataframe.copy()
        date_columns = self._detect_date_columns(df)
        numeric_columns = [
            column for column in df.select_dtypes(include=[np.number]).columns.tolist()
            if column not in date_columns
        ]
        boolean_columns = df.select_dtypes(include=["bool"]).columns.tolist()
        categorical_columns = self._detect_categorical_columns(df, numeric_columns, date_columns, boolean_columns)

        column_profiles = [
            self._profile_column(df, column, numeric_columns, categorical_columns, date_columns, boolean_columns)
            for column in df.columns
        ]

        return DatasetProfile(
            dataset_id=dataset_id,
            filename=filename,
            rows=int(df.shape[0]),
            columns=int(df.shape[1]),
            duplicate_rows=int(df.duplicated().sum()),
            total_missing_values=int(df.isna().sum().sum()),
            memory_usage_mb=round(float(df.memory_usage(deep=True).sum() / (1024 * 1024)), 3),
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            date_columns=date_columns,
            boolean_columns=boolean_columns,
            column_profiles=column_profiles,
            statistical_overview=self._statistical_overview(df, numeric_columns),
            top_categories=self._top_categories(df, categorical_columns),
            date_ranges=self._date_ranges(df, date_columns),
            correlation_matrix=self._correlation_matrix(df, numeric_columns),
            kpis=self._kpis(df, numeric_columns),
            chart_recommendations=self._chart_recommendations(numeric_columns, categorical_columns, date_columns),
            preview_rows=self._records(df.head(25)),
        )

    def _detect_date_columns(self, df: pd.DataFrame) -> list[str]:
        date_columns: list[str] = []
        for column in df.columns:
            series = df[column].dropna()
            if series.empty:
                continue
            if pd.api.types.is_datetime64_any_dtype(series):
                date_columns.append(column)
                continue
            if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
                sample = series.astype(str).head(100)
                parsed = pd.to_datetime(sample, errors="coerce", format="mixed", utc=False)
                if parsed.notna().mean() >= 0.8:
                    date_columns.append(column)
        return date_columns

    def _detect_categorical_columns(
        self,
        df: pd.DataFrame,
        numeric_columns: list[str],
        date_columns: list[str],
        boolean_columns: list[str],
    ) -> list[str]:
        categorical: list[str] = []
        excluded = set(numeric_columns + date_columns + boolean_columns)
        for column in df.columns:
            if column in excluded:
                continue
            unique_ratio = df[column].nunique(dropna=True) / max(len(df), 1)
            if unique_ratio <= 0.5 or df[column].nunique(dropna=True) <= 30:
                categorical.append(column)
        return categorical

    def _profile_column(
        self,
        df: pd.DataFrame,
        column: str,
        numeric_columns: list[str],
        categorical_columns: list[str],
        date_columns: list[str],
        boolean_columns: list[str],
    ) -> ColumnProfile:
        series = df[column]
        kind = "unknown"
        stats: dict[str, Any] = {}

        if column in numeric_columns:
            kind = "numeric"
            stats = self._numeric_stats(series)
        elif column in date_columns:
            kind = "datetime"
            parsed = pd.to_datetime(series, errors="coerce", format="mixed")
            stats = {
                "min": self._clean_value(parsed.min()),
                "max": self._clean_value(parsed.max()),
                "valid_dates": int(parsed.notna().sum()),
            }
        elif column in boolean_columns:
            kind = "boolean"
            stats = series.value_counts(dropna=False).to_dict()
        elif column in categorical_columns:
            kind = "categorical"
            stats = {"top_values": self._value_counts(series, limit=5)}
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            kind = "text"

        return ColumnProfile(
            name=column,
            kind=kind,
            dtype=str(series.dtype),
            missing_count=int(series.isna().sum()),
            missing_percent=round(float(series.isna().mean() * 100), 2),
            unique_count=int(series.nunique(dropna=True)),
            sample_values=[self._clean_value(value) for value in series.dropna().head(5).tolist()],
            stats=self._clean_value(stats),
        )

    def _numeric_stats(self, series: pd.Series) -> dict[str, Any]:
        described = series.describe(percentiles=[0.25, 0.5, 0.75])
        return {
            "mean": self._clean_value(described.get("mean")),
            "median": self._clean_value(series.median()),
            "std": self._clean_value(described.get("std")),
            "min": self._clean_value(described.get("min")),
            "max": self._clean_value(described.get("max")),
            "q1": self._clean_value(described.get("25%")),
            "q3": self._clean_value(described.get("75%")),
        }

    def _statistical_overview(self, df: pd.DataFrame, numeric_columns: list[str]) -> dict[str, dict[str, Any]]:
        overview: dict[str, dict[str, Any]] = {}
        for column in numeric_columns[:MAX_NUMERIC_COLUMNS]:
            overview[column] = self._numeric_stats(df[column])
        return overview

    def _top_categories(self, df: pd.DataFrame, categorical_columns: list[str]) -> dict[str, list[dict[str, Any]]]:
        return {
            column: self._value_counts(df[column], limit=8)
            for column in categorical_columns[:MAX_CATEGORY_COLUMNS]
        }

    def _value_counts(self, series: pd.Series, limit: int) -> list[dict[str, Any]]:
        counts = series.value_counts(dropna=True).head(limit)
        return [
            {"label": self._clean_value(index), "count": int(value)}
            for index, value in counts.items()
        ]

    def _date_ranges(self, df: pd.DataFrame, date_columns: list[str]) -> dict[str, dict[str, str | None]]:
        ranges: dict[str, dict[str, str | None]] = {}
        for column in date_columns:
            parsed = pd.to_datetime(df[column], errors="coerce", format="mixed")
            ranges[column] = {
                "start": self._clean_value(parsed.min()),
                "end": self._clean_value(parsed.max()),
            }
        return ranges

    def _correlation_matrix(self, df: pd.DataFrame, numeric_columns: list[str]) -> dict[str, dict[str, float]]:
        if len(numeric_columns) < 2:
            return {}
        corr = df[numeric_columns[:MAX_NUMERIC_COLUMNS]].corr(numeric_only=True).round(3)
        return self._clean_value(corr.to_dict())

    def _kpis(self, df: pd.DataFrame, numeric_columns: list[str]) -> list[dict[str, Any]]:
        kpis: list[dict[str, Any]] = [
            {"label": "Total Rows", "value": int(df.shape[0]), "type": "count"},
            {"label": "Total Columns", "value": int(df.shape[1]), "type": "count"},
            {"label": "Missing Values", "value": int(df.isna().sum().sum()), "type": "quality"},
            {"label": "Duplicate Rows", "value": int(df.duplicated().sum()), "type": "quality"},
        ]
        for column in numeric_columns[:4]:
            kpis.append(
                {
                    "label": f"Average {column}",
                    "value": self._clean_value(df[column].mean()),
                    "type": "metric",
                }
            )
        return kpis

    def _chart_recommendations(
        self,
        numeric_columns: list[str],
        categorical_columns: list[str],
        date_columns: list[str],
    ) -> list[ChartRecommendation]:
        recommendations: list[ChartRecommendation] = []
        if categorical_columns and numeric_columns:
            recommendations.append(
                ChartRecommendation(
                    chart_type="bar",
                    title=f"{numeric_columns[0]} by {categorical_columns[0]}",
                    x=categorical_columns[0],
                    y=numeric_columns[0],
                    reason="Compare a key numeric measure across top categories.",
                )
            )
            recommendations.append(
                ChartRecommendation(
                    chart_type="pie",
                    title=f"Distribution of {categorical_columns[0]}",
                    x=categorical_columns[0],
                    reason="Show category concentration and share.",
                )
            )
        if date_columns and numeric_columns:
            recommendations.append(
                ChartRecommendation(
                    chart_type="line",
                    title=f"{numeric_columns[0]} trend over {date_columns[0]}",
                    x=date_columns[0],
                    y=numeric_columns[0],
                    reason="Track the most likely time-series signal.",
                )
            )
        if len(numeric_columns) >= 2:
            recommendations.extend(
                [
                    ChartRecommendation(
                        chart_type="scatter",
                        title=f"{numeric_columns[0]} vs {numeric_columns[1]}",
                        x=numeric_columns[0],
                        y=numeric_columns[1],
                        reason="Inspect relationships and potential outliers.",
                    ),
                    ChartRecommendation(
                        chart_type="heatmap",
                        title="Numeric correlation heatmap",
                        reason="Reveal relationships across numeric metrics.",
                    ),
                ]
            )
        if numeric_columns:
            recommendations.append(
                ChartRecommendation(
                    chart_type="histogram",
                    title=f"Distribution of {numeric_columns[0]}",
                    x=numeric_columns[0],
                    reason="Understand spread, skew, and outliers.",
                )
            )
        return recommendations[:6]

    def _records(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        return self._clean_value(df.replace({np.nan: None}).to_dict(orient="records"))

    def _clean_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(self._clean_value(key)): self._clean_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._clean_value(item) for item in value]
        if isinstance(value, tuple):
            return [self._clean_value(item) for item in value]
        if isinstance(value, (pd.Timestamp, np.datetime64)):
            if pd.isna(value):
                return None
            return pd.Timestamp(value).isoformat()
        if isinstance(value, np.generic):
            return self._clean_value(value.item())
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value


dataset_service = DatasetService()
