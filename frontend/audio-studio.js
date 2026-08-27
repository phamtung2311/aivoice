// AIVoice Audio Studio — standalone page. Project metadata and WAV blobs stay local.
const API = 'http://127.0.0.1:8000'
const PROJECT_KEY = 'aivoice_audio_studio_project'
const PROJECTS_KEY = 'aivoice_audio_studio_projects'
const ACTIVE_PROJECT_KEY = 'aivoice_audio_studio_active_project'
const DB_NAME = 'aivoice_history'
const DB_VERSION = 3
const STORE = 'voice_lab_audio'
const PREFIX = 'studio:'

const titleInput = document.getElementById('studioTitle')
const segmentsEl = document.getElementById('studioSegments')
const addBtn = document.getElementById('studioAddSegment')
const fabAddBtn = document.getElementById('studioFabAdd')
const newProjectBtn = document.getElementById('studioNewProject')
const saveProjectBtn = document.getElementById('studioSaveProject')
const playAllBtn = document.getElementById('studioPlayAll')
const exportBtn = document.getElementById('studioExport')
const statusEl = document.getElementById('studioStatus')
const saveEl = document.getElementById('studioSaveStatus')
const projectsEl = document.getElementById('studioProjectsList')
const projectSearch = document.getElementById('studioProjectSearch')
const projectStatsEl = document.getElementById('studioProjectStats')
const inspectorStatsEl = document.getElementById('studioInspectorStats')
const inspectorPlayAllBtn = document.getElementById('studioInspectorPlayAll')
const inspectorExportBtn = document.getElementById('studioInspectorExport')
const inspectorStatusEl = document.getElementById('studioInspectorStatus')
const healthEl = document.getElementById('studioHealth')
const themeToggle = document.getElementById('studioThemeToggle')

let voices = []
let project = null
let projects = []
let generating = false
let expandedSegmentId = null
let projectSearchQuery = ''

