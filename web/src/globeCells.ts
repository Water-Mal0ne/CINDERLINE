interface AnnualCell {id:string;region:string;lat:number;lon:number;values:(number|null)[]}

/** One country record per geographic square; never add independently calibrated values. */
export function visibleGlobeCells<T extends AnnualCell>(cells:readonly T[],yearIndex:number,selectedRegion:string):T[] {
  const byCenter=new Map<string,T>();
  for(const cell of cells){
    const key=`${cell.lat}:${cell.lon}`,prior=byCenter.get(key);
    const selected=cell.region===selectedRegion,priorSelected=prior?.region===selectedRegion;
    if(!prior||(selected&&!priorSelected)||(selected===priorSelected&&
      (cell.region<prior.region||(cell.region===prior.region&&cell.id<prior.id))))byCenter.set(key,cell);
  }
  // Resolve identity first: missing selected-country values must not silently
  // become a neighboring country's value. Recorded zero is a visible value.
  return [...byCenter.values()].filter(cell=>{
    const value=cell.values[yearIndex];
    return typeof value==='number'&&Number.isFinite(value);
  });
}
