export type Nullable = number | null;
export interface Daily {
  date: string; cell_id?: string; raw_terra: Nullable; raw_aqua: Nullable; raw_viirs: Nullable;
  raw: Nullable; harmonized: Nullable; lo: Nullable; hi: Nullable; coverage: string; source: string; model: string;
}
export interface Climatology {week: number; median: Nullable; p10: Nullable; p90: Nullable; critical: boolean}
export interface Anomaly {date: string; week: number; value: Nullable; z_score: Nullable; status: string}
export interface Critical {start_week: number; end_week: number; label: string}
export interface Evaluation {model: string; region: string; split: string; aggregation: string; bias_pct: Nullable; mae: Nullable; correlation: Nullable; peak_week_error: Nullable}
export interface RhythmStream {stream: string; weekdays: {day: string; index: Nullable; lo: Nullable; hi: Nullable}[]; years: number; rest_day: string; p_adjusted?: Nullable; status: string}
export interface Region {
  meta: {region: string; name: string; label: string; period_start: string; period_end: string; reference: string; model: string; coverage_note: string; sources: {name: string; url: string}[]; centroid: [number, number]; cell_scope?: string; cell_count_total?: number; cell_count_displayed?: number};
  daily: Daily[]; weekly_climatology: Climatology[]; anomalies: Anomaly[]; critical_periods: Critical[];
  rhythm: null | {gate: {decision: string; [key: string]: unknown} | string; streams: RhythmStream[]; rest_day: string};
  eval: Evaluation[]; cells: {id: string; lat: number; lon: number; daily: Daily[]}[];
}
export interface Index {label: string; regions: {id: string; name: string; file: string}[]; generated_at: string; limitations: string[]}
export interface Week {key: string; year: number; week: number; date: string; rows: Daily[]; raw: Nullable; harmonized: Nullable}
