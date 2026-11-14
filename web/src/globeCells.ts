interface AnnualCell {id:string;region:string;lat:number;lon:number;values:(number|null)[]}

export const localGlobeCellId=(cell:AnnualCell)=>cell.id.startsWith(`${cell.region}:`)?cell.id.slice(cell.region.length+1):cell.id;

/** Annual table rows remain country-specific, including shared border centers. */
export function filterGlobeTableCells<T extends AnnualCell>(cells:readonly T[],yearIndex:number,region:string,dailyIds:readonly string[],dailyOnly=false,query=''):T[] {
  const available=new Set(dailyIds),terms=query.toLowerCase().trim().split(/[\s,°/]+/).filter(Boolean);
  return cells.filter(cell=>{
    const value=cell.values[yearIndex];
    if(cell.region!==region||typeof value!=='number'||!Number.isFinite(value))return false;
    if(dailyOnly&&!available.has(localGlobeCellId(cell)))return false;
    const coordinates=[cell.lat.toFixed(3),cell.lon.toFixed(3),Math.abs(cell.lat).toFixed(3),cell.lat<0?'s':'n',Math.abs(cell.lon).toFixed(3),cell.lon<0?'w':'e'];
    return terms.every(term=>coordinates.some(coordinate=>coordinate.startsWith(term)));
  }).sort((a,b)=>b.values[yearIndex]!-a.values[yearIndex]!||a.id.localeCompare(b.id));
}

export function globeTablePage<T>(cells:readonly T[],requestedPage:number,pageSize=20) {
  const pages=Math.max(1,Math.ceil(cells.length/pageSize));
  const page=Math.max(0,Math.min(Number.isFinite(requestedPage)?Math.floor(requestedPage):0,pages-1));
  return {page,pages,rows:cells.slice(page*pageSize,(page+1)*pageSize),first:cells.length?page*pageSize+1:0,last:Math.min((page+1)*pageSize,cells.length)};
}

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
