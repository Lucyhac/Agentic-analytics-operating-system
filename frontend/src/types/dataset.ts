export type ColumnKind = 'numeric' | 'categorical' | 'datetime' | 'boolean' | 'text' | 'unknown';

export interface ColumnProfile {
  name: string;
  kind: ColumnKind;
  dtype: string;
  missing_count: number;
  missing_percent: number;
  unique_count: number;
  sample_values: unknown[];
  stats: Record<string, unknown>;
}

export interface ChartRecommendation {
  chart_type: 'bar' | 'line' | 'pie' | 'heatmap' | 'scatter' | 'histogram';
  title: string;
  x?: string | null;
  y?: string | null;
  reason: string;
}

export interface DatasetProfile {
  dataset_id: string;
  filename: string;
  rows: number;
  columns: number;
  duplicate_rows: number;
  total_missing_values: number;
  memory_usage_mb: number;
  numeric_columns: string[];
  categorical_columns: string[];
  date_columns: string[];
  boolean_columns: string[];
  column_profiles: ColumnProfile[];
  statistical_overview: Record<string, Record<string, unknown>>;
  top_categories: Record<string, Array<{ label: string; count: number }>>;
  date_ranges: Record<string, { start: string | null; end: string | null }>;
  correlation_matrix: Record<string, Record<string, number>>;
  kpis: Array<{ label: string; value: unknown; type: string }>;
  chart_recommendations: ChartRecommendation[];
  preview_rows: Record<string, unknown>[];
}

export interface UploadResponse {
  message: string;
  profile: DatasetProfile;
}

export interface DataAction {
  action: string;
  column?: string | null;
  target_column?: string | null;
  operation?: string | null;
  value?: unknown;
  metric?: string | null;
  group_by?: string | null;
  limit?: number | null;
  chart_type?: string | null;
  x?: string | null;
  y?: string | null;
}

export interface AgentChart {
  chart_type: 'bar' | 'line' | 'pie' | 'heatmap' | 'scatter' | 'histogram';
  title: string;
  x?: string | null;
  y?: string | null;
  data: Record<string, unknown>[];
  insight: string;
}

export interface ToolExecutionResult {
  tool: string;
  success: boolean;
  message: string;
  data?: unknown;
}

export interface AgentResponse {
  conversation_id: string;
  intent: string;
  response: string;
  actions: DataAction[];
  tool_results: ToolExecutionResult[];
  profile: DatasetProfile;
  charts: AgentChart[];
  insights: string[];
}
