// Validate the fields the views read. Never coerce, replace, or recompute results.
const object = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === 'object' && !Array.isArray(v);
const string = (v: unknown) => typeof v === 'string';
const number = (v: unknown) => typeof v === 'number' && Number.isFinite(v);
const boolean = (v: unknown) => typeof v === 'boolean';
const nullable = (v: unknown, check: (v: unknown) => boolean) => v == null || check(v);
const array = (v: unknown, check: (v: unknown) => boolean): v is unknown[] => Array.isArray(v) && v.every(check);
const dictionary = (v: unknown, check: (v: unknown) => boolean) => object(v) && Object.values(v).every(check);
const fields = (v: Record<string, unknown>, keys: string[], check: (v: unknown) => boolean) => keys.every(key => check(v[key]));
const strings = (v: unknown) => array(v, string);
const day = (v: unknown) => object(v) && string(v.day) && fields(v, ['index', 'lo', 'hi'], n => nullable(n, number));
const stream = (v: unknown) => object(v) && fields(v, ['stream', 'status'], string) && number(v.detections)
  && (v.status !== 'ok' || (array(v.weekdays, day) && v.weekdays.length > 0))
  && nullable(v.weekdays, rows => array(rows, day))
  && fields(v, ['years', 'rest_index', 'p_null', 'bonferroni_m'], n => nullable(n, number))
  && nullable(v.lowest_day, string) && nullable(v.significant, boolean);
const check = (v: unknown) => object(v) && boolean(v.passed) && nullable(v.status, string) && nullable(v.streams, number);

export function validRhythmPayload(v: unknown): boolean {
  if (!object(v) || !fields(v, ['label', 'wording'], string) || !strings(v.caveats)
    || !nullable(v.headline, string) || !nullable(v.sunday_caveat, string) || !object(v.official)) return false;
  if (!fields(v.official, ['decision', 'source'], string)
    || !dictionary(v.official.per_country, c => object(c) && string(c.status)
      && fields(c, ['streams_significant', 'streams_with_data'], number))) return false;
  if (!array(v.countries, c => object(c) && fields(c, ['country', 'name', 'rest_day', 'status'], string)
    && array(c.streams, stream) && array(c.daytime_streams, stream)) || !v.countries.length) return false;
  if (!array(v.negative_control, c => object(c) && string(c.stream) && number(c.detections)
    && nullable(c.max_abs_deviation, number))) return false;
  if (v.robustness == null) return true;
  const r = v.robustness;
  return object(r) && dictionary(r.descriptions, string) && dictionary(r.flagged, strings)
    && nullable(r.notes, notes => dictionary(notes, string)) && nullable(r.control_nuance, string) && nullable(r.source, string)
    && dictionary(r.per_country, c => object(c) && fields(c, ['ci_upper_below_one', 'strict_reanalysis', 'matched_static_controls'], check));
}

export function validRhythmCellTable(v: unknown): boolean {
  if (!object(v) || !object(v.metadata) || !string(v.metadata.label) || !array(v.columns, string)
    || new Set(v.columns).size !== v.columns.length || !Array.isArray(v.rows)) return false;
  const columns = v.columns as string[];
  const numeric = ['cell_lat', 'cell_lon', 'years', 'mean_detections_per_year', 'rest_index', 'ci_lo', 'ci_hi', 'q_bh'];
  const required = ['country', 'rest_day', ...numeric, 'significant', 'aqua_rest_index', 'aqua_significant'];
  if (!required.every(key => columns.includes(key))) return false;
  return v.rows.every(row => {
    if (!Array.isArray(row) || row.length !== columns.length) return false;
    const cell = Object.fromEntries(columns.map((key, i) => [key, row[i]]));
    return fields(cell, ['country', 'rest_day'], string) && fields(cell, numeric, number)
      && boolean(cell.significant) && nullable(cell.aqua_rest_index, number) && nullable(cell.aqua_significant, boolean);
  });
}

export function validRhythmCellSummary(v: unknown): boolean {
  if (!object(v) || !dictionary(v.aqua_check, c => object(c)
    && fields(c, ['cells_with_both', 'viirs_sig_cells_with_aqua', 'of_those_aqua_below_1', 'of_those_aqua_significant'], number)
    && nullable(c.corr_rest_index, number))) return false;
  if (v.northeast_india_area == null) return true;
  return object(v.northeast_india_area) && fields(v.northeast_india_area,
    ['northeast_mostly_india', 'northeast_cross_border', 'rest_of_india_mostly_india'],
    area => object(area) && fields(area, ['cells', 'significant'], number) && nullable(area.median_sunday_index, number));
}

export function validRhythmLand(v: unknown): boolean {
  const point = (p: unknown) => Array.isArray(p) && p.length >= 2 && number(p[0]) && number(p[1]);
  const polygon = (p: unknown) => array(p, ring => array(ring, point));
  return object(v) && array(v.features, feature => object(feature) && object(feature.geometry)
    && (feature.geometry.type === 'Polygon' ? polygon(feature.geometry.coordinates)
      : feature.geometry.type === 'MultiPolygon' && array(feature.geometry.coordinates, polygon)));
}
