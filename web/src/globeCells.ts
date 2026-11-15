interface AnnualCell {id:string;region:string;lat:number;lon:number;values:(number|null)[]}

type PointerPosition=Pick<PointerEvent,'pointerId'|'clientX'|'clientY'>;
type PointerPress=PointerPosition&Pick<PointerEvent,'button'|'isPrimary'>;

/** Only a completed single-pointer tap selects a cell; orbit/zoom gestures do not. */
export function createGlobeCellSelection() {
  const active=new Set<number>();
  let candidate:PointerPosition|null=null;
  const withinTap=(event:PointerPosition)=>candidate!==null&&Math.hypot(event.clientX-candidate.clientX,event.clientY-candidate.clientY)<=6;
  return {
    down(event:PointerPress) {
      active.add(event.pointerId);
      candidate=active.size===1&&event.button===0&&event.isPrimary
        ?{pointerId:event.pointerId,clientX:event.clientX,clientY:event.clientY}:null;
    },
    move(event:PointerPosition) {
      if(candidate?.pointerId===event.pointerId&&!withinTap(event))candidate=null;
    },
    up(event:PointerPress) {
      if(!active.has(event.pointerId))return false;
      const select=active.size===1&&candidate?.pointerId===event.pointerId&&event.button===0&&event.isPrimary&&withinTap(event);
      active.delete(event.pointerId);
      candidate=null;
      return select;
    },
    cancel(event:Pick<PointerEvent,'pointerId'>) {
      if(active.delete(event.pointerId))candidate=null;
    },
    reset() {active.clear();candidate=null;},
  };
}

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
