from __future__ import annotations

import re
from difflib import get_close_matches
from typing import Any

import pandas as pd

from app.models.schemas import AgentIntent, DataAction


class CommandClassifier:
    def classify(self, message: str) -> AgentIntent:
        text = message.lower()
        if self._contains(text, ["remove null", "drop null", "missing", "duplicate", "normalize", "outlier", "clean"]):
            return "cleaning"
        if self._contains(text, ["add ", "rename", "filter", "sort", "convert", "delete column", "drop column"]):
            return "modification"
        if self._contains(text, ["chart", "graph", "plot", "bar", "pie", "line", "heatmap", "scatter"]):
            return "visualization"
        if self._contains(text, ["insight", "recommend", "explain", "why", "summary", "pattern"]):
            return "insights"
        if self._contains(text, ["forecast", "predict", "projection"]):
            return "forecasting"
        if self._contains(text, ["top", "average", "mean", "highest", "lowest", "compare", "correlation", "total"]):
            return "analytics"
        return "unknown"

    def _contains(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)


class RuleBasedPlanner:
    def plan(self, message: str, dataframe: pd.DataFrame, intent: AgentIntent) -> list[DataAction]:
        text = message.lower()
        columns = list(dataframe.columns)

        if intent == "cleaning":
            return self._cleaning_plan(text, columns, dataframe)
        if intent == "modification":
            return self._modification_plan(text, columns)
        if intent == "visualization":
            return [self._chart_action(text, columns, dataframe)]
        if intent == "insights":
            return [DataAction(action="generate_insights")]
        if intent == "analytics":
            return self._analytics_plan(text, columns, dataframe)
        return [DataAction(action="generate_insights")]

    def _cleaning_plan(self, text: str, columns: list[str], dataframe: pd.DataFrame) -> list[DataAction]:
        if "duplicate" in text:
            return [DataAction(action="drop_duplicates")]
        if "normalize" in text:
            column = self._find_column(text, columns) or self._first_numeric(dataframe)
            return [DataAction(action="normalize_column", column=column)]
        if "outlier" in text:
            column = self._find_column(text, columns) or self._first_numeric(dataframe)
            return [DataAction(action="remove_outliers", column=column)]
        if "mean" in text or "average" in text:
            column = self._find_column(text, columns) or self._first_numeric(dataframe)
            return [DataAction(action="fill_missing", column=column, operation="mean")]
        return [DataAction(action="drop_missing")]

    def _modification_plan(self, text: str, columns: list[str]) -> list[DataAction]:
        rename_match = re.search(r"rename\s+column\s+(.+?)\s+to\s+(.+)$", text)
        if rename_match:
            column = self._find_column(rename_match.group(1), columns)
            return [DataAction(action="rename_column", column=column, target_column=rename_match.group(2).strip())]

        add_match = re.search(r"add\s+(-?\d+(?:\.\d+)?)\s+to\s+(.+?)(?:\s+column)?$", text)
        if add_match:
            column = self._find_column(add_match.group(2), columns)
            return [DataAction(action="modify_column", column=column, operation="add", value=float(add_match.group(1)))]

        filter_match = re.search(r"where\s+(.+?)\s*(>=|<=|>|<|=|==)\s*(-?\d+(?:\.\d+)?)", text)
        if filter_match:
            column = self._find_column(filter_match.group(1), columns)
            return [
                DataAction(
                    action="filter_rows",
                    column=column,
                    operation=filter_match.group(2),
                    value=float(filter_match.group(3)),
                )
            ]

        return [DataAction(action="generate_insights")]

    def _analytics_plan(self, text: str, columns: list[str], dataframe: pd.DataFrame) -> list[DataAction]:
        if "correlation" in text:
            return [DataAction(action="correlation")]

        metric = "sum" if "total" in text or "highest" in text or "top" in text else "mean"
        numeric = self._find_numeric_column(text, dataframe) or self._first_numeric(dataframe)
        categorical = self._first_categorical(dataframe)

        top_match = re.search(r"top\s+(\d+)", text)
        limit = int(top_match.group(1)) if top_match else 10

        if categorical and numeric and ("by" in text or "top" in text or "compare" in text or "highest" in text):
            group_by = self._find_best_group_by(text, columns, dataframe) or categorical
            return [DataAction(action="groupby_metric", column=numeric, group_by=group_by, metric=metric, limit=limit)]
        return [DataAction(action="calculate_metric", column=numeric, metric=metric)]

    def _chart_action(self, text: str, columns: list[str], dataframe: pd.DataFrame) -> DataAction:
        numeric = self._find_column(text, columns) or self._first_numeric(dataframe)
        categorical = self._first_categorical(dataframe)
        date_column = self._first_date_like(dataframe)

        chart_type = "bar"
        if "pie" in text:
            chart_type = "pie"
        elif "line" in text or "trend" in text or "monthly" in text:
            chart_type = "line"
        elif "heatmap" in text or "correlation" in text:
            chart_type = "heatmap"
        elif "scatter" in text or " vs " in text:
            chart_type = "scatter"

        if chart_type == "line":
            return DataAction(action="generate_chart", chart_type=chart_type, x=date_column or categorical, y=numeric)
        if chart_type == "pie":
            return DataAction(action="generate_chart", chart_type=chart_type, x=categorical, y=numeric)
        if chart_type == "scatter":
            numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()
            return DataAction(
                action="generate_chart",
                chart_type=chart_type,
                x=numeric_columns[0] if numeric_columns else numeric,
                y=numeric_columns[1] if len(numeric_columns) > 1 else numeric,
            )
        return DataAction(action="generate_chart", chart_type=chart_type, x=categorical, y=numeric)

    def _find_column(self, text: str, columns: list[str]) -> str | None:
        normalized = {column.lower(): column for column in columns}
        for lowered, original in normalized.items():
            if lowered in text:
                return original
        matches = get_close_matches(text.strip().lower(), list(normalized.keys()), n=1, cutoff=0.65)
        return normalized[matches[0]] if matches else None

    def _find_best_group_by(self, text: str, columns: list[str], dataframe: pd.DataFrame) -> str | None:
        explicit = self._find_column(text, columns)
        if explicit and explicit not in dataframe.select_dtypes(include="number").columns:
            return explicit
        return self._first_categorical(dataframe)

    def _find_numeric_column(self, text: str, dataframe: pd.DataFrame) -> str | None:
        numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()
        return self._find_column(text, numeric_columns)

    def _first_numeric(self, dataframe: pd.DataFrame) -> str | None:
        columns = dataframe.select_dtypes(include="number").columns.tolist()
        return columns[0] if columns else None

    def _first_categorical(self, dataframe: pd.DataFrame) -> str | None:
        candidates = dataframe.select_dtypes(exclude="number").columns.tolist()
        return candidates[0] if candidates else None

    def _first_date_like(self, dataframe: pd.DataFrame) -> str | None:
        for column in dataframe.columns:
            parsed = pd.to_datetime(dataframe[column].dropna().astype(str).head(50), errors="coerce", format="mixed")
            if not parsed.empty and parsed.notna().mean() >= 0.8:
                return column
        return None


classifier = CommandClassifier()
planner = RuleBasedPlanner()
