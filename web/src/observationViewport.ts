/** Geometry decisions only. No resampling or modification of observations. */
export const OBSERVATION_MIN_DISTANCE = 1.003;
export const OBSERVATION_POINT_DISTANCE = 1.055;
export const OBSERVATION_POINT_BUDGET = 80000;

export interface ObservationView {
  lat:number;
  lon:number;
  distance:number;
  radiusDegrees:number;
}

export function surfaceView(x:number,y:number,z:number,fov:number,aspect:number):ObservationView {
  const distance=Math.hypot(x,y,z);
  if(!Number.isFinite(distance)||distance<=1||!Number.isFinite(fov)||fov<=0||fov>=180||!Number.isFinite(aspect)||aspect<=0)
    throw new Error('Invalid observation camera');
  const diagonal=Math.atan(Math.tan(fov*Math.PI/360)*Math.hypot(1,aspect));
  const discriminant=1-distance*distance*Math.sin(diagonal)**2;
  let radius=Math.acos(1/distance);
  if(discriminant>=0){
    const ray=distance*Math.cos(diagonal)-Math.sqrt(discriminant);
    radius=Math.atan2(ray*Math.sin(diagonal),distance-ray*Math.cos(diagonal));
  }
  return {lat:Math.asin(y/distance)*180/Math.PI,lon:Math.atan2(x,z)*180/Math.PI,distance,
    radiusDegrees:radius*180/Math.PI};
}

export function angularSeparation(lat1:number,lon1:number,lat2:number,lon2:number):number {
  const rad=Math.PI/180,a=lat1*rad,b=lat2*rad,d=(lon2-lon1)*rad;
  return Math.acos(Math.max(-1,Math.min(1,Math.sin(a)*Math.sin(b)+Math.cos(a)*Math.cos(b)*Math.cos(d))))/rad;
}

/** A conservative spherical cap encloses the viewport; tile corner padding avoids edge holes. */
export function tileIntersectsView(bounds:readonly number[],view:ObservationView):boolean {
  const [west,south,east,north]=bounds;
  const lat=(south+north)/2,lon=(west+east)/2;
  // Distance along a meridian then a parallel bounds any centre-to-point path.
  // This deliberately overfetches near polar edges rather than omitting records.
  const padding=(north-south)/2+(east-west)/2;
  return angularSeparation(lat,lon,view.lat,view.lon)<=view.radiusDegrees+padding+.02;
}

export function pointInView(lat:number,lon:number,view:ObservationView):boolean {
  return angularSeparation(lat,lon,view.lat,view.lon)<=view.radiusDegrees+.02;
}

export function boundedObservationZoom(distance:number,factor:number,maxDistance:number):number {
  if(!Number.isFinite(distance)||!Number.isFinite(factor)||distance<=0||factor<=0||!Number.isFinite(maxDistance)||maxDistance<OBSERVATION_MIN_DISTANCE)throw new Error('Invalid zoom');
  // Zoom relative to altitude: never jump through the sphere at high magnification.
  return Math.min(maxDistance,Math.max(OBSERVATION_MIN_DISTANCE,1+(distance-1)*factor));
}
