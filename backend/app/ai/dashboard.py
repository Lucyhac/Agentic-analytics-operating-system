from __future__ import annotations

import pandas as pd

from app.models.schemas import ChartDataSpec


class DashboardChartBuilder:
    def build(self, dataframe: pd.DataFrame, existing: list[ChartDataSpec] | None = None) -> list[ChartDataSpec]:
        charts = list(existing or [])
        signatures = {self._signature(chart) for chart in charts}

        for chart in self._recommended_charts(dataframe):
            signature = self._signature(chart)
            if signature not in signatures:
                charts.append(chart)
                signatures.add(signature)
            if len(charts) >= 6:
                break

        return charts

    def _recommended_charts(self, df: pd.DataFrame) -> list[ChartDataSpec]:
        numeric = df.select_dtypes(include="number").columns.tolist()
        categorical = df.select_dtypes(exclude="number").columns.tolist()
        date_column = self._first_date_like(df)
        charts: list[ChartDataSpec] = []

        if categorical and numeric:
            charts.append(self._bar_chart(df, categorical[0], numeric[0]))
            charts.append(self._pie_chart(df, categorical[0], numeric[0]))

        if date_column and numeric:
            charts.append(self._line_chart(df, date_column, numeric[0]))

        if len(numeric) >= 2:
            charts.append(self._scatter_chart(df, numeric[0], numeric[1]))
            charts.append(self._heatmap_chart(df, numeric))

        if numeric:
            charts.append(self._histogram_chart(df, numeric[0]))

        return charts

    def _bar_chart(self, df: pd.DataFrame, category: str, value: str) -> ChartDataSpec:
        grouped = df.groupby(category)[value].sum().sort_values(ascending=False).head(12)
        records = [{"label": str(index), "value": float(item)} for index, item in grouped.items()]
        return ChartDataSpec(
            chart_type="bar",
            title=f"{value} by {category}",
            x="label",
            y="value",
            data=records,
            insight=self._leader_insight(records, category, value),
        )

    def _pie_chart(self, df: pd.DataFrame, category: str, value: str) -> ChartDataSpec:
        grouped = df.groupby(category)[value].sum().sort_values(ascending=False).head(8)
        records = [{"label": str(index), "value": float(item)} for index, item in grouped.items()]
        return ChartDataSpec(
            chart_type="pie",
            title=f"{value} share by {category}",
            x="label",
            y="value",
            data=records,
            insight=self._leader_insight(records, category, value),
        )

    def _line_chart(self, df: pd.DataFrame, date_column: str, value: str) -> ChartDataSpec:
        working = df[[date_column, value]].copy()
        working[date_column] = pd.to_datetime(working[date_column], errors="coerce", format="mixed")
        grouped = working.dropna().groupby(pd.Grouper(key=date_column, freq="ME"))[value].sum().tail(18)
        records = [{"label": index.strftime("%b %Y"), "value": float(item)} for index, item in grouped.items()]
        return ChartDataSpec(
            chart_type="line",
            title=f"{value} trend over time",
            x="label",
            y="value",
            data=records,
            insight="The line chart shows the recent time-based movement for the selected metric.",
        )

    def _scatter_chart(self, df: pd.DataFrame, x: str, y: str) -> ChartDataSpec:
        records = df[[x, y]].dropna().head(400).to_dict(orient="records")
        return ChartDataSpec(
            chart_type="scatter",
            title=f"{y} vs {x}",
            x=x,
            y=y,
            data=records,
            insight=f"Scatter view compares {x} and {y} to reveal clusters and outliers.",
        )

    def _heatmap_chart(self, df: pd.DataFrame, numeric: list[str]) -> ChartDataSpec:
        corr = df[numeric[:8]].corr(numeric_only=True).round(3)
        records = [
            {"x": row, "y": column, "value": float(corr.loc[row, column])}
            for row in corr.index
            for column in corr.columns
        ]
        return ChartDataSpec(
            chart_type="heatmap",
            title="Correlation heatmap",
            data=records,
            insight="Correlation heatmap highlights the strongest relationships between numeric columns.",
        )

    def _histogram_chart(self, df: pd.DataFrame, value: str) -> ChartDataSpec:
        counts = pd.cut(df[value].dropna(), bins=8).value_counts().sort_index()
        records = [{"label": str(index), "value": int(item)} for index, item in counts.items()]
        return ChartDataSpec(
            chart_type="histogram",
            title=f"{value} distribution",
            x="label",
            y="value",
            data=records,
            insight=f"Distribution chart shows spread and skew for {value}.",
        )

    def _first_date_like(self, df: pd.DataFrame) -> str | None:
        for column in df.columns:
            sample = df[column].dropna().astype(str).head(80)
            if sample.empty:
                continue
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() >= 0.8:
                return column
        return None

    def _leader_insight(self, records: list[dict[str, float | str]], category: str, value: str) -> str:
        if not records:
            return "No chartable records were found."
        leader = records[0]
        return f"{leader['label']} leads {category} by {value}."

    def _signature(self, chart: ChartDataSpec) -> tuple[str, str]:
        return chart.chart_type, chart.title


dashboard_chart_builder = DashboardChartBuilder()
