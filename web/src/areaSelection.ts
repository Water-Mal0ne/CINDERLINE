/** Area-of-interest arithmetic on the published per-cell monthly series. Pure functions; no model or refitting. */
export interface AreaPayload {
  label: string; country: string; model: string; reference: string; first_month: string; months: number; grid: number;
  unit: string; switch: string; outage_months: string[]; note: string; lat: number[]; lon: number[]; series: number[][];
}
export interface Rect {south: number; north: number; west: number; east: number}
export interface Circle {lat: number; lon: number; km: number}
export type Selection = {kind: 'rect'; rect: Rect} | {kind: 'circle'; circle: Circle};

export const AREA_NOTE = 'Area values use national calibration; local accuracy has not been validated.';
const EARTH_KM = 6371.0088;

export function validPayload(value: unknown): value is AreaPayload {
  const v = value as AreaPayload;
  return !!v && typeof v === 'object' && Array.isArray(v.lat) && Array.isArray(v.lon) && Array.isArray(v.series)
    && v.lat.length === v.lon.length && v.lat.length === v.series.length && Number.isInteger(v.months) && v.months > 0
    && typeof v.first_month === 'string' && /^\d{4}-\d{2}$/.test(v.first_month) && Array.isArray(v.outage_months);
}

export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number) {
  const r = Math.PI / 180, dLat = (lat2 - lat1) * r, dLon = (lon2 - lon1) * r;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_KM * Math.asin(Math.min(1, Math.sqrt(a)));
}

/** Indices of cells whose centre lies inside the selection. */
export function selectCells(area: AreaPayload, selection: Selection): number[] {
  const out: number[] = [];
  for (let i = 0; i < area.lat.length; i++) {
    const lat = area.lat[i], lon = area.lon[i];
    if (selection.kind === 'rect') {
      const {south, north, west, east} = selection.rect;
      if (lat >= south && lat <= north && lon >= west && lon <= east) out.push(i);
    } else if (haversineKm(selection.circle.lat, selection.circle.lon, lat, lon) <= selection.circle.km) out.push(i);
  }
  return out;
}

/** Decode the sparse [month-delta, tenths] pairs of the selected cells and sum them per month (detections). */
export function sumSeries(area: AreaPayload, indices: readonly number[]): Float64Array {
  const total = new Float64Array(area.months);
  for (const i of indices) {
    const s = area.series[i];
    let month = 0;
    for (let k = 0; k + 1 < s.length; k += 2) {
      month += s[k];
      if (month < area.months) total[month] += s[k + 1];
    }
  }
  for (let m = 0; m < total.length; m++) total[m] /= 10;
  return total;
}

/** Validation message for typed latitude, longitude and radius; null when valid. */
export function circleError(lat: string, lon: string, km: string): string | null {
  const a = Number(lat), b = Number(lon), r = Number(km);
  if ([lat, lon, km].some(v => v.trim() === '') || ![a, b, r].every(Number.isFinite)) return 'Enter a latitude, a longitude and a radius as numbers.';
  if (a < -90 || a > 90) return 'Latitude must be between -90 and 90.';
  if (b < -180 || b > 180) return 'Longitude must be between -180 and 180.';
  if (r <= 0 || r > 1000) return 'Radius must be more than 0 and at most 1,000 km.';
  return null;
}

export function describeSelection(selection: Selection) {
  const f = (v: number) => v.toFixed(3);
  return selection.kind === 'rect'
    ? `Rectangle ${f(selection.rect.south)} to ${f(selection.rect.north)} latitude, ${f(selection.rect.west)} to ${f(selection.rect.east)} longitude`
    : `Circle of ${selection.circle.km} km around ${f(selection.circle.lat)}, ${f(selection.circle.lon)}`;
}

export function firstYear(area: AreaPayload) { return Number(area.first_month.slice(0, 4)); }