function setStatus(message, error=false){
  statusEl.textContent=message
  statusEl.style.color=error?'var(--danger)':''
  statusEl.setAttribute('role',error?'alert':'status')
  if(inspectorStatusEl){inspectorStatusEl.textContent=message;inspectorStatusEl.classList.toggle('error',error)}
}
function id(){ return `seg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,8)}` }
function projectId(){ return `project_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,8)}` }
function settings(){ return {temperature:.8,top_k:25,top_p:.95,repetition_penalty:1.2,smart_text_processing:true} }
function segment(){ return {id:id(),text:'',voice:voices[0]||'',speed:1,settings:settings(),duration:0,status:'draft',hasAudio:false} }
function normalize(raw){ const now=new Date().toISOString(); return {id:raw?.id||projectId(),title:raw?.title||'Audio Project',created_at:raw?.created_at||now,updated_at:raw?.updated_at||now,segments:Array.isArray(raw?.segments)?raw.segments.map(item=>({...segment(),...item,settings:{...settings(),...(item.settings||{})}})):[]} }
function formatTime(seconds){seconds=Math.floor(Number(seconds)||0);return `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`}
function formatBytes(bytes){if(!bytes)return '0 KB';if(bytes<1024*1024)return `${Math.max(1,Math.round(bytes/1024))} KB`;return `~${(bytes/(1024*1024)).toFixed(1)} MB`}
function metrics(candidate=project){const segments=candidate?.segments||[],ready=segments.filter(item=>item.hasAudio),duration=ready.reduce((sum,item)=>sum+(Number(item.duration)||0),0);return {total:segments.length,ready:ready.length,duration,percent:segments.length?Math.round(ready.length/segments.length*100):0,estimatedBytes:duration*24000*2}}
function save(){
  project.title=(titleInput.value||project.title||'Audio Project').trim().slice(0,120)||'Audio Project'
  project.updated_at=new Date().toISOString()
  projects=projects.map(item=>item.id===project.id?project:item)
  localStorage.setItem(PROJECTS_KEY,JSON.stringify(projects))
  localStorage.setItem(ACTIVE_PROJECT_KEY,project.id)
  localStorage.setItem(PROJECT_KEY,JSON.stringify(project))
  saveEl.textContent=`Đã lưu cục bộ · ${new Date(project.updated_at).toLocaleTimeString('vi-VN')}`
  renderProjectList();renderInspector()
}
function load(){
  try{projects=JSON.parse(localStorage.getItem(PROJECTS_KEY)||'[]')}catch(_){projects=[]}
  if(!Array.isArray(projects)||!projects.length){try{project=normalize(JSON.parse(localStorage.getItem(PROJECT_KEY)||'null'))}catch(_){project=normalize(null)}projects=[project]}
  else{projects=projects.map(normalize);const active=localStorage.getItem(ACTIVE_PROJECT_KEY);project=projects.find(item=>item.id===active)||projects[0]}
  titleInput.value=project.title;save();render()
}
function makeStat(label,value){const box=document.createElement('div'),caption=document.createElement('span'),number=document.createElement('strong');caption.textContent=label;number.textContent=value;box.append(caption,number);return box}
function renderProjectStats(){if(!projectStatsEl)return;const summary=metrics();projectStatsEl.replaceChildren(makeStat('Segments',String(summary.total)),makeStat('Sẵn sàng',`${summary.percent}%`),makeStat('Tổng thời lượng',formatTime(summary.duration)))}
function renderInspector(){
  if(!inspectorStatsEl)return
  const summary=metrics()
  inspectorStatsEl.replaceChildren(makeStat('Segment sẵn sàng',`${summary.ready} / ${summary.total}`),makeStat('Tổng thời lượng',formatTime(summary.duration)),makeStat('WAV ước tính',formatBytes(summary.estimatedBytes)))
  inspectorPlayAllBtn.disabled=!summary.ready;inspectorExportBtn.disabled=!summary.ready
}
function renderProjectList(){
  if(!projectsEl)return
  projectsEl.replaceChildren()
  const query=projectSearchQuery.trim().toLocaleLowerCase('vi-VN'),matching=projects.filter(item=>!query||item.title.toLocaleLowerCase('vi-VN').includes(query))
  if(!matching.length){const empty=document.createElement('p');empty.className='muted small';empty.textContent='Không tìm thấy dự án phù hợp.';projectsEl.appendChild(empty)}
  matching.forEach(item=>{
    const summary=metrics(item),card=document.createElement('article'),open=document.createElement('button'),name=document.createElement('strong'),meta=document.createElement('p'),actions=document.createElement('div'),duplicate=document.createElement('button'),remove=document.createElement('button')
    card.className=`studioProjectCard${item.id===project.id?' active':''}`
    card.addEventListener('click',event=>{if(!event.target.closest('button'))openProject(item.id)})
    open.type='button';open.className='studioProjectOpen';open.setAttribute('aria-label',`Mở dự án ${item.title}`);open.addEventListener('click',()=>openProject(item.id))
    name.className='studioProjectName';name.textContent=item.title;meta.className='studioProjectMeta';meta.textContent=`${summary.total} segment · ${formatTime(summary.duration)} · ${summary.percent}% sẵn sàng`;open.append(name,meta)
    actions.className='studioProjectActions'
    duplicate.type='button';duplicate.className='secondary small';duplicate.textContent='Nhân bản';duplicate.setAttribute('aria-label',`Nhân bản dự án ${item.title}`);duplicate.addEventListener('click',()=>duplicateProject(item.id))
    remove.type='button';remove.className='secondary small historyDelete';remove.textContent='Xóa';remove.disabled=projects.length===1;remove.setAttribute('aria-label',`Xóa dự án ${item.title}`);remove.addEventListener('click',()=>deleteProject(item.id))
    actions.append(duplicate,remove);card.append(open,actions);projectsEl.appendChild(card)
  })
  renderProjectStats()
}
function openProject(idToOpen){save();const next=projects.find(item=>item.id===idToOpen);if(!next)return;project=next;expandedSegmentId=null;titleInput.value=project.title;localStorage.setItem(ACTIVE_PROJECT_KEY,project.id);render();setStatus(`Đã mở project “${project.title}”.`)}
function duplicateProject(idToCopy){
  save();const source=projects.find(item=>item.id===idToCopy);if(!source)return
  const now=new Date().toISOString()
  project={id:projectId(),title:`${source.title} (bản sao)`.slice(0,120),created_at:now,updated_at:now,segments:source.segments.map(item=>({...item,id:id(),hasAudio:false,status:'draft',duration:0,settings:{...item.settings}}))}
  projects.push(project);expandedSegmentId=null;titleInput.value=project.title;save();render();setStatus('Đã tạo bản sao project. Audio được tạo lại riêng cho bản sao.')
}
async function deleteProject(idToDelete){const target=projects.find(item=>item.id===idToDelete);if(!target||projects.length===1)return;if(!window.confirm(`Xóa project “${target.title}” và audio segment của project này?`))return;await Promise.all(target.segments.filter(item=>item.hasAudio).map(item=>deleteAudio(item.id).catch(()=>{})));projects=projects.filter(item=>item.id!==idToDelete);if(project.id===idToDelete){project=projects[0];expandedSegmentId=null;titleInput.value=project.title}save();render();setStatus('Đã xóa project.')}

