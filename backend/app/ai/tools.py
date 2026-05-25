from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from app.models.schemas import ChartDataSpec, DataAction, ToolExecutionResult


class DataToolExecutor:
    def execute(self, dataframe: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, ChartDataSpec | None, list[str]]:
        df = dataframe.copy()
        handler = getattr(self, f"_execute_{action.action}", None)
        if handler is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported action: {action.action}")
        return handler(df, action)

    def _execute_drop_missing(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        before = len(df)
        cleaned = df.dropna()
        removed = before - len(cleaned)
        return cleaned, self._result(action.action, f"Removed {removed} rows containing missing values."), None, []

    def _execute_fill_missing(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        column = self._require_column(df, action.column)
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise self._bad_request(f"Column '{column}' must be numeric for mean imputation.")
        value = df[column].mean()
        count = int(df[column].isna().sum())
        df[column] = df[column].fillna(value)
        return df, self._result(action.action, f"Filled {count} missing values in '{column}' with mean {value:.2f}."), None, []

    def _execute_drop_duplicates(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        before = len(df)
        cleaned = df.drop_duplicates()
        removed = before - len(cleaned)
        return cleaned, self._result(action.action, f"Removed {removed} duplicate rows."), None, []

    def _execute_rename_column(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        column = self._require_column(df, action.column)
        if not action.target_column:
            raise self._bad_request("A target column name is required for rename operations.")
        if action.target_column in df.columns:
            raise self._bad_request(f"Column '{action.target_column}' already exists.")
        renamed = df.rename(columns={column: action.target_column})
        return renamed, self._result(action.action, f"Renamed '{column}' to '{action.target_column}'."), None, []

    def _execute_modify_column(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        column = self._require_column(df, action.column)
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise self._bad_request(f"Column '{column}' must be numeric for modification.")
        value = self._require_numeric_value(action.value)
        if action.operation == "add":
            df[column] = df[column] + value
        elif action.operation == "subtract":
            df[column] = df[column] - value
        elif action.operation == "multiply":
            df[column] = df[column] * value
        elif action.operation == "divide":
            if value == 0:
                raise self._bad_request("Cannot divide by zero.")
            df[column] = df[column] / value
        else:
            raise self._bad_request("Supported modify operations are add, subtract, multiply, and divide.")
        return df, self._result(action.action, f"Applied {action.operation} {value:g} to '{column}'."), None, []

    def _execute_filter_rows(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        column = self._require_column(df, action.column)
        value = self._require_numeric_value(action.value)
        operators = {
            ">": df[column] > value,
            ">=": df[column] >= value,
            "<": df[column] < value,
            "<=": df[column] <= value,
            "=": df[column] == value,
            "==": df[column] == value,
        }
        if action.operation not in operators:
            raise self._bad_request("Unsupported filter operator.")
        filtered = df[operators[action.operation]].copy()
        return filtered, self._result(action.action, f"Kept {len(filtered)} rows where '{column}' {action.operation} {value:g}."), None, []

    def _execute_normalize_column(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        column = self._require_column(df, action.column)
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise self._bad_request(f"Column '{column}' must be numeric for normalization.")
        minimum = df[column].min()
        maximum = df[column].max()
        if maximum == minimum:
            raise self._bad_request(f"Column '{column}' has no range to normalize.")
        df[column] = (df[column] - minimum) / (maximum - minimum)
        return df, self._result(action.action, f"Normalized '{column}' to a 0-1 scale."), None, []

    def _execute_remove_outliers(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        column = self._require_column(df, action.column)
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise self._bad_request(f"Column '{column}' must be numeric for outlier removal.")
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        filtered = df[df[column].between(lower, upper)].copy()
        return filtered, self._result(action.action, f"Removed {len(df) - len(filtered)} outliers from '{column}' using IQR bounds."), None, []

    def _execute_calculate_metric(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        column = self._require_column(df, action.column)
        metric = action.metric or "mean"
        value = self._metric(df[column], metric)
        return df, self._result(action.action, f"{metric.title()} of '{column}' is {value:.2f}.", {"metric": metric, "column": column, "value": value}), None, [
            f"{metric.title()} of {column}: {value:.2f}"
        ]

    def _execute_groupby_metric(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, ChartDataSpec, list[str]]:
        value_column = self._require_column(df, action.column)
        group_by = self._require_column(df, action.group_by)
        metric = action.metric or "sum"
        limit = action.limit or 10
        grouped = getattr(df.groupby(group_by)[value_column], metric)().sort_values(ascending=False).head(limit)
        records = [{"label": str(index), "value": self._clean_number(value)} for index, value in grouped.items()]
        chart = ChartDataSpec(
            chart_type="bar",
            title=f"Top {len(records)} {group_by} by {metric} {value_column}",
            x="label",
            y="value",
            data=records,
            insight=f"{records[0]['label']} leads with {records[0]['value']:.2f}." if records else "No grouped result found.",
        )
        return df, self._result(action.action, f"Calculated {metric} of '{value_column}' by '{group_by}'.", records), chart, [chart.insight]

    def _execute_correlation(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, ChartDataSpec | None, list[str]]:
        numeric = df.select_dtypes(include="number")
        if numeric.shape[1] < 2:
            raise self._bad_request("At least two numeric columns are required for correlation.")
        corr = numeric.corr(numeric_only=True).round(3)
        heatmap_data = [
            {"x": row, "y": column, "value": float(corr.loc[row, column])}
            for row in corr.index
            for column in corr.columns
        ]
        pairs = corr.where(~np.eye(corr.shape[0], dtype=bool)).abs().stack().sort_values(ascending=False)
        top_pair = pairs.index[0] if len(pairs) else None
        insight = f"Strongest correlation is between {top_pair[0]} and {top_pair[1]}." if top_pair else "Correlation matrix generated."
        chart = ChartDataSpec(chart_type="heatmap", title="Correlation heatmap", data=heatmap_data, insight=insight)
        return df, self._result(action.action, "Generated numeric correlation matrix.", corr.to_dict()), chart, [insight]

    def _execute_generate_chart(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, ChartDataSpec, list[str]]:
        chart_type = action.chart_type or "bar"
        if chart_type == "heatmap":
            _, result, chart, insights = self._execute_correlation(df, DataAction(action="correlation"))
            if chart is None:
                raise self._bad_request("Could not generate heatmap.")
            return df, result, chart, insights

        x = self._require_column(df, action.x)
        y = self._require_column(df, action.y) if action.y else None
        if chart_type in {"bar", "pie", "line"}:
            if y and pd.api.types.is_numeric_dtype(df[y]):
                data = df.groupby(x)[y].sum().sort_values(ascending=False).head(20)
                records = [{"label": str(index), "value": self._clean_number(value)} for index, value in data.items()]
            else:
                data = df[x].value_counts().head(20)
                records = [{"label": str(index), "value": int(value)} for index, value in data.items()]
            insight = f"{records[0]['label']} is the leading segment." if records else "Chart generated."
            chart = ChartDataSpec(chart_type=chart_type, title=f"{chart_type.title()} chart for {x}", x="label", y="value", data=records, insight=insight)
            return df, self._result(action.action, f"Generated {chart_type} chart."), chart, [insight]

        if chart_type == "scatter":
            y = self._require_column(df, action.y)
            records = df[[x, y]].dropna().head(500).to_dict(orient="records")
            chart = ChartDataSpec(chart_type="scatter", title=f"{y} vs {x}", x=x, y=y, data=records, insight="Scatter plot generated for relationship inspection.")
            return df, self._result(action.action, "Generated scatter plot."), chart, [chart.insight]

        raise self._bad_request(f"Unsupported chart type: {chart_type}")

    def _execute_generate_insights(self, df: pd.DataFrame, action: DataAction) -> tuple[pd.DataFrame, ToolExecutionResult, None, list[str]]:
        insights = self._basic_insights(df)
        return df, self._result(action.action, "Generated business insights.", insights), None, insights

    def _basic_insights(self, df: pd.DataFrame) -> list[str]:
        insights = [
            f"The active dataset has {len(df):,} rows and {df.shape[1]:,} columns.",
            f"There are {int(df.isna().sum().sum()):,} missing values and {int(df.duplicated().sum()):,} duplicate rows.",
        ]
        numeric = df.select_dtypes(include="number")
        if not numeric.empty:
            highest_mean = numeric.mean(numeric_only=True).sort_values(ascending=False).index[0]
            insights.append(f"{highest_mean} has the highest average among numeric columns.")
        categorical = df.select_dtypes(exclude="number")
        if not categorical.empty:
            column = categorical.columns[0]
            top = df[column].value_counts().head(1)
            if not top.empty:
                insights.append(f"{top.index[0]} is the most frequent value in {column}.")
        return insights

    def _metric(self, series: pd.Series, metric: str) -> float:
        if metric == "sum":
            return float(series.sum())
        if metric in {"avg", "average", "mean"}:
            return float(series.mean())
        if metric == "max":
            return float(series.max())
        if metric == "min":
            return float(series.min())
        raise self._bad_request(f"Unsupported metric: {metric}")

    def _require_column(self, df: pd.DataFrame, column: str | None) -> str:
        if not column:
            raise self._bad_request("The requested operation needs a target column.")
        if column not in df.columns:
            raise self._bad_request(f"Column '{column}' was not found in the dataset.")
        return column

    def _require_numeric_value(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise self._bad_request("A numeric value is required for this operation.") from exc

    def _result(self, tool: str, message: str, data: Any = None) -> ToolExecutionResult:
        return ToolExecutionResult(tool=tool, success=True, message=message, data=self._clean_value(data))

    def _bad_request(self, message: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    def _clean_number(self, value: Any) -> float:
        if isinstance(value, np.generic):
            value = value.item()
        return float(value)

    def _clean_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._clean_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._clean_value(item) for item in value]
        if isinstance(value, np.generic):
            return value.item()
        return value


tool_executor = DataToolExecutor()
