import {useEffect,useMemo,useRef,useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {ArrowUpRight,Globe2,Minus,Plus,RotateCcw} from 'lucide-react';
import {compact,fmt,numeric} from './utils';
import {invalidateData,loadData} from './loadData';
import {validGlobeData} from './globeData';
import {applyCalendarAlignment,annualCalendarCoverage} from './calendarAlignment';
import ReliabilityNotice from './ReliabilityNotice';
import type {GlobeCell,GlobeData} from './globeData';
import {createDemandRenderer} from './demandRenderer';
import {globeOverviewDistance} from './globeViewport';
import {createGlobeCellSelection,filterGlobeTableCells,globeTablePage,localGlobeCellId,visibleGlobeCells} from './globeCells';
import './globe.css';

interface Outline {type:string;coordinates:number[][][];geometry?:{type:string;coordinates:number[][][]}}
interface SceneState {renderer:THREE.WebGLRenderer;scene:THREE.Scene;camera:THREE.PerspectiveCamera;controls:OrbitControls;heat:THREE.Mesh|null;cells:GlobeCell[];max:number;requestRender:()=>void}
let cachedData:GlobeData|null=null;
const point=(lat:number,lon:number,r=1)=>{const a=THREE.MathUtils.degToRad(lat),b=THREE.MathUtils.degToRad(lon);return new THREE.Vector3(r*Math.cos(a)*Math.sin(b),r*Math.sin(a),r*Math.cos(a)*Math.cos(b));};

export default function Globe({regionId,year:requestedYear,onYear,onRegion,onCell,availableCells}:{regionId:string;year:number;onYear:(year:number)=>void;onRegion:(id:string,year:number)=>void;onCell:(id:string,year:number)=>void;availableCells:string[]}) {
  const [data,setData]=useState<GlobeData|null>(cachedData),[error,setError]=useState(''),[fallback,setFallback]=useState(false),[selected,setSelected]=useState<GlobeCell|null>(null);
  const [fallbackReason,setFallbackReason]=useState('');
  const [loadAttempt,setLoadAttempt]=useState(0),[tablePage,setTablePage]=useState(0),[tableQuery,setTableQuery]=useState(''),[dailyOnly,setDailyOnly]=useState(false);
  const selectionPanel=useRef<HTMLDivElement>(null);
  const host=useRef<HTMLDivElement>(null),state=useRef<SceneState|null>(null),selectedRef=useRef<(cell:GlobeCell)=>void>(()=>{});
  const year=data?.years.includes(requestedYear)?requestedYear:data?.years[data.years.length-1]||requestedYear;
  const yearIndex=data?.years.indexOf(year)??-1;
  const colorMaximum=useMemo(()=>data?.cells.reduce((max,cell)=>cell.values.reduce<number>((m,v)=>numeric(v)?Math.max(m,v):m,max),1)||1,[data]);
  selectedRef.current=setSelected;
  useEffect(()=>{
    if(cachedData){setData(cachedData);return;}
    setError('');const c=new AbortController();
    Promise.all([loadData<unknown>('globe.json',c.signal),loadData<unknown>('calendar-alignment.json',c.signal)])
      .then(async([source,alignment])=>{
        if(c.signal.aborted)return;
        if(!validGlobeData(source))throw new Error('Invalid annual globe data');
        const aligned=await applyCalendarAlignment(source,alignment);
        if(c.signal.aborted)return;
        cachedData=aligned;setData(aligned);
      }).catch(()=>{
        if(!c.signal.aborted)setError('The annual globe layer could not be loaded or its calendar alignment could not be verified. The calendar and evidence remain available below.');
      });
    return()=>c.abort();
  },[loadAttempt]);
  useEffect(()=>{
    if(!data||!host.current||fallback)return;
    const element=host.current;let renderer:THREE.WebGLRenderer;
    try {renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'low-power'});}catch{setFallbackReason('3D rendering is unavailable on this device. The grid table provides the same annual values.');setFallback(true);return;}
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.75));renderer.setClearColor(0x0d1b23,1);element.appendChild(renderer.domElement);
    renderer.domElement.setAttribute('aria-label','Interactive three-dimensional Earth. Drag to rotate, scroll to zoom, or use the annual grid table.');renderer.domElement.setAttribute('role','img');
    const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(39,1,.05,30);camera.position.set(0,0,3.4);
    const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;controls.enablePan=false;controls.minDistance=1.2;controls.maxDistance=5.5;controls.rotateSpeed=.55;controls.zoomSpeed=.55;
    const renderLoop=createDemandRenderer(()=>{const changed=controls.update();renderer.render(scene,camera);return changed;},callback=>requestAnimationFrame(callback),id=>cancelAnimationFrame(id));
    const requestRender=()=>renderLoop.invalidate();
    controls.addEventListener('change',requestRender);
    const earth=new THREE.Mesh(new THREE.SphereGeometry(1,96,64),new THREE.MeshPhongMaterial({color:0x39606c,shininess:3,specular:0x16343c}));earth.rotation.y=-Math.PI/2;scene.add(earth);
    scene.add(new THREE.AmbientLight(0xb8d6d6,1.7));const sun=new THREE.DirectionalLight(0xffe4bb,1.7);sun.position.set(4,3,5);scene.add(sun);
    const graticule:number[]=[];const pushLine=(coords:THREE.Vector3[])=>{for(let i=1;i<coords.length;i++)graticule.push(...coords[i-1].toArray(),...coords[i].toArray());};
    for(let lat=-60;lat<=60;lat+=30)pushLine(Array.from({length:181},(_,i)=>point(lat,i*2-180,1.002)));
    for(let lon=-180;lon<180;lon+=30)pushLine(Array.from({length:91},(_,i)=>point(i*2-90,lon,1.002)));
    const gridGeometry=new THREE.BufferGeometry();gridGeometry.setAttribute('position',new THREE.Float32BufferAttribute(graticule,3));scene.add(new THREE.LineSegments(gridGeometry,new THREE.LineBasicMaterial({color:0x54727b,transparent:true,opacity:.22})));
    const controller=new AbortController();fetch(`${import.meta.env.BASE_URL}data/world-outline.json`,{signal:controller.signal}).then(r=>r.ok?r.json():null).then((outline:Outline|null)=>{if(!outline||controller.signal.aborted)return;const lines=outline.geometry?.coordinates||outline.coordinates;const positions:number[]=[];for(const line of lines||[]){for(let i=1;i<line.length;i++){if(Math.abs(line[i][0]-line[i-1][0])>180)continue;positions.push(...point(line[i-1][1],line[i-1][0],1.003).toArray(),...point(line[i][1],line[i][0],1.003).toArray());}}const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));scene.add(new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:0x9fc0b9,transparent:true,opacity:.5})));requestRender();}).catch(()=>{});
    let landTexture:THREE.CanvasTexture|null=null;
    fetch(`${import.meta.env.BASE_URL}data/world-land.json`,{signal:controller.signal}).then(r=>r.ok?r.json():null).then(raw=>{
      if(!raw||controller.signal.aborted)return;const canvas=document.createElement('canvas');canvas.width=2048;canvas.height=1024;const ctx=canvas.getContext('2d');if(!ctx)return;
      ctx.fillStyle='#426b77';ctx.fillRect(0,0,2048,1024);ctx.fillStyle='#526f61';
      const geometries=raw.type==='FeatureCollection'?raw.features.map((f:{geometry:unknown})=>f.geometry):[raw.geometry||raw];
      for(const g of geometries){const polygons=g.type==='Polygon'?[g.coordinates]:g.coordinates;if(!Array.isArray(polygons))continue;for(const polygon of polygons){ctx.beginPath();for(const ring of polygon){let lastX:number|null=null;ring.forEach(([lon,lat]:number[],i:number)=>{const x=(lon+180)/360*2048,y=(90-lat)/180*1024;if(i===0||lastX!==null&&Math.abs(x-lastX)>1024)ctx.moveTo(x,y);else ctx.lineTo(x,y);lastX=x;});ctx.closePath();}ctx.fill('evenodd');}}
      landTexture=new THREE.CanvasTexture(canvas);landTexture.colorSpace=THREE.SRGBColorSpace;earth.material.map=landTexture;earth.material.color.setHex(0xffffff);earth.material.needsUpdate=true;
      requestRender();
    }).catch(()=>{});
    state.current={renderer,scene,camera,controls,heat:null,cells:[],max:1,requestRender};
    const resize=()=>{
      const width=Math.max(element.clientWidth,1),height=Math.max(element.clientHeight,1);
      const previousFit=globeOverviewDistance(camera.fov,camera.aspect);
      renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();
      const nextFit=globeOverviewDistance(camera.fov,camera.aspect);
      // Preserve the user's relative zoom when the available canvas changes.
      camera.position.multiplyScalar(nextFit/previousFit);controls.maxDistance=Math.max(5.5,nextFit*1.5);
      controls.update();requestRender();
    };resize();const observer=new ResizeObserver(resize);observer.observe(element);
    let inViewport=false;
    const updateVisibility=()=>renderLoop.setActive(inViewport&&!document.hidden);
    const intersection=new IntersectionObserver(entries=>{inViewport=entries.some(entry=>entry.isIntersecting);updateVisibility();});intersection.observe(element);
    document.addEventListener('visibilitychange',updateVisibility);
    const contextLost=(event:Event)=>{event.preventDefault();renderLoop.setActive(false);setFallbackReason('The 3D view lost its graphics connection. Your data is preserved in the grid table; you can try 3D Earth again.');setFallback(true);};
    renderer.domElement.addEventListener('webglcontextlost',contextLost);
    const ray=new THREE.Raycaster(),pointer=new THREE.Vector2(),selectionGesture=createGlobeCellSelection();
    const pointerDown=(e:PointerEvent)=>selectionGesture.down(e);
    const pointerMove=(e:PointerEvent)=>selectionGesture.move(e);
    const pointerCancel=(e:PointerEvent)=>selectionGesture.cancel(e);
    const pointerUp=(e:PointerEvent)=>{if(!selectionGesture.up(e)||!state.current?.heat)return;const rect=renderer.domElement.getBoundingClientRect();if(!rect.width||!rect.height||e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)return;pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);const hit=ray.intersectObject(state.current.heat)[0],surface=ray.intersectObject(earth)[0];if(hit&&surface&&hit.distance>surface.distance+.02)return;if(hit?.faceIndex!==undefined&&hit.faceIndex!==null){const cell=state.current.cells[Math.floor(hit.faceIndex/2)];if(cell)selectedRef.current(cell);}};
    // A second touch can end outside the canvas. Track completion on the document
    // so that a finished pinch cannot leave the next tap blocked or select a cell.
    renderer.domElement.addEventListener('pointerdown',pointerDown);document.addEventListener('pointermove',pointerMove);document.addEventListener('pointerup',pointerUp);document.addEventListener('pointercancel',pointerCancel);window.addEventListener('blur',selectionGesture.reset);
    return()=>{controller.abort();renderLoop.dispose();observer.disconnect();intersection.disconnect();document.removeEventListener('visibilitychange',updateVisibility);controls.removeEventListener('change',requestRender);controls.dispose();landTexture?.dispose();renderer.domElement.removeEventListener('webglcontextlost',contextLost);renderer.domElement.removeEventListener('pointerdown',pointerDown);document.removeEventListener('pointermove',pointerMove);document.removeEventListener('pointerup',pointerUp);document.removeEventListener('pointercancel',pointerCancel);window.removeEventListener('blur',selectionGesture.reset);selectionGesture.reset();scene.traverse(object=>{if(object instanceof THREE.Mesh||object instanceof THREE.LineSegments){object.geometry.dispose();const mats=Array.isArray(object.material)?object.material:[object.material];mats.forEach(m=>m.dispose());}});renderer.dispose();renderer.domElement.remove();state.current=null;};
  },[data,fallback]);
  useEffect(()=>{
    const s=state.current;if(!s||!data||yearIndex<0)return;
    if(s.heat){s.scene.remove(s.heat);s.heat.geometry.dispose();(s.heat.material as THREE.Material).dispose();}
    const cells=visibleGlobeCells(data.cells,yearIndex,regionId);const max=colorMaximum;
    const positions:number[]=[],colors:number[]=[],half=data.cell_size/2;
    for(const c of cells){const value=c.values[yearIndex]!,t=Math.log1p(Math.max(0,value))/Math.log1p(max);const color=value===0?new THREE.Color('#52666a'):new THREE.Color().setHSL(.105*(1-t),.47+.42*t,.17+.45*t);const corners=[point(c.lat-half,c.lon-half,1.007),point(c.lat-half,c.lon+half,1.007),point(c.lat+half,c.lon+half,1.007),point(c.lat+half,c.lon-half,1.007)];for(const i of [0,1,2,0,2,3]){positions.push(...corners[i].toArray());colors.push(color.r,color.g,color.b);}}
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    const heat=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide}));s.scene.add(heat);s.heat=heat;s.cells=cells;s.max=max;
    s.requestRender();
  },[data,yearIndex,regionId,fallback,colorMaximum]);
  function focus(close=false){
    const s=state.current;if(!s||!data)return;
    const cells=data.cells.filter(c=>c.region===regionId);if(!cells.length)return;
    // Average on the sphere so a region crossing the date line stays centered.
    const direction=cells.reduce((sum,c)=>sum.add(point(c.lat,c.lon)),new THREE.Vector3()).normalize();
    if(direction.lengthSq()===0)return;
    let distance=globeOverviewDistance(s.camera.fov,s.camera.aspect);
    if(close){
      const extent=cells.reduce((angle,c)=>Math.max(angle,direction.angleTo(point(c.lat,c.lon))),0)+THREE.MathUtils.degToRad(data.cell_size/Math.SQRT2);
      const vertical=THREE.MathUtils.degToRad(s.camera.fov)/2;
      const halfFov=Math.min(vertical,Math.atan(Math.tan(vertical)*s.camera.aspect));
      // Fit the occupied cells in the narrower canvas dimension, with margin.
      // Very dispersed regions keep a global view rather than an arbitrary close-up.
      if(extent<Math.PI/2){
        const fit=Math.cos(extent)+Math.sin(extent)/Math.tan(halfFov*.88);
        const horizon=1.015/Math.cos(extent);
        distance=THREE.MathUtils.clamp(Math.max(fit,horizon)*1.007,s.controls.minDistance,s.controls.maxDistance);
      }
    }
    s.camera.position.copy(direction.multiplyScalar(distance));s.controls.target.set(0,0,0);s.controls.update();s.requestRender();
  }
  useEffect(()=>{focus(false);},[data,regionId,fallback]);
  useEffect(()=>{setSelected(null);},[data,regionId]);
  const regionCells=useMemo(()=>filterGlobeTableCells(data?.cells||[],yearIndex,regionId,availableCells,dailyOnly,tableQuery),[data,regionId,yearIndex,availableCells,dailyOnly,tableQuery]);
  const table=globeTablePage(regionCells,tablePage);
  useEffect(()=>setTablePage(0),[regionId,yearIndex,dailyOnly,tableQuery]);
  const regionInfo=data?.coverage_regions.find(r=>r.id===regionId);const chosen=selected&&numeric(selected.values[yearIndex])?selected:null;
  const chosenRegionInfo=data?.coverage_regions.find(r=>r.id===chosen?.region);
  const coverageNames=data?.coverage_regions.map(r=>r.name)||[];
  const coverageSummary=coverageNames.length>3?`${coverageNames.length} countries`:coverageNames.join(' + ');
  const chosenId=chosen?localGlobeCellId(chosen):undefined;
  const annualCoverage=data?annualCalendarCoverage(data,regionId,year):null;
  const exactCenter=(cell:GlobeCell)=>`${Math.abs(cell.lat).toFixed(3)}° ${cell.lat<0?'S':'N'}, ${Math.abs(cell.lon).toFixed(3)}° ${cell.lon<0?'W':'E'}`;
  const inspectTableCell=(cell:GlobeCell)=>{setSelected(cell);requestAnimationFrame(()=>selectionPanel.current?.focus());};
  if(error)return <div className="globe-unavailable"><Globe2 size={24}/><p role="alert">{error}</p><button className="button subtle" onClick={()=>{invalidateData('globe.json');invalidateData('calendar-alignment.json');setLoadAttempt(attempt=>attempt+1);}}>Retry annual globe layer</button></div>;
  if(!data)return <div className="globe-unavailable" role="status"><span className="loader"/><p>Loading annual grid observations…</p></div>;
  return <div className="earth-explorer"><div className="globe-heading"><div><span className="eyebrow">A GEOGRAPHIC VIEW OF THE RECORD</span><h2>Where the signal comes from.</h2></div><div className="globe-view-actions">{!fallback&&<button className="chart-scale-button" onClick={()=>focus(true)}>Focus {regionInfo?.name||regionId}</button>}<button className="chart-scale-button" onClick={()=>{setFallbackReason('' );setFallback(v=>!v);}} aria-pressed={fallback}>{fallback?'Show 3D Earth':'Grid table'}</button></div></div>
    {fallbackReason&&<p className="chart-note" role="status">{fallbackReason}</p>}<div className="globe-body">{!fallback?<div className="globe-stage"><div className="globe-canvas" ref={host}/><div className="globe-instructions">Drag to orbit · scroll to zoom · select a colored cell</div><div className="globe-buttons"><button aria-label="Zoom into Earth" onClick={()=>{const s=state.current;if(s){s.camera.position.multiplyScalar(.85);s.requestRender();}}}><Plus size={16}/></button><button aria-label="Zoom out from Earth" onClick={()=>{const s=state.current;if(s){s.camera.position.multiplyScalar(1.2);s.requestRender();}}}><Minus size={16}/></button><button aria-label="Refocus selected region" onClick={()=>focus(false)}><RotateCcw size={15}/></button><button aria-label="Show global view" onClick={()=>{const s=state.current;if(s){s.camera.position.normalize().multiplyScalar(globeOverviewDistance(s.camera.fov,s.camera.aspect));s.controls.update();s.requestRender();}}}><Globe2 size={15}/></button></div><div className="globe-coverage">PROCESSED COVERAGE ONLY<br/><strong>{coverageSummary}</strong><span>Uncolored areas are not claims of no fire.</span>{chosen&&<button type="button" className="chart-scale-button globe-selection-shortcut" aria-controls="globe-cell-selection" aria-label={`Inspect selected cell ${exactCenter(chosen)}, ${chosenRegionInfo?.name||chosen.region}`} onClick={()=>selectionPanel.current?.focus()}>Inspect selected cell</button>}</div></div>:<div className="globe-table">
      <p>Annual grid cells in {regionInfo?.name||regionId}, {year}, ordered by activity. Values cover available observations.</p>
      <div className="globe-table-filters"><label>Find grid center<input type="search" value={tableQuery} onChange={event=>setTableQuery(event.target.value)} placeholder="Latitude or longitude…"/></label><label className="globe-daily-filter"><input type="checkbox" checked={dailyOnly} onChange={event=>setDailyOnly(event.target.checked)}/> With a daily record</label></div>
      <p className="globe-table-count" role="status">{fmt(regionCells.length)} matching annual cells{regionCells.length>0&&` · showing ${table.first}–${table.last}`}. Daily records are available for {availableCells.length} selected cells in this region.</p>
      <div className="table-scroll" tabIndex={0} role="group" aria-label="Annual grid table"><table><caption className="sr-only">Annual Aqua-reference-equivalent grid detections in {regionInfo?.name||regionId}, {year}</caption><thead><tr><th scope="col">Grid center</th><th scope="col">Aqua-reference-equivalent</th><th scope="col">Evidence</th></tr></thead><tbody>{table.rows.map(c=><tr key={c.id} className={chosen?.id===c.id?'globe-row-selected':undefined}><td>{exactCenter(c)}{availableCells.includes(localGlobeCellId(c))&&<span className="globe-daily-badge">Daily record</span>}</td><td>{fmt(c.values[yearIndex],1)}</td><td><button className="text-button" aria-label={`Inspect grid cell ${exactCenter(c)}`} aria-pressed={chosen?.id===c.id} onClick={()=>inspectTableCell(c)}>{chosen?.id===c.id?'Selected':'Inspect cell'}</button></td></tr>)}</tbody></table></div>
      {regionCells.length===0&&<div className="globe-table-empty"><p>No annual cells match these filters. Try another coordinate or include all annual cells.</p><button className="chart-scale-button" onClick={()=>{setTableQuery('');setDailyOnly(false);}}>Clear grid filters</button></div>}
      <nav className="globe-pagination" aria-label="Annual grid table pages"><button className="chart-scale-button" disabled={table.page===0} onClick={()=>setTablePage(table.page-1)}>Previous cells</button><span>Page {table.page+1} of {table.pages}</span><button className="chart-scale-button" disabled={table.page===table.pages-1} onClick={()=>setTablePage(table.page+1)}>Next cells</button></nav>
    </div>}
    <div className="globe-detail"><div className="globe-year-control"><span className="eyebrow">ANNUAL ACTIVITY</span><label className="globe-year" htmlFor="globe-year">{year}</label><input id="globe-year" aria-label="Globe year; updates calendar date range" aria-valuetext={String(year)} type="range" min="0" max={data.years.length-1} step="1" value={yearIndex} onChange={e=>onYear(data.years[Number(e.target.value)])}/><div className="year-range"><span>{data.years[0]}</span><span>{data.years[data.years.length-1]}</span></div><p className="globe-year-note">Choosing a year also filters the calendar below.</p></div><div className="globe-legend"><div className="globe-scale"><span>LOW</span><i/><span>HIGH</span></div><small>Fixed all-year log scale · annual Aqua-reference-equivalent detections · {data.cell_size}° cells · maximum {fmt(colorMaximum,1)}</small><div className="globe-zero-key"><i/> 0 recorded <span>Uncolored = no processed value</span></div><div className="globe-source"><span>SOURCE FOR {regionInfo?.name||regionId}</span><strong>{regionInfo?.sources?.[yearIndex]||'See daily evidence for source'}</strong></div></div></div>
      {chosen?<div className="globe-selection" id="globe-cell-selection" ref={selectionPanel} tabIndex={-1} role="region" aria-label={`Selected grid cell ${exactCenter(chosen)}, ${chosenRegionInfo?.name||chosen.region}`}><div className="globe-selection-values"><span>SELECTED GRID CELL · {chosenRegionInfo?.name||chosen.region.replaceAll('_',' ')}</span><strong>{exactCenter(chosen)}</strong><b>{compact(chosen.values[yearIndex])}</b><small>{fmt(chosen.values[yearIndex],1)} Aqua-reference-equivalent detections in {year}</small><small>Source: {chosenRegionInfo?.sources?.[yearIndex]||'See daily evidence for this region'}</small></div><div className="globe-selection-evidence"><ReliabilityNotice regionName={chosenRegionInfo?.name||chosen.region.replaceAll('_',' ')} regionId={chosen.region} cellId={chosenId} scope="annual" start={`${year}-01-01`} end={`${year}-12-31`}/><p className="globe-outage-notice">Annual totals sum the available daily values with the same supplier-outage exclusions. Weekly and monthly calendars omit outage-affected bins, so their displayed sums can differ.</p>{chosen.region===regionId&&availableCells.includes(chosenId||'')?<button className="button subtle full" onClick={()=>onCell(chosenId!,year)}>Open {year} daily record <ArrowUpRight size={13}/></button>:<><p>Annual grid summary. Daily drill-down is available for a selected subset of cells.</p><button className="button subtle full" onClick={()=>onRegion(chosen.region,year)}>Open {year} region calendar <ArrowUpRight size={13}/></button></>}</div></div>:<div className="globe-selection globe-selection-empty"><span>FOLLOW THE EVIDENCE</span><p>Select a colored cell on Earth, or use the grid table to inspect exact values.</p></div>}
    </div>{annualCoverage&&<details className="globe-outage-notice"><summary>{annualCoverage.retained_dates} of {annualCoverage.calendar_dates} calendar dates retained in {year}{annualCoverage.excluded_dates.length>0?` · ${annualCoverage.excluded_dates.length} outage dates excluded`:''}</summary><p>Annual values use the daily calendar's supplier-outage exclusions. Retained dates are not a measure of cloud-free satellite coverage. Weekly and monthly calendar totals omit bins affected by an outage.</p>{annualCoverage.excluded_dates.length>0&&<p>Excluded dates: {annualCoverage.excluded_dates.join(', ')}.</p>}<p>Custom-area monthly data omit entire outage-affected months and round each cell's values, so their sums can differ.</p></details>}{coverageNames.length>3&&<p className="chart-note globe-regions"><strong>Processed regions:</strong> {coverageNames.join(', ')}.</p>}<p className="chart-note">Shared border squares prioritize the selected country; otherwise country order is used. Switch country to see its values. Overlapping country records are not combined.</p><p className="chart-note">Annual sums are not burned area or distinct fires. Satellite observation coverage remains unknown; the heatmap shows only processed regions.</p><span className="chart-label">{data.label}</span>
  </div>;
}
