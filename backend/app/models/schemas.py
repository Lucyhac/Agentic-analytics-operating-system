from typing import Any, Literal

from pydantic import BaseModel, Field


ColumnKind = Literal["numeric", "categorical", "datetime", "boolean", "text", "unknown"]


class ColumnProfile(BaseModel):
    name: str
    kind: ColumnKind
    dtype: str
    missing_count: int
    missing_percent: float
    unique_count: int
    sample_values: list[Any]
    stats: dict[str, Any] = Field(default_factory=dict)


class ChartRecommendation(BaseModel):
    chart_type: Literal["bar", "line", "pie", "heatmap", "scatter", "histogram"]
    title: str
    x: str | None = None
    y: str | None = None
    reason: str


class DatasetProfile(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    duplicate_rows: int
    total_missing_values: int
    memory_usage_mb: float
    numeric_columns: list[str]
    categorical_columns: list[str]
    date_columns: list[str]
    boolean_columns: list[str]
    column_profiles: list[ColumnProfile]
    statistical_overview: dict[str, dict[str, Any]]
    top_categories: dict[str, list[dict[str, Any]]]
    date_ranges: dict[str, dict[str, str | None]]
    correlation_matrix: dict[str, dict[str, float]]
    kpis: list[dict[str, Any]]
    chart_recommendations: list[ChartRecommendation]
    preview_rows: list[dict[str, Any]]


class UploadResponse(BaseModel):
    message: str
    profile: DatasetProfile


AgentIntent = Literal[
    "cleaning",
    "modification",
    "analytics",
    "visualization",
    "forecasting",
    "insights",
    "unknown",
]

ActionName = Literal[
    "drop_missing",
    "fill_missing",
    "drop_duplicates",
    "rename_column",
    "modify_column",
    "filter_rows",
    "normalize_column",
    "remove_outliers",
    "calculate_metric",
    "groupby_metric",
    "correlation",
    "generate_chart",
    "generate_insights",
]


class DataAction(BaseModel):
    action: ActionName
    column: str | None = None
    target_column: str | None = None
    operation: str | None = None
    value: Any = None
    metric: str | None = None
    group_by: str | None = None
    limit: int | None = None
    chart_type: str | None = None
    x: str | None = None
    y: str | None = None


class ChartDataSpec(BaseModel):
    chart_type: Literal["bar", "line", "pie", "heatmap", "scatter", "histogram"]
    title: str
    x: str | None = None
    y: str | None = None
    data: list[dict[str, Any]]
    insight: str


class ToolExecutionResult(BaseModel):
    tool: str
    success: bool
    message: str
    data: Any = None


class AgentRequest(BaseModel):
    dataset_id: str
    message: str
    conversation_id: str | None = None


class AgentResponse(BaseModel):
    conversation_id: str
    intent: AgentIntent
    response: str
    actions: list[DataAction]
    tool_results: list[ToolExecutionResult]
    profile: DatasetProfile
    charts: list[ChartDataSpec] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