function openDb(){ return new Promise((resolve,reject)=>{ const req=indexedDB.open(DB_NAME,DB_VERSION); req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains('history_audio'))db.createObjectStore('history_audio');if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE)}; req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(req.error) }) }
async function storeRun(mode, callback){ const db=await openDb(); return new Promise((resolve,reject)=>{ const tx=db.transaction(STORE,mode), request=callback(tx.objectStore(STORE)); tx.oncomplete=()=>{db.close();resolve(request?.result)}; tx.onerror=()=>{db.close();reject(tx.error)} }) }
function putAudio(key,blob){return storeRun('readwrite',store=>store.put(blob,PREFIX+key))}
function getAudio(key){return storeRun('readonly',store=>store.get(PREFIX+key))}
function deleteAudio(key){return storeRun('readwrite',store=>store.delete(PREFIX+key))}

function ensureVoice(item){if((!item.voice||!voices.includes(item.voice))&&voices.length)item.voice=voices[0]}
function statusLabel(item){return item.status==='ready'?'Sẵn sàng':item.status==='generating'?'Đang tạo':'Bản nháp'}
function render(){
  if(expandedSegmentId&&!project.segments.some(item=>item.id===expandedSegmentId))expandedSegmentId=null
  segmentsEl.replaceChildren()
  if(!project.segments.length){const hint=document.createElement('p');hint.className='studioEmpty muted';hint.textContent='Chưa có segment. Bấm “Thêm segment” để bắt đầu.';segmentsEl.appendChild(hint);renderInspector();return}
  project.segments.forEach((item,index)=>{
    ensureVoice(item)
    const expanded=item.id===expandedSegmentId,card=document.createElement('article'),header=document.createElement('div'),number=document.createElement('span'),summary=document.createElement('div'),voiceSummary=document.createElement('span'),durationSummary=document.createElement('span'),badge=document.createElement('span'),toggle=document.createElement('button')
    card.className=`studioSegment${expanded?' expanded':''}`;card.dataset.id=item.id
    header.className='studioSegmentHeader';number.className='studioSegmentNumber';number.textContent=`${index+1}`
    summary.className='studioSegmentSummary';voiceSummary.className='studioSegmentVoice';voiceSummary.textContent=item.voice||'Chưa chọn giọng';durationSummary.textContent=formatTime(item.duration);badge.className=`studioBadge ${item.status}`;badge.textContent=statusLabel(item);summary.append(voiceSummary,durationSummary,badge)
    header.title=expanded?'Bấm để thu gọn segment':'Bấm để mở segment'
    header.addEventListener('click',event=>{if(event.target.closest('button'))return;expandedSegmentId=expandedSegmentId===item.id?null:item.id;render()})
    toggle.type='button';toggle.className='secondary small';toggle.dataset.action='toggle';toggle.setAttribute('aria-expanded',String(expanded));toggle.textContent=expanded?'Thu gọn':'Mở';header.append(number,summary,toggle);card.appendChild(header)
    if(expanded){
      const body=document.createElement('div'),text=document.createElement('textarea'),controls=document.createElement('div'),voice=document.createElement('select'),speed=document.createElement('input'),generate=document.createElement('button'),actions=document.createElement('div'),details=document.createElement('p')
      body.className='studioSegmentBody';text.rows=5;text.placeholder='Nhập nội dung segment...';text.value=item.text;text.addEventListener('input',()=>{item.text=text.value;generate.disabled=generating||!item.text.trim();save()})
      controls.className='studioSegmentControls';voices.forEach(value=>{const option=document.createElement('option');option.value=value;option.textContent=value;option.selected=value===item.voice;voice.appendChild(option)})
      voice.disabled=!voices.length;voice.setAttribute('aria-label','Chọn giọng đọc');voice.addEventListener('change',()=>{item.voice=voice.value;save()})
      speed.type='number';speed.min='.5';speed.max='2';speed.step='.1';speed.value=item.speed;speed.setAttribute('aria-label','Tốc độ đọc');speed.addEventListener('change',()=>{item.speed=Math.min(2,Math.max(.5,Number(speed.value)||1));speed.value=item.speed;save()})
      generate.type='button';generate.className='primary small';generate.dataset.action='generate';generate.textContent=item.hasAudio?'↻ Regenerate':'▶ Generate';generate.disabled=generating||!item.text.trim();controls.append(voice,speed,generate)
      actions.className='studioSegmentActions';for(const [caption,action,disabled] of [['▶ Play','play',!item.hasAudio],['⧉ Duplicate','duplicate',false],['↑ Lên','up',index===0],['↓ Xuống','down',index===project.segments.length-1],['Xóa','delete',false]]){const button=document.createElement('button');button.type='button';button.className='secondary small';button.dataset.action=action;button.textContent=caption;button.disabled=disabled;actions.appendChild(button)}
      details.className='muted small studioSettings';details.textContent=`Advanced · T ${item.settings.temperature} · K ${item.settings.top_k} · P ${item.settings.top_p} · Rep ${item.settings.repetition_penalty} · Smart ${item.settings.smart_text_processing?'ON':'OFF'}`
      body.append(text,controls,actions,details);card.appendChild(body)
    }
    segmentsEl.appendChild(card)
  })
  save()
}
function currentIndex(button){const itemId=button.closest('[data-id]')?.dataset.id;return project.segments.findIndex(item=>item.id===itemId)}
function addSegment(){const next=segment();project.segments.push(next);expandedSegmentId=next.id;save();render();requestAnimationFrame(()=>segmentsEl.querySelector(`[data-id="${next.id}"] textarea`)?.focus())}
segmentsEl.addEventListener('click',event=>{const button=event.target.closest('[data-action]');if(!button||button.disabled)return;const index=currentIndex(button);if(index<0)return;const action=button.dataset.action;if(action==='toggle'){expandedSegmentId=expandedSegmentId===project.segments[index].id?null:project.segments[index].id;render();return}if(action==='generate')generate(index);else if(action==='play')play(project.segments[index]);else if(action==='duplicate'){const copy={...project.segments[index],id:id(),hasAudio:false,status:'draft',duration:0,settings:{...project.segments[index].settings}};project.segments.splice(index+1,0,copy);expandedSegmentId=copy.id;save();render()}else if(action==='up'||action==='down'){const target=index+(action==='up'?-1:1);[project.segments[index],project.segments[target]]=[project.segments[target],project.segments[index]];save();render()}else if(action==='delete'){const [removed]=project.segments.splice(index,1);if(removed.hasAudio)deleteAudio(removed.id).catch(()=>{});expandedSegmentId=null;save();render()}})

