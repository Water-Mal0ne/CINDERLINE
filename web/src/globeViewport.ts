/** Fit the whole sphere in the narrower field of view, leaving room around it. */
export function globeOverviewDistance(verticalFovDegrees:number,aspect:number):number {
  const vertical=verticalFovDegrees*Math.PI/360;
  const horizontal=Math.atan(Math.tan(vertical)*Math.max(aspect,.01));
  return 1.007/Math.sin(Math.min(vertical,horizontal)*.9);
}
