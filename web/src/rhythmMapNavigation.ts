/** One tab stop for the map; arrow keys traverse the published cell order. */
export function nextRhythmCell(key: string, current: number, count: number): number | null {
  if (count < 1) return null;
  const index = Math.max(0, Math.min(current, count - 1));
  if (key === 'Home') return 0;
  if (key === 'End') return count - 1;
  if (key === 'ArrowRight') return Math.min(index + 1, count - 1);
  if (key === 'ArrowLeft') return Math.max(index - 1, 0);
  return null;
}