function duration(blob){return new Promise(resolve=>{const audio=document.createElement('audio'),url=URL.createObjectURL(blob),done=value=>{URL.revokeObjectURL(url);resolve(value)};audio.onloadedmetadata=()=>done(Number.isFinite(audio.duration)?audio.duration:0);audio.onerror=()=>done(0);audio.src=url})}
async function generate(index){const item=project.segments[index];if(!item||generating)return;if(!item.voice&&voices.length){item.voice=voices[0];save()}if(!item.voice){setStatus('Đang tải danh sách giọng. Hãy thử lại sau ít giây.',true);return}generating=true;item.status='generating';expandedSegmentId=item.id;setStatus(`Đang tạo Segment ${index+1}...`);render();try{const response=await fetch(API+'/api/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:item.text,voice:item.voice,speed:item.speed,...item.settings})});if(!response.ok)throw Error();const blob=await response.blob();if(!blob||blob.size<=44)throw Error();await putAudio(item.id,blob);item.duration=await duration(blob);item.status='ready';item.hasAudio=true;save();setStatus(`Segment ${index+1} đã sẵn sàng.`)}catch(_){item.status=item.hasAudio?'ready':'draft';setStatus(`Không thể tạo Segment ${index+1}. Hãy kiểm tra backend rồi thử lại.`,true)}finally{generating=false;render()}}
async function play(item){const blob=await getAudio(item.id);if(!(blob instanceof Blob)){item.hasAudio=false;save();render();setStatus('Không tìm thấy audio của segment này.',true);return}const audio=new Audio(URL.createObjectURL(blob));audio.onended=()=>URL.revokeObjectURL(audio.src);await audio.play()}
async function playAll(){for(const item of project.segments)if(item.hasAudio)await new Promise(async resolve=>{const blob=await getAudio(item.id);if(!(blob instanceof Blob))return resolve();const audio=new Audio(URL.createObjectURL(blob));audio.onended=()=>{URL.revokeObjectURL(audio.src);resolve()};audio.onerror=resolve;await audio.play()})}
function encodeWav(channels,sr){const length=channels[0].length,buffer=new ArrayBuffer(44+length*channels.length*2),view=new DataView(buffer),u32=(at,value)=>view.setUint32(at,value,true);view.setUint32(0,0x46464952,true);u32(4,36+length*channels.length*2);view.setUint32(8,0x45564157,true);view.setUint32(12,0x20746d66,true);u32(16,16);view.setUint16(20,1,true);view.setUint16(22,channels.length,true);u32(24,sr);u32(28,sr*channels.length*2);view.setUint16(32,channels.length*2);view.setUint16(34,16);view.setUint32(36,0x61746164,true);u32(40,length*channels.length*2);let at=44;for(let i=0;i<length;i++)for(const channel of channels){const value=Math.max(-1,Math.min(1,channel[i]));view.setInt16(at,value<0?value*0x8000:value*0x7fff,true);at+=2}return new Blob([buffer],{type:'audio/wav'})}
async function exportWav(){const ready=project.segments.filter(item=>item.hasAudio);if(!ready.length){setStatus('Chưa có segment nào để xuất WAV.',true);return}const context=new AudioContext();try{const buffers=[];for(const item of ready){const blob=await getAudio(item.id);if(blob instanceof Blob)buffers.push(await context.decodeAudioData(await blob.arrayBuffer()))}if(!buffers.length||buffers.some(item=>item.sampleRate!==buffers[0].sampleRate))throw Error();const channels=Math.max(...buffers.map(item=>item.numberOfChannels)),length=buffers.reduce((total,item)=>total+item.length,0),merged=Array.from({length:channels},()=>new Float32Array(length));let offset=0;for(const buffer of buffers){for(let channel=0;channel<channels;channel++)merged[channel].set(buffer.getChannelData(Math.min(channel,buffer.numberOfChannels-1)),offset);offset+=buffer.length}const url=URL.createObjectURL(encodeWav(merged,buffers[0].sampleRate)),link=document.createElement('a');link.href=url;link.download=`${project.title.replace(/[^\w-]+/g,'-')||'audio-project'}.wav`;link.click();setTimeout(()=>URL.revokeObjectURL(url),2000);setStatus('Đã xuất WAV.')}catch(_){setStatus('Không thể xuất WAV. Hãy kiểm tra các segment đã sẵn sàng và cùng sample rate.',true)}finally{context.close()}}

async function loadVoices(){try{const [health,response]=await Promise.all([fetch(API+'/api/health'),fetch(API+'/api/voices')]);const info=health.ok?await health.json():null;healthEl.textContent=info?'● TTS cục bộ đang hoạt động':'● Backend không khả dụng';healthEl.style.color=info?'#78e08f':'#ff9b9b';const data=await response.json();voices=(data.voices||[]).map(item=>item.id).filter(Boolean);render()}catch(_){healthEl.textContent='● Backend không khả dụng';healthEl.style.color='#ff9b9b'}}
function applyTheme(theme){document.documentElement.setAttribute('data-theme',theme);localStorage.setItem('theme',theme);themeToggle.textContent=theme==='light'?'☀️':'🌙'}
themeToggle.addEventListener('click',()=>applyTheme(document.documentElement.getAttribute('data-theme')==='light'?'dark':'light'))
addBtn.addEventListener('click',addSegment);fabAddBtn?.addEventListener('click',addSegment)
saveProjectBtn.addEventListener('click',()=>{save();setStatus('Đã lưu project cục bộ.')})
newProjectBtn.addEventListener('click',()=>{save();project=normalize(null);projects.push(project);expandedSegmentId=null;titleInput.value=project.title;save();render();setStatus('Đã tạo project mới. Project cũ vẫn được lưu trong danh sách.')})
playAllBtn.addEventListener('click',playAll);exportBtn.addEventListener('click',exportWav)
inspectorPlayAllBtn?.addEventListener('click',playAll);inspectorExportBtn?.addEventListener('click',exportWav)
projectSearch?.addEventListener('input',()=>{projectSearchQuery=projectSearch.value;renderProjectList()})
titleInput.addEventListener('input',save)
applyTheme(localStorage.getItem('theme')||'dark');load();loadVoices()
