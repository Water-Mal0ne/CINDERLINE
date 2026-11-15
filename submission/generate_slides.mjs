/** Build the judging deck from SLIDES.md without changing scientific copy.
 * Requires @oai/artifact-tool and the presentation skill finalizer.
 * Example: node submission/generate_slides.mjs --modules NODE_MODULES --skill SKILL_DIR --python PYTHON
 * Outputs are validated before copying to the requested submission paths.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';

const here=path.dirname(fileURLToPath(import.meta.url)), repo=path.dirname(here);
const args=Object.fromEntries(process.argv.slice(2).reduce((rows,value,index,list)=>index%2?rows:[...rows,[value.replace(/^--/,''),list[index+1]]],[]));
if(!args.modules||!args.skill||!args.python) throw new Error('Provide --modules, --skill and --python runtime paths.');
process.env.RUNTIME_NODE_MODULES=path.resolve(args.modules);
const resolve=createRequire(path.join(path.resolve(args.modules),'firetrace-resolve.cjs'));
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(resolve.resolve('@oai/artifact-tool')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(path.resolve(args.skill),'container_tools/artifact_tool_utils.mjs')).href);
const W=1280,H=720,C={bg:'#111b20',panel:'#18252b',text:'#f2eee5',muted:'#aebdc0',orange:'#f79963',line:'#42575e'};
const clean=text=>text.replace(/\*\*|`/g,'').replace(/^[-*] /gm,'').trim();
const words=text=>clean(text).match(/\S+/g)?.length||0;
const markdown=(await fs.readFile(path.join(here,'SLIDES.md'),'utf8')).replace(/\r\n?/g,'\n');
const slides=[...markdown.matchAll(/^## Slide (\d+) [—-] (.+)\r?\n([\s\S]*?)(?=^## Slide |$(?![\s\S]))/gm)].map(match=>{
  const sections=Object.fromEntries([...match[3].matchAll(/^### (.+)\r?\n([\s\S]*?)(?=^### |$(?![\s\S]))/gm)].map(m=>[m[1],m[2].trim()]));
  const raw=sections['On-slide text']||'',tableLines=raw.split('\n').filter(line=>line.startsWith('|'));
  const table=tableLines.filter(line=>!/^\|[\s:|-]+\|$/.test(line)).map(line=>line.split('|').slice(1,-1).map(clean));
  const prose=clean(raw.split('\n').filter(line=>!line.startsWith('|')).join('\n'));
  const title=clean(match[2]),notes=sections['Speaker notes']||'';
  const count=words([title,prose,...table.flat()].join(' '))+(Number(match[1])===1?1:0);
  if(count>40)throw new Error(`Slide ${match[1]} has ${count} authored words.`);
  if(words(notes)<60||words(notes)>90)throw new Error(`Slide ${match[1]} has ${words(notes)} spoken-note words.`);
  return {number:Number(match[1]),title,prose,table,notes,sources:sections.Sources||'',visual:sections.Visual||'',authoredWords:count,spokenWords:words(notes)};
});
if(slides.length!==7||slides.some((s,i)=>s.number!==i+1))throw new Error('Expected exactly seven sequential Slide sections.');
const stamp=new Date().toISOString().replace(/[:.]/g,'-'), build=path.join(repo,'.deck-build',stamp), rendered=path.join(build,'rendered');
await fs.mkdir(rendered,{recursive:true});
const deck=Presentation.create({slideSize:{width:W,height:H}}), evidence=[];
const txt=(slide,text,x,y,w,h,size=30,color=C.text,bold=false)=>{
  const shape=slide.shapes.add({geometry:'textbox',name:text.slice(0,70),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  shape.text=clean(text);shape.text.style={typeface:'Arial',fontSize:size,bold,color,wrap:'square',autoFit:'none',verticalAlignment:'top',insets:0};
  return shape;
};
async function picture(slide,relative,x,y,w,h,crop){
  const absolute=path.join(repo,relative),bytes=await fs.readFile(absolute),sha256=createHash('sha256').update(bytes).digest('hex');
  evidence.push({slide:deck.slides.items.length,path:relative,sha256,crop:crop||null});
  return slide.images.add({blob:bytes,contentType:/\.png$/i.test(relative)?'image/png':'image/jpeg',alt:`Original evidence: ${relative}`,fit:'contain',position:{left:x,top:y,width:w,height:h},...(crop?{crop}: {})});
}
const paragraphs=text=>text.split(/\n\s*\n/).filter(Boolean);
for(const item of slides){
  const slide=deck.slides.add();slide.background.fill=C.bg;
  // Spoken copy remains separate from documentary source references.
  slide.speakerNotes.text=`${item.notes}\n\nSOURCES (not spoken)\n${item.sources}\n\nVISUAL PROVENANCE (not spoken)\n${item.visual}`;
  const p=paragraphs(item.prose);
  if(item.number===1){
    txt(slide,'CINDERLINE',64,52,410,46,30,C.orange,true);
    txt(slide,item.title,64,132,470,150,55,C.text,true);
    txt(slide,p[0],64,322,440,95,34,C.orange);
    txt(slide,p.slice(1).join('\n\n'),64,442,440,150,29,C.muted);
    await picture(slide,'submission/assets/live-calendar.jpg',550,140,675,422);
  }else if(item.number===2){
    txt(slide,item.title,64,42,1152,82,48,C.text,true);
    txt(slide,p[0],64,143,420,66,42,C.orange,true);
    txt(slide,p[1],700,143,516,66,42,C.orange,true);
    txt(slide,p.slice(2).join('\n\n'),64,218,1152,58,26,C.muted);
    await picture(slide,'reports/review/aqua_vs_converted_viirs_Nepal.png',64,290,1152,367);
  }else if(item.number===3){
    txt(slide,item.title,64,42,1152,110,48,C.text,true);
    txt(slide,p[0],64,183,750,65,34,C.orange,true);
    txt(slide,p[1],64,288,735,115,32,C.text);
    txt(slide,p.slice(2).join('\n\n').replace(/ → /g,'\n→ '),64,440,735,200,32,C.muted);
    await picture(slide,'submission/assets/live-evidence.jpg',935,165,265,526,{left:0.675,top:0,right:0.01,bottom:0});
  }else if(item.number===4){
    txt(slide,item.title,64,42,1152,110,48,C.text,true);
    txt(slide,p[0],64,169,1152,56,30,C.orange);
    const table=slide.tables.add({rows:item.table.length,columns:item.table[0].length,left:64,top:252,width:1152,height:268,columnWidths:[330,210,320,292],values:item.table});
    table.borders.assign({style:'solid',fill:C.line,width:1});
    table.cells.block({row:0,column:0,rowCount:item.table.length,columnCount:item.table[0].length}).assign({fill:C.panel,textStyle:{typeface:'Arial',fontSize:30,color:C.text},margins:{top:12,right:18,bottom:12,left:18},anchor:'middle'});
    table.cells.block({row:0,column:0,rowCount:1,columnCount:item.table[0].length}).assign({fill:'#283b40',textStyle:{typeface:'Arial',fontSize:26,bold:true,color:C.orange}});
    txt(slide,p.slice(1).join('\n\n'),64,573,1152,86,28,C.muted);
  }else if(item.number===5){
    txt(slide,item.title,64,42,1152,110,48,C.text,true);
    txt(slide,p[0],64,190,695,98,32,C.muted);
    txt(slide,p[1],64,345,695,120,40,C.orange,true);
    txt(slide,p.slice(2).join('\n\n'),64,520,695,120,30,C.text);
    await picture(slide,'submission/assets/live-outage.jpg',914,165,286,526,{left:0.65,top:0,right:0.01,bottom:0});
  }else if(item.number===6){
    txt(slide,item.title,64,42,1152,110,48,C.text,true);
    txt(slide,p[0],64,189,390,112,34,C.orange,true);
    txt(slide,p[1],64,340,390,170,28,C.text);
    txt(slide,p.slice(2).join('\n\n'),64,553,390,116,28,C.muted);
    await picture(slide,'submission/assets/live-rhythm-map.jpg',494,184,722,451);
  }else{
    txt(slide,item.title,64,45,1152,100,48,C.text,true);
    txt(slide,p[0],64,192,790,110,38,C.orange,true);
    txt(slide,p[1],64,347,790,140,30,C.text);
    p.slice(2).forEach((line,index)=>{
      const box=txt(slide,line,64,544+index*58,1152,50,28,C.muted);
      const link=box.text.get(clean(line));link.link={uri:`https://${clean(line)}`,isExternal:true};link.color=C.orange;
    });
    await picture(slide,'submission/assets/live-calendar.jpg',920,192,296,185);
  }
}
const candidate=path.join(build,'candidate.pptx'),final=path.join(build,'final','FIRETRACE_slides.pptx');
await fs.mkdir(path.dirname(final),{recursive:true});
await(await PresentationFile.exportPptx(deck)).save(candidate);
await finalizePresentation({workspaceDir:repo,candidatePath:candidate,finalPath:final,pythonExecutable:path.resolve(args.python),integrityValidatorPath:path.join(path.resolve(args.skill),'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(path.resolve(args.skill),'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','4'],explicitTotalSlideCount:7,requiredNativeTableOwnerSlides:[4],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
const finalDeck=await PresentationFile.importPptx(await FileBlob.load(final));
for(const [i,slide]of finalDeck.slides.items.entries()){
  const png=await finalDeck.export({slide,format:'png',scale:2});
  await fs.writeFile(path.join(rendered,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
const pythonInfo=spawnSync(path.resolve(args.python),['-c','import sys, json, importlib.metadata as m; print(json.dumps({"python":sys.version.split()[0],"packages":{n:m.version(n) for n in ("reportlab","Pillow","pypdf")}}))'],{encoding:'utf8'});
if(pythonInfo.status!==0)throw new Error('Cannot record PDF dependency versions.');
const artifactPackage=JSON.parse(await fs.readFile(path.join(path.resolve(args.modules),'@oai/artifact-tool/package.json'),'utf8'));
const manifest={createdUtc:new Date().toISOString(),source:'submission/SLIDES.md',sourceSha256:createHash('sha256').update(markdown).digest('hex'),slideCount:7,slides:slides.map(({number,title,authoredWords,spokenWords})=>({number,title,authoredWords,spokenWords})),wordCountScope:'Authored title and slide copy, including native table cells and cover brand. Unmodified source screenshot/figure labels are retained as evidence and excluded from this prose limit.',evidence,pdfFallback:'Artifact Tool PNG/PPTX exports work; native PDF exporter fails with missing #standard-fonts/Helvetica. PDF is generated by ReportLab from final-PPTX high-resolution slide renders.',editability:{pptx:'Native editable titles, body text, speaker notes and slide-4 results table. Original source figures and screenshots remain embedded images.',nativeTableSlides:[4],pdf:'Raster pages: text is not selectable. This is not a tagged accessible PDF. Use submission/SLIDES.md for selectable text and complete notes, or the editable PPTX.'},runtime:{node:process.version,artifactTool:artifactPackage.version,...JSON.parse(pythonInfo.stdout),visualQA:'Poppler pdftoppm renders every PDF page; inspect all seven pages.',reproduce:'node submission/generate_slides.mjs --modules NODE_MODULES --skill PRESENTATION_SKILL_DIRECTORY --python PYTHON_EXECUTABLE',dependencies:'Use the bundled runtime and presentation skill finalizer; do not modify their installed packages.'},targetApplicationCheck:'Package/import/render verified. PowerPoint desktop save/reopen was not performed.',pptx:final,rendered};
await fs.writeFile(path.join(build,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
const pdf=path.join(build,'final','FIRETRACE_slides.pdf');
const result=spawnSync(path.resolve(args.python),[path.join(here,'render_slides_pdf.py'),path.join(build,'manifest.json'),pdf],{cwd:repo,stdio:'inherit'});
if(result.status!==0)throw new Error('PDF rendering failed.');
await fs.copyFile(final,path.join(here,'FIRETRACE_slides.pptx'));await fs.copyFile(pdf,path.join(here,'FIRETRACE_slides.pdf'));
manifest.outputs=await Promise.all(['pptx','pdf'].map(async format=>{const bytes=await fs.readFile(path.join(here,`FIRETRACE_slides.${format}`));return {path:`submission/FIRETRACE_slides.${format}`,sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length};}));
await fs.writeFile(path.join(build,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
const {pptx:privatePptx,rendered:privateRenders,...publicManifest}=manifest;
publicManifest.sourceHashNormalization='LF';
await fs.writeFile(path.join(here,'assets/deck-manifest.json'),JSON.stringify(publicManifest,null,2)+'\n');
await fs.writeFile(path.join(repo,'.deck-build','latest.json'),JSON.stringify({build,rendered,manifest:path.join(build,'manifest.json')},null,2)+'\n');
console.log(JSON.stringify({build,slides:manifest.slides,pptx:path.join(here,'FIRETRACE_slides.pptx'),pdf:path.join(here,'FIRETRACE_slides.pdf')},null,2));
