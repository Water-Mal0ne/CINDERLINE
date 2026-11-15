/** Pure URL-state helpers. No network, storage, DOM, HTML or credentials. */
export type View = 'explore' | 'evidence' | 'rhythm' | 'methods';
export type Scale = 'harmonized' | 'raw';
export type GlobeView = 'earth' | 'table';

export interface RegionAvailability {
  id: string;
  start: string;
  end: string;
  dailyCellIds: readonly string[];
  globeYears: readonly number[];
}
export interface ExplorationCatalog {
  regions: readonly RegionAvailability[];
  defaultRegionId?: string;
  /** Exact published IDs, e.g. Nepal:27.25:84.75; not arbitrary coordinates. */
  globeCellIds: readonly string[];
  /** Optional immutable build/dataset identifier supplied by the publisher. */
  dataVersion?: string;
}
export interface ExplorationState {
  region: string;
  start: string;
  end: string;
  cell: string;
  view: View;
  scale: Scale;
  /** Kept consistent with the calendar end year, as in the current app. */
  globeYear: number;
  globeCell: string | null;
  globeView: GlobeView;
  /** January-1-anchored week start; resolved to actual rows by the UI. */
  evidenceWeek: string | null;
}
export interface Resolution {
  state: ExplorationState;
  notices: string[];
  hasSharedState: boolean;
  canonicalQuery: string;
}

export const SHARE_VERSION = '1';
export const MAX_QUERY_LENGTH = 2048;
const KEYS = ['v','region','start','end','cell','view','scale','globeYear','globeCell','globeView','week','data'] as const;
const DAY_MS = 86_400_000;

/** Rejects rolled-over dates (2023-02-29), timestamps and locale-dependent forms. */
export function isCivilDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split('-').map(Number);
  if (year < 1000 || year > 9999 || month < 1 || month > 12 || day < 1 || day > 31) return false;
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

function assertCatalog(catalog: ExplorationCatalog): void {
  if (!catalog.regions.length) throw new Error('No published regions are available.');
  const seen = new Set<string>();
  for (const region of catalog.regions) {
    if (!region.id || seen.has(region.id) || !isCivilDate(region.start) || !isCivilDate(region.end) || region.start > region.end)
      throw new Error('Invalid published region catalog.');
    seen.add(region.id);
    if (!region.globeYears.length || region.globeYears.some(year => !Number.isInteger(year) || year < 1000 || year > 9999))
      throw new Error('The published globe must identify supported years.');
  }
}

function yearForDate(end: string, region: RegionAvailability): number {
  const target = Number(end.slice(0,4));
  if (region.globeYears.includes(target)) return target;
  // An unavailable archive year stays unavailable. Use the nearest supported
  // year (earlier on a tie) and report the substitution explicitly.
  return [...region.globeYears].sort((a,b) => Math.abs(a-target)-Math.abs(b-target) || a-b)[0];
}

export function defaultExploration(catalog: ExplorationCatalog, regionId?: string): ExplorationState {
  assertCatalog(catalog);
  const region = catalog.regions.find(r => r.id === regionId)
    ?? catalog.regions.find(r => r.id === catalog.defaultRegionId) ?? catalog.regions[0];
  return {region:region.id,start:region.start,end:region.end,cell:'ALL',view:'explore',scale:'harmonized',
    globeYear:yearForDate(region.end,region),globeCell:null,globeView:'earth',evidenceWeek:null};
}

/** First-stage hint lets App load exactly one region before full validation. */
export function linkedRegion(search: string, availableIds: readonly string[], fallbackId?: string): string | null {
  const fallback = availableIds.includes(fallbackId ?? '') ? fallbackId! : availableIds[0] ?? null;
  if (search.length > MAX_QUERY_LENGTH) return fallback;
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  if (params.getAll('region').length !== 1 || (params.has('v') && params.get('v') !== SHARE_VERSION)) return fallback;
  const value = params.get('region')!;
  return availableIds.includes(value) ? value : fallback;
}

/** Page selection does not require the calendar catalog to be available. */
export function linkedView(search: string): View {
  if (search.length > MAX_QUERY_LENGTH) return 'explore';
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  const versions = params.getAll('v'), views = params.getAll('view');
  if (versions.length === 1 && versions[0] !== SHARE_VERSION) return 'explore';
  return views.length === 1 && (['explore','evidence','rhythm','methods'] as string[]).includes(views[0]) ? views[0] as View : 'explore';
}

function encodeState(state: ExplorationState, dataVersion?: string): string {
  const params = new URLSearchParams();
  params.set('v', SHARE_VERSION);
  params.set('region', state.region);
  params.set('start', state.start);
  params.set('end', state.end);
  if (state.cell !== 'ALL') params.set('cell', state.cell);
  if (state.view !== 'explore') params.set('view', state.view);
  if (state.scale !== 'harmonized') params.set('scale', state.scale);
  params.set('globeYear', String(state.globeYear));
  if (state.globeCell) params.set('globeCell', state.globeCell);
  if (state.globeView !== 'earth') params.set('globeView', state.globeView);
  if (state.evidenceWeek) params.set('week', state.evidenceWeek);
  if (dataVersion) params.set('data', dataVersion);
  return '?' + params.toString();
}

