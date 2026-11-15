import {useEffect,useMemo,useRef,useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {Minus,Plus,RotateCcw} from 'lucide-react';
import ObservationControls,{useObservationDetail} from './ObservationControls';
import type {ObservationMode} from './ObservationControls';
import {loadObservationTiles,observationMonthLabel} from './observationDetail';
import type {ObservationGridCell,ObservationMonth,ObservationPoint} from './observationDetail';
import {boundedObservationZoom,OBSERVATION_MIN_DISTANCE,OBSERVATION_POINT_BUDGET,OBSERVATION_POINT_DISTANCE,pointInView,surfaceView,tileIntersectsView} from './observationViewport';
import type {ObservationView} from './observationViewport';
import {createDemandRenderer} from './demandRenderer';
import {createGlobeCellSelection} from './globeCells';
import './observation-earth.css';

const vector=(lat:number,lon:number,r=1)=>{
  const a=lat*Math.PI/180,b=lon*Math.PI/180;
  return new THREE.Vector3(r*Math.cos(a)*Math.sin(b),r*Math.sin(a),r*Math.cos(a)*Math.cos(b));
};
const location=(lat:number,lon:number)=>`${Math.abs(lat).toFixed(3)}° ${lat<0?'S':'N'}, ${Math.abs(lon).toFixed(3)}° ${lon<0?'W':'E'}`;
const format=(n:number)=>new Intl.NumberFormat('en').format(n);
interface ObservationScene {
  scene:THREE.Scene;camera:THREE.PerspectiveCamera;controls:OrbitControls;renderer:THREE.WebGLRenderer;
  layer:THREE.Mesh|THREE.Points|null;grid:ObservationGridCell[];points:ObservationPoint[];invalidate:()=>void;
}
const emptyView:ObservationView={lat:28,lon:84,distance:3.4,radiusDegrees:75};

export default function ObservationEarth({regionId,regionName,month,onMonth,onMode}:{regionId:string;regionName:string;month:string;onMonth:(month:string)=>void;onMode:(mode:ObservationMode)=>void}){
  const detail=useObservationDetail({enabled:true,country:regionId,month});
  const [view,setView]=useState<ObservationView>(emptyView),[tableMode,setTableMode]=useState(false),[fallbackReason,setFallbackReason]=useState('');
  const [selected,setSelected]=useState<ObservationPoint|null>(null),[gridPage,setGridPage]=useState(0),[pointPage,setPointPage]=useState(0),[tileAttempt,setTileAttempt]=useState(0);
  const [loaded,setLoaded]=useState<{key:string;points:ObservationPoint[];status:'loading'|'ready'|'error';error:string}>({key:'',points:[],status:'loading',error:''});
  const host=useRef<HTMLDivElement>(null),scene=useRef<ObservationScene|null>(null),dataRef=useRef<ObservationMonth|null>(null),focusedCountry=useRef('');
  const selectRef=useRef<(p:ObservationPoint)=>void>(()=>{}),zoomCellRef=useRef<(c:ObservationGridCell)=>void>(()=>{});
  dataRef.current=detail.monthData;selectRef.current=setSelected;
  const monthData=detail.monthData;
  const close=view.distance<=OBSERVATION_POINT_DISTANCE;
  const tiles=useMemo(()=>monthData&&close?monthData.tiles.filter(tile=>tileIntersectsView(tile.bounds,view)):[],[monthData,close,view]);
  const requestedCount=tiles.reduce((n,t)=>n+t.count,0),withinBudget=requestedCount<=OBSERVATION_POINT_BUDGET;
  const tileKey=monthData&&close&&withinBudget?`${regionId}:${month}:${tileAttempt}:${tiles.map(t=>t.id).join('|')}`:'';
  const current=loaded.key===tileKey?loaded:null;
  const nativePoints=!!tileKey&&current?.status==='ready';
  const nearby=useMemo(()=>nativePoints?current!.points.filter(p=>pointInView(p.lat,p.lon,view)):[],[nativePoints,current,view]);
  const grid=useMemo(()=>[...(monthData?.grid??[])].sort((a,b)=>b[2]-a[2]||a[0]-b[0]||a[1]-b[1]),[monthData]);
  const gridPages=Math.max(1,Math.ceil(grid.length/20)),pointPages=Math.max(1,Math.ceil(nearby.length/20));
  const safeGridPage=Math.min(gridPage,gridPages-1),safePointPage=Math.min(pointPage,pointPages-1);
  const zoomTo=(lat:number,lon:number,distance:number)=>{
    const s=scene.current;
    if(s){s.camera.position.copy(vector(lat,lon,distance));s.controls.target.set(0,0,0);s.controls.update();s.invalidate();}
    else setView(surfaceView(...vector(lat,lon,distance).toArray() as [number,number,number],39,.85));
  };
  zoomCellRef.current=cell=>{setSelected(null);zoomTo((cell[0]+.5)*.05,(cell[1]+.5)*.05,1.018);};
  const focusCountry=()=>{
    const data=dataRef.current;if(!data?.grid.length)return;
    const direction=data.grid.reduce((sum,c)=>sum.add(vector((c[0]+.5)*.05,(c[1]+.5)*.05)),new THREE.Vector3()).normalize();
    const extent=data.grid.reduce((max,c)=>Math.max(max,direction.angleTo(vector((c[0]+.5)*.05,(c[1]+.5)*.05))),0);
    const s=scene.current,aspect=s?.camera.aspect??.85,vertical=39*Math.PI/360;
    const halfFov=Math.min(vertical,Math.atan(Math.tan(vertical)*aspect));
    const distance=extent<Math.PI/2?Math.max(1.02,Math.min(5.5,Math.cos(extent)+Math.sin(extent)/Math.tan(halfFov*.85))):3.5;
    const center=surfaceView(...direction.clone().multiplyScalar(distance).toArray() as [number,number,number],39,aspect);
    zoomTo(center.lat,center.lon,distance);
  };
  useEffect(()=>{
    if(!tileKey||!monthData)return;const controller=new AbortController();
    setLoaded({key:tileKey,points:[],status:'loading',error:''});
    loadObservationTiles(monthData,tiles,controller.signal,{baseUrl:`${import.meta.env.BASE_URL}data/`,reload:tileAttempt>0})
      .then(points=>{if(!controller.signal.aborted)setLoaded({key:tileKey,points,status:'ready',error:''});})
      .catch(error=>{if(!controller.signal.aborted)setLoaded({key:tileKey,points:[],status:'error',error:error instanceof Error?error.message:'Nearby observations could not be loaded.'});});
    return()=>controller.abort();
    // Tile identity, month and retry completely identify the request. Camera-only movement does not refetch unchanged tiles.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[tileKey,monthData,tileAttempt]);
  useEffect(()=>{setSelected(null);setGridPage(0);setPointPage(0);},[regionId,month]);
  useEffect(()=>{if(monthData&&focusedCountry.current!==regionId){focusCountry();focusedCountry.current=regionId;}},[monthData,regionId,tableMode]);

  useEffect(()=>{
    if(tableMode||!host.current)return;const element=host.current;let renderer:THREE.WebGLRenderer;
    try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'low-power'});}catch{setFallbackReason('3D is unavailable. The observation grid and records remain available in the table.');setTableMode(true);return;}
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.75));renderer.setClearColor(0x0d1b23,1);element.appendChild(renderer.domElement);
    renderer.domElement.setAttribute('role','img');renderer.domElement.setAttribute('aria-label','Observed VIIRS Earth. Drag to rotate, scroll or use zoom buttons. Select a grid square to zoom into its observations.');
    const world=new THREE.Scene(),camera=new THREE.PerspectiveCamera(39,1,.0001,30);
    camera.position.copy(vector(view.lat,view.lon,view.distance));
    const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.1;controls.enablePan=false;controls.minDistance=OBSERVATION_MIN_DISTANCE;controls.maxDistance=6;controls.rotateSpeed=.4;controls.zoomSpeed=.35;
    const earth=new THREE.Mesh(new THREE.SphereGeometry(1,256,192),new THREE.MeshBasicMaterial({color:0x21414c}));world.add(earth);
    const loop=createDemandRenderer(()=>{const changed=controls.update();renderer.render(world,camera);return changed;},cb=>requestAnimationFrame(cb),id=>cancelAnimationFrame(id));
    let timer:ReturnType<typeof setTimeout>|undefined;
    const updateView=()=>{clearTimeout(timer);timer=setTimeout(()=>setView(surfaceView(camera.position.x,camera.position.y,camera.position.z,camera.fov,camera.aspect)),160);};
    const change=()=>{loop.invalidate();updateView();};controls.addEventListener('change',change);
    scene.current={scene:world,camera,controls,renderer,layer:null,grid:[],points:[],invalidate:()=>loop.invalidate()};
    const resize=()=>{renderer.setSize(Math.max(1,element.clientWidth),Math.max(1,element.clientHeight));camera.aspect=Math.max(1,element.clientWidth)/Math.max(1,element.clientHeight);camera.updateProjectionMatrix();change();};
    resize();const observer=new ResizeObserver(resize);observer.observe(element);
    let visible=false;const visibility=()=>loop.setActive(visible&&!document.hidden);
    const intersection=new IntersectionObserver(entries=>{visible=entries.some(e=>e.isIntersecting);visibility();});intersection.observe(element);document.addEventListener('visibilitychange',visibility);
    const controller=new AbortController();
    fetch(`${import.meta.env.BASE_URL}data/world-outline.json`,{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('Outline unavailable');return r.json();}).then(raw=>{
      if(controller.signal.aborted)return;const coords:number[]=[];
      for(const line of raw.geometry?.coordinates??raw.coordinates??[])for(let i=1;i<line.length;i++)if(Math.abs(line[i][0]-line[i-1][0])<=180)coords.push(...vector(line[i-1][1],line[i-1][0],1.00008).toArray(),...vector(line[i][1],line[i][0],1.00008).toArray());
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(coords,3));world.add(new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:0x8faea8,transparent:true,opacity:.65})));loop.invalidate();
    }).catch(()=>{/* Context outline is optional; observation fetches have their own visible errors. */});
    const gesture=createGlobeCellSelection(),ray=new THREE.Raycaster();
    const down=(e:PointerEvent)=>gesture.down(e),move=(e:PointerEvent)=>gesture.move(e),cancel=(e:PointerEvent)=>gesture.cancel(e);
    const up=(e:PointerEvent)=>{
      if(!gesture.up(e)||!scene.current?.layer)return;const rect=element.getBoundingClientRect();
      if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)return;
      ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),camera);
      ray.params.Points.threshold=Math.max(.000005,(camera.position.length()-1)*Math.tan(camera.fov*Math.PI/360)*12/rect.height);
      const hit=ray.intersectObject(scene.current.layer)[0],surface=ray.intersectObject(earth)[0];
      if(!hit||(surface&&hit.distance>surface.distance+.0005)||camera.position.dot(hit.point)<=hit.point.lengthSq())return;
      if(scene.current.layer instanceof THREE.Points&&hit.index!==undefined){const p=scene.current.points[hit.index];if(p)selectRef.current(p);}
      else if(hit.faceIndex!==undefined&&hit.faceIndex!==null){const cell=scene.current.grid[Math.floor(hit.faceIndex/2)];if(cell)zoomCellRef.current(cell);}
    };
    const contextLost=(e:Event)=>{e.preventDefault();setFallbackReason('The graphics connection was lost. Observation counts and records are available in the table.');setTableMode(true);};
    renderer.domElement.addEventListener('pointerdown',down);renderer.domElement.addEventListener('webglcontextlost',contextLost);
    document.addEventListener('pointermove',move);document.addEventListener('pointerup',up);document.addEventListener('pointercancel',cancel);window.addEventListener('blur',gesture.reset);
    if(dataRef.current)focusCountry();
    return()=>{clearTimeout(timer);controller.abort();observer.disconnect();intersection.disconnect();document.removeEventListener('visibilitychange',visibility);loop.dispose();controls.removeEventListener('change',change);controls.dispose();renderer.domElement.removeEventListener('pointerdown',down);renderer.domElement.removeEventListener('webglcontextlost',contextLost);document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',up);document.removeEventListener('pointercancel',cancel);window.removeEventListener('blur',gesture.reset);world.traverse(object=>{if(object instanceof THREE.Mesh||object instanceof THREE.Points||object instanceof THREE.LineSegments){object.geometry.dispose();const materials=Array.isArray(object.material)?object.material:[object.material];materials.forEach(m=>m.dispose());}});renderer.dispose();renderer.domElement.remove();scene.current=null;};
    // A scene survives month/country updates. Those change only the data layer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[tableMode]);

  useEffect(()=>{
    const s=scene.current;if(!s)return;
    if(s.layer){s.scene.remove(s.layer);s.layer.geometry.dispose();(s.layer.material as THREE.Material).dispose();s.layer=null;}
    s.points=[];s.grid=[];if(!monthData){s.invalidate();return;}
    const positions:number[]=[];
    if(nativePoints){
      s.points=current!.points;for(const p of s.points)positions.push(...vector(p.lat,p.lon,1.00025).toArray());
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
      const material=new THREE.ShaderMaterial({uniforms:{size:{value:5*s.renderer.getPixelRatio()}},transparent:true,depthWrite:false,
        vertexShader:'uniform float size; void main(){gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);gl_PointSize=size;}',
        fragmentShader:'void main(){float r=length(gl_PointCoord-vec2(.5));if(r>.5)discard;gl_FragColor=vec4(1.0,.69,.40,1.0-smoothstep(.35,.5,r));}'});
      s.layer=new THREE.Points(geometry,material);
    }else{
      const colors:number[]=[],maximum=monthData.grid.reduce((max,c)=>Math.max(max,c[2]),1);s.grid=monthData.grid;
      for(const c of s.grid){
        const lat=c[0]*.05,lon=c[1]*.05,color=new THREE.Color().setHSL(.105*(1-Math.log1p(c[2])/Math.log1p(maximum)),.76,.53);
        const corners=[vector(lat,lon,1.0002),vector(lat,lon+.05,1.0002),vector(lat+.05,lon+.05,1.0002),vector(lat+.05,lon,1.0002)];
        for(const i of [0,1,2,0,2,3]){positions.push(...corners[i].toArray());colors.push(color.r,color.g,color.b);}
      }
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
      s.layer=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide}));
    }
    s.scene.add(s.layer);s.invalidate();
  },[monthData,nativePoints,current,tableMode]);

  const zoom=(factor:number)=>{const s=scene.current;if(s){s.camera.position.setLength(boundedObservationZoom(s.camera.position.length(),factor,s.controls.maxDistance));s.controls.update();s.invalidate();}};
  const hint=close&&!withinBudget?`This view contains ${format(requestedCount)} nearby records. The complete grid remains visible; zoom closer to load individual detections without sampling.`:close&&nativePoints?'Each marker is one archived observation; multiple observations may overlap.':'Select a grid square to zoom into that area. The grid shows observed counts, not harmonized estimates.';
  const retry=()=>{setTileAttempt(n=>n+1);detail.retry();};
  return <div className="earth-explorer earth-workspace observation-earth">
    <div className="globe-heading"><div><span className="eyebrow">A closer look at the observations</span><h2>Where the satellite detected heat</h2></div><div className="globe-view-actions"><button type="button" className="chart-scale-button" onClick={focusCountry} disabled={!monthData?.grid.length}>Focus {regionName}</button><button type="button" className="chart-scale-button" onClick={()=>{setFallbackReason('');setTableMode(v=>!v);}} aria-pressed={tableMode}>{tableMode?'Show 3D Earth':'Observation table'}</button></div></div>
    <ObservationControls sourceUrl={detail.index?.countries.find(c=>c.id===regionId)?.source.url} mode="observations" onMode={onMode} month={month} onMonth={onMonth} regionName={regionName} status={detail.status} error={detail.error} onRetry={retry} availableMonths={detail.availableMonths} pointCount={monthData?.count} display={nativePoints?'points':'grid'} detailLoading={!!tileKey&&current?.status!=='ready'&&current?.status!=='error'} detailError={current?.error} loadedPointCount={current?.points.length} detailHint={hint} selectedPoint={selected?.id.startsWith(`${regionId}:${month}:`)?selected:null} onClearSelection={()=>setSelected(null)}>
    {fallbackReason&&<p className="chart-note" role="status">{fallbackReason}</p>}
    {!tableMode&&<div className="globe-stage observation-stage"><div className="globe-canvas" ref={host}/><div className="globe-instructions">Drag to orbit · zoom or select a grid square for detail</div><div className="globe-buttons"><button type="button" aria-label="Zoom into observations" onClick={()=>zoom(.55)}><Plus size={16}/></button><button type="button" aria-label="Zoom out from observations" onClick={()=>zoom(1.8)}><Minus size={16}/></button><button type="button" aria-label="Refocus observation country" onClick={focusCountry}><RotateCcw size={15}/></button></div><div className="observation-map-key">{nativePoints?'Individual VIIRS pixel centres':'Observed detections · 0.05° grid'}<span>{observationMonthLabel(month)} · UTC · {regionName}</span>{!nativePoints&&<span>Colour: log count within this month and country; empty areas have no qualifying records, not proven absence of fire.</span>}</div></div>}
    {tableMode&&monthData&&<section className="observation-grid-table" aria-label="Observed detection grid"><p>{format(grid.length)} occupied 0.05° cells in {regionName}, {observationMonthLabel(month)}. Selecting a cell loads its nearby observation records.</p><div className="table-scroll"><table><caption className="sr-only">Observed VIIRS grid counts, UTC month</caption><thead><tr><th>Grid centre</th><th>Observed detections</th><th>Detail</th></tr></thead><tbody>{grid.slice(safeGridPage*20,(safeGridPage+1)*20).map(c=><tr key={`${c[0]}:${c[1]}`}><td>{location((c[0]+.5)*.05,(c[1]+.5)*.05)}</td><td>{format(c[2])}</td><td><button className="text-button" onClick={()=>zoomCellRef.current(c)}>Inspect observations</button></td></tr>)}</tbody></table></div><nav className="globe-pagination" aria-label="Observed grid pages"><button className="chart-scale-button" disabled={safeGridPage===0} onClick={()=>setGridPage(safeGridPage-1)}>Previous cells</button><span>{safeGridPage+1} / {gridPages}</span><button className="chart-scale-button" disabled={safeGridPage+1===gridPages} onClick={()=>setGridPage(safeGridPage+1)}>Next cells</button></nav></section>}
    </ObservationControls>
    {nativePoints&&<details className="observation-records" open={tableMode||undefined}><summary>Inspect nearby observation records ({format(nearby.length)})</summary><p>Records within the view’s enclosing area. Multiple satellite passes can observe the same fire.</p><div className="table-scroll"><table><caption className="sr-only">Nearby observed VIIRS records</caption><thead><tr><th>Pixel centre</th><th>Acquired (UTC)</th><th>Evidence</th></tr></thead><tbody>{nearby.slice(safePointPage*20,(safePointPage+1)*20).map(p=><tr key={p.id}><td>{location(p.lat,p.lon)}</td><td>{p.utc.replace('T',' ').replace(':00Z','')}</td><td><button className="text-button" aria-label={`Inspect observation ${p.utc} at ${location(p.lat,p.lon)}`} onClick={()=>setSelected(p)}>Inspect</button></td></tr>)}</tbody></table></div><nav className="globe-pagination" aria-label="Observation record pages"><button className="chart-scale-button" disabled={safePointPage===0} onClick={()=>setPointPage(safePointPage-1)}>Previous records</button><span>{safePointPage+1} / {pointPages}</span><button className="chart-scale-button" disabled={safePointPage+1===pointPages} onClick={()=>setPointPage(safePointPage+1)}>Next records</button></nav></details>}
  </div>;
}
