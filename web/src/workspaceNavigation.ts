/** Presentation-only state; scientific date, sensor and spatial filters stay in explorationState. */
export interface WorkspaceNavigation {
  section: 'calendar' | 'patterns' | 'earth';
  calendar: 'weekly' | 'monthly';
  pattern: 'instruments' | 'seasons' | 'anomalies';
}

export function parseWorkspaceNavigation(search: string): WorkspaceNavigation {
  const params = new URLSearchParams(search);
  const section = params.get('workspace');
  const pattern = params.get('pattern');
  return {
    section: section === 'patterns' || section === 'earth' ? section : 'calendar',
    // The month overview is legible on first arrival; existing shared links retain their weekly default.
    calendar: params.get('calendar') === 'monthly' || params.size === 0 ? 'monthly' : 'weekly',
    pattern: pattern === 'seasons' || pattern === 'anomalies' ? pattern : 'instruments',
  };
}

export function withWorkspaceNavigation(url: string, state: WorkspaceNavigation): string {
  const result = new URL(url);
  for (const key of ['workspace', 'calendar', 'pattern']) result.searchParams.delete(key);
  if (state.section !== 'calendar') result.searchParams.set('workspace', state.section);
  if (state.calendar !== 'weekly') result.searchParams.set('calendar', state.calendar);
  if (state.pattern !== 'instruments') result.searchParams.set('pattern', state.pattern);
  return result.toString();
}