export function resolveExploration(search: string, catalog: ExplorationCatalog): Resolution {
  assertCatalog(catalog);
  const notices: string[] = [];
  const notify = (message: string) => {if (!notices.includes(message)) notices.push(message);};
  let params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  const hasSharedState = KEYS.some(key => params.has(key));
  if (search.length > MAX_QUERY_LENGTH) {
    params = new URLSearchParams();
    notify('This exploration link is too long. The full published record has been restored.');
  }
  const value = (key: typeof KEYS[number]): string | null => {
    const values = params.getAll(key);
    if (values.length > 1) {
      notify('A repeated link setting was ignored. Review the restored view before sharing it.');
      return null;
    }
    return values[0] ?? null;
  };
  const version = value('v');
  if (version !== null && version !== SHARE_VERSION) {
    const state = defaultExploration(catalog);
    notify('This link uses an unsupported format. The full published record has been restored.');
    return {state,notices,hasSharedState,canonicalQuery:encodeState(state,catalog.dataVersion)};
  }
  const regionValue = value('region');
  const requestedRegion = catalog.regions.find(region => region.id === regionValue);
  const state = defaultExploration(catalog, requestedRegion?.id);
  const region = catalog.regions.find(region => region.id === state.region)!;
  const unknownRegion = regionValue !== null && !requestedRegion;
  if (unknownRegion) notify('That region is not published in this release. The default region and its full record are shown.');

  // Region-dependent settings cannot silently carry across an unknown country.
  if (!unknownRegion) {
    for (const key of ['start','end'] as const) {
      const date = value(key);
      if (date === null) continue;
      if (!isCivilDate(date)) {
        notify('An invalid date was replaced with a supported record boundary.');
      } else {
        state[key] = date < region.start ? region.start : date > region.end ? region.end : date;
        if (state[key] !== date) notify('The date range was limited to the published record.');
      }
    }
    if (state.start > state.end) {
      state.start = region.start; state.end = region.end;
      notify('The link’s start date followed its end date. The full record has been restored.');
    }
    const cell = value('cell');
    if (cell !== null && cell !== 'ALL') {
      if (region.dailyCellIds.includes(cell)) state.cell = cell;
      else notify('That daily grid cell is not published for this region. The whole-region record is shown.');
    }
  }

  const readChoice = <T extends string>(key:typeof KEYS[number], choices:readonly T[], fallback:T):T => {
    const choice = value(key);
    if (choice === null) return fallback;
    if (choices.includes(choice as T)) return choice as T;
    notify('An unsupported display setting was replaced with its default.');
    return fallback;
  };
  state.view = readChoice('view',['explore','evidence','rhythm','methods'] as const,'explore');
  state.scale = readChoice('scale',['harmonized','raw'] as const,'harmonized');
  state.globeView = readChoice('globeView',['earth','table'] as const,'earth');
  state.globeYear = yearForDate(state.end,region);
  const globeYear = value('globeYear');
  if (globeYear !== null && (!/^\d{4}$/.test(globeYear) || Number(globeYear) !== state.globeYear))
    notify('The globe year was aligned with the calendar’s supported end year.');
  if (state.globeYear !== Number(state.end.slice(0,4)))
    notify('The calendar end year has no annual globe layer. The nearest supported globe year is shown.');
  const globeCell = value('globeCell');
  if (globeCell !== null && !unknownRegion) {
    if (catalog.globeCellIds.includes(globeCell)) state.globeCell = globeCell;
    else notify('That annual grid cell is not published. The globe selection was cleared.');
  }
  const week = value('week');
  if (week !== null && !unknownRegion) {
    if (isCivilDate(week)) {
      const year = Number(week.slice(0,4));
      const time = Date.parse(week + 'T00:00:00Z');
      const day = Math.round((time - Date.UTC(year,0,1)) / DAY_MS);
      const last = Math.min(time + 6*DAY_MS,Date.UTC(year+1,0,1)-DAY_MS);
      if (day % 7 === 0 && week <= state.end && new Date(last).toISOString().slice(0,10) >= state.start)
        state.evidenceWeek = week;
    }
    if (!state.evidenceWeek) notify('The selected evidence week is outside this view or is invalid. Its panel was closed.');
  }
  const dataVersion = value('data');
  if (dataVersion !== null && catalog.dataVersion && dataVersion !== catalog.dataVersion)
    notify('This link was created with another data release. The current published data is shown; values may differ.');
  return {state,notices,hasSharedState,canonicalQuery:encodeState(state,catalog.dataVersion)};
}

/** Creates a clean same-page link, retaining no pre-existing query, hash or userinfo. */
export function createShareLink(basePage: string, state: ExplorationState, catalog: ExplorationCatalog): Resolution & {url:string} {
  const base = new URL(basePage);
  if (!['https:','http:'].includes(base.protocol) || base.username || base.password)
    throw new Error('Share links require a public HTTP(S) page without embedded credentials.');
  const resolved = resolveExploration(encodeState(state,catalog.dataVersion),catalog);
  base.search = resolved.canonicalQuery;
  base.hash = '';
  return {...resolved,url:base.toString()};
}
