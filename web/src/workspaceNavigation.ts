/** Presentation-only state; scientific date, sensor and spatial filters stay in explorationState. */
export interface WorkspaceNavigation {
  section: 'home' | 'calendar' | 'patterns' | 'earth';
  calendar: 'weekly' | 'monthly';
  pattern: 'instruments' | 'seasons' | 'anomalies';
  homeWeek?: string;
}

function validWeekDate(date: string | null): date is string {
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return false;
  const stamp = Date.parse(date + 'T00:00:00Z');
  return Number.isFinite(stamp) && new Date(stamp).toISOString().slice(0, 10) === date
    && (stamp - Date.UTC(Number(date.slice(0, 4)), 0, 1)) / 86400000 % 7 === 0;
}

export function parseWorkspaceNavigation(search: string): WorkspaceNavigation {
  const params = new URLSearchParams(search);
  const section = params.get('workspace');
  const pattern = params.get('pattern');
  const homeWeek = params.get('homeWeek');
  return {
    // Keep previously shared Introduction links working after the Home rename.
    section: section === 'home' || section === 'introduction' || params.size === 0 ? 'home' : section === 'patterns' || section === 'earth' ? section : 'calendar',
    // The month overview is legible on first arrival; existing shared links retain their weekly default.
    calendar: params.get('calendar') === 'monthly' || params.size === 0 ? 'monthly' : 'weekly',
    pattern: pattern === 'seasons' || pattern === 'anomalies' ? pattern : 'instruments',
    ...(params.getAll('homeWeek').length === 1 && validWeekDate(homeWeek) ? {homeWeek} : {}),
  };
}

export function withWorkspaceNavigation(url: string, state: WorkspaceNavigation): string {
  const result = new URL(url);
  for (const key of ['workspace', 'calendar', 'pattern', 'homeWeek']) result.searchParams.delete(key);
  if (state.section !== 'calendar') result.searchParams.set('workspace', state.section);
  if (state.calendar !== 'weekly') result.searchParams.set('calendar', state.calendar);
  if (state.pattern !== 'instruments') result.searchParams.set('pattern', state.pattern);
  if (validWeekDate(state.homeWeek ?? null)) result.searchParams.set('homeWeek', state.homeWeek!);
  return result.toString();
}
