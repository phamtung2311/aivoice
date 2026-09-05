// AIVoice Audio Studio — standalone page. Project metadata and WAV blobs stay local.
const API = 'http://127.0.0.1:8000'
const DEFAULT_VOICE_ID = 'podcast_soft_baritone'
const PROJECT_KEY = 'aivoice_audio_studio_project'
const PROJECTS_KEY = 'aivoice_audio_studio_projects'
const ACTIVE_PROJECT_KEY = 'aivoice_audio_studio_active_project'
const DB_NAME = 'aivoice_history'
const DB_VERSION = 3
const STORE = 'voice_lab_audio'
const PREFIX = 'studio:'
const PODCAST_BRAND_VOICE_ID = 'podcast_brand_voice_v1'

const titleInput = document.getElementById('studioTitle')
const segmentsEl = document.getElementById('studioSegments')
const addBtn = document.getElementById('studioAddSegment')
const fabAddBtn = document.getElementById('studioFabAdd')
const newProjectBtn = document.getElementById('studioNewProject')
const saveProjectBtn = document.getElementById('studioSaveProject')
const addAudioBtn = document.getElementById('studioAddAudio')
const audioImport = document.getElementById('studioAudioImport')
const cancelBtn = document.getElementById('studioCancel')
const playAllBtn = document.getElementById('studioPlayAll')
const pauseBtn = document.getElementById('studioPause')
const stopBtn = document.getElementById('studioStop')
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
const soundPicker = document.getElementById('studioSoundPicker')
const soundPickerList = document.getElementById('studioSoundPickerList')
const soundPickerClose = document.getElementById('studioSoundPickerClose')
const soundPickerUpload = document.getElementById('studioSoundPickerUpload')

let voices = []
let project = null
let projects = []
let generating = false
let activeJob = null
let expandedSegmentId = null
let projectSearchQuery = ''
const playback = {state:'idle',mode:null,audio:null,itemId:null,queueToken:0,silenceTimer:null,silenceFrame:null,objectUrl:null}
const SOUND_LIBRARY = [
  {id:'flute',name:'✦ Sáo & đàn tranh thư giãn',description:'Sáo mềm cùng phần đệm nhạc nhẹ · 7 giây',duration:7},
  {id:'piano',name:'✦ Piano lofi chuyển cảnh',description:'Piano ấm, nhẹ nhàng · 7 giây',duration:7},
  {id:'ambient',name:'✦ Không gian dịu',description:'Nền ấm, thư giãn · 7 giây',duration:7}
]
let soundInsertIndex = null
let soundPreview = null

function setStatus(message, error=false){
  statusEl.textContent=message
  statusEl.style.color=error?'var(--danger)':''
  statusEl.setAttribute('role',error?'alert':'status')
  if(inspectorStatusEl){inspectorStatusEl.textContent=message;inspectorStatusEl.classList.toggle('error',error)}
}
function setGenerating(value){generating=value;cancelBtn.hidden=!value;cancelBtn.disabled=!value}
function updatePlaybackControls(){const active=playback.state!=='idle';playAllBtn.hidden=active;pauseBtn.hidden=!active;stopBtn.hidden=!active;pauseBtn.textContent=playback.state==='paused'?'▶ Tiếp tục':'⏸ Tạm dừng';pauseBtn.setAttribute('aria-label',pauseBtn.textContent);if(active)setStatus(playback.state==='paused'?'Tạm dừng phát.':'Đang phát.')}
function id(){ return `seg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,8)}` }
function projectId(){ return `project_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,8)}` }
function settings(){ return {temperature:.8,top_k:25,top_p:.95,repetition_penalty:1.2,smart_text_processing:true,tts_script:'',prosody_markup:false} }
function defaultVoice(){return !voices.length||voices.includes(DEFAULT_VOICE_ID)?DEFAULT_VOICE_ID:voices[0]}
function segment(){ return {id:id(),type:'tts',text:'',voice:defaultVoice(),speed:1,settings:settings(),duration:0,status:'draft',hasAudio:false} }
function audioClip(){return {id:id(),type:'audio',name:'Audio Clip',audioKey:'',duration:0,status:'draft',hasAudio:false,volume:100}}
function silence(){return {id:id(),type:'silence',duration_ms:2500,duration:2.5,status:'ready',hasAudio:false}}
function normalizeItem(item){const type=item?.type==='audio'?'audio':item?.type==='silence'?'silence':'tts';return type==='audio'?{...audioClip(),...item,type:'audio',audioKey:item.audioKey||item.id}:type==='silence'?{...silence(),...item,type:'silence',duration_ms:Math.min(30000,Math.max(100,Number(item.duration_ms)||2500)),status:'ready'}:{...segment(),...item,type:'tts',settings:{...settings(),...(item.settings||{})}}}
function normalize(raw){ const now=new Date().toISOString(); return {id:raw?.id||projectId(),title:raw?.title||'Audio Project',created_at:raw?.created_at||now,updated_at:raw?.updated_at||now,segments:Array.isArray(raw?.segments)?raw.segments.map(normalizeItem):[]} }
function formatTime(seconds){seconds=Math.floor(Number(seconds)||0);return `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`}
function formatBytes(bytes){if(!bytes)return '0 KB';if(bytes<1024*1024)return `${Math.max(1,Math.round(bytes/1024))} KB`;return `~${(bytes/(1024*1024)).toFixed(1)} MB`}
function itemDuration(item){return item?.type==='silence'?Math.max(0,Number(item.duration_ms)||0)/1000:Number(item?.duration)||0}
function metrics(candidate=project){const segments=candidate?.segments||[],ready=segments.filter(item=>item.hasAudio||item.type==='silence'),duration=ready.reduce((sum,item)=>sum+itemDuration(item),0);return {total:segments.length,ready:ready.length,duration,percent:segments.length?Math.round(ready.length/segments.length*100):0,estimatedBytes:duration*24000*2}}
function save(){
  project.title=(titleInput.value||project.title||'Audio Project').trim().slice(0,120)||'Audio Project'
  project.updated_at=new Date().toISOString()
  projects=projects.map(item=>item.id===project.id?project:item)
  localStorage.setItem(PROJECTS_KEY,JSON.stringify(projects))
  localStorage.setItem(ACTIVE_PROJECT_KEY,project.id)
  localStorage.setItem(PROJECT_KEY,JSON.stringify(project))
  saveEl.textContent='✓ Đã lưu'
  renderProjectList();renderInspector()
}
function load(){
  try{projects=JSON.parse(localStorage.getItem(PROJECTS_KEY)||'[]')}catch(_){projects=[]}
  if(!Array.isArray(projects)||!projects.length){try{project=normalize(JSON.parse(localStorage.getItem(PROJECT_KEY)||'null'))}catch(_){project=normalize(null)}projects=[project]}
  else{projects=projects.map(normalize);const active=localStorage.getItem(ACTIVE_PROJECT_KEY);project=projects.find(item=>item.id===active)||projects[0]}
  titleInput.value=project.title
  try{const handoff=JSON.parse(sessionStorage.getItem('aivoice_audio_studio_handoff')||'null');if(handoff?.text?.trim()){const next=segment();next.text=handoff.text;next.voice=handoff.voice||next.voice;next.speed=Math.min(2,Math.max(.5,Number(handoff.speed)||1));next.settings.tts_script=handoff.tts_script||'';next.settings.prosody_markup=/\|/.test(next.settings.tts_script);project.segments.push(next);expandedSegmentId=next.id;sessionStorage.removeItem('aivoice_audio_studio_handoff')}}catch(_){sessionStorage.removeItem('aivoice_audio_studio_handoff')}
  save();render()
}
function makeStat(label,value){const box=document.createElement('div'),caption=document.createElement('span'),number=document.createElement('strong');caption.textContent=label;number.textContent=value;box.append(caption,number);return box}
function renderProjectStats(){if(!projectStatsEl)return;const summary=metrics();projectStatsEl.replaceChildren(makeStat('Segments',String(summary.total)),makeStat('Sẵn sàng',`${summary.percent}%`),makeStat('Tổng thời lượng',formatTime(summary.duration)))}
function renderInspector(){
  if(!inspectorStatsEl)return
  const summary=metrics()
  inspectorStatsEl.replaceChildren(makeStat('Segment sẵn sàng',`${summary.ready} / ${summary.total}`),makeStat('Tổng thời lượng',formatTime(summary.duration)),makeStat('WAV ước tính',formatBytes(summary.estimatedBytes)))
  if(inspectorPlayAllBtn)inspectorPlayAllBtn.disabled=!summary.ready;if(inspectorExportBtn)inspectorExportBtn.disabled=!summary.ready
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
  project={id:projectId(),title:`${source.title} (bản sao)`.slice(0,120),created_at:now,updated_at:now,segments:source.segments.map(item=>item.type==='audio'?{...item,id:id()}:{...item,id:id(),hasAudio:false,status:'draft',duration:0,settings:{...item.settings}})}
  projects.push(project);expandedSegmentId=null;titleInput.value=project.title;save();render();setStatus('Đã tạo bản sao project. TTS tạo lại riêng; Audio Clip dùng lại tệp cục bộ.')
}
async function deleteProject(idToDelete){const target=projects.find(item=>item.id===idToDelete);if(!target||projects.length===1)return;if(!window.confirm(`Xóa project “${target.title}”?`))return;projects=projects.filter(item=>item.id!==idToDelete);if(project.id===idToDelete){project=projects[0];expandedSegmentId=null;titleInput.value=project.title}save();render();setStatus('Đã xóa project. Audio cục bộ dùng chung được giữ an toàn.')}

function openDb(){ return new Promise((resolve,reject)=>{ const req=indexedDB.open(DB_NAME,DB_VERSION); req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains('history_audio'))db.createObjectStore('history_audio');if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE)}; req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(req.error) }) }
async function storeRun(mode, callback){ const db=await openDb(); return new Promise((resolve,reject)=>{ const tx=db.transaction(STORE,mode), request=callback(tx.objectStore(STORE)); tx.oncomplete=()=>{db.close();resolve(request?.result)}; tx.onerror=()=>{db.close();reject(tx.error)} }) }
function putAudio(key,blob){return storeRun('readwrite',store=>store.put(blob,PREFIX+key))}
function getAudio(key){return storeRun('readonly',store=>store.get(PREFIX+key))}
function deleteAudio(key){return storeRun('readwrite',store=>store.delete(PREFIX+key))}

function ensureVoice(item){if((!item.voice||!voices.includes(item.voice))&&voices.length)item.voice=defaultVoice()}
function statusLabel(item){return item.status==='ready'?'Sẵn sàng':item.status==='generating'?'Đang tạo':'Bản nháp'}
function insertionPoint(index){const wrap=document.createElement('div'),open=document.createElement('button'),menu=document.createElement('div');wrap.className='studioInsertion';open.type='button';open.className='studioInsertButton';open.textContent='＋';open.title='Thêm vào đây';open.setAttribute('aria-label','Thêm vào đây');open.setAttribute('aria-expanded','false');menu.className='studioInsertionMenu';menu.hidden=true;for(const [caption,type] of [['🎙 Đoạn đọc','tts'],['⏸ Khoảng nghỉ','silence'],['🎵 Âm thanh','audio']]){const button=document.createElement('button');button.type='button';button.className='secondary small';button.textContent=caption;button.addEventListener('click',()=>type==='audio'?openSoundPicker(index):insertTimelineItem(index,type));menu.appendChild(button)}open.addEventListener('click',()=>{const next=menu.hidden;document.querySelectorAll('.studioInsertionMenu').forEach(candidate=>candidate.hidden=true);document.querySelectorAll('.studioInsertButton').forEach(candidate=>candidate.setAttribute('aria-expanded','false'));menu.hidden=!next;open.setAttribute('aria-expanded',String(next))});wrap.append(open,menu);return wrap}
function insertTimelineItem(index,type){if(type==='silence'){const item=silence();project.segments.splice(index,0,item);expandedSegmentId=item.id;save();render();setStatus('Đã thêm Nghỉ 2,5 giây.')}else if(type==='tts'){const item=segment();project.segments.splice(index,0,item);expandedSegmentId=item.id;save();render()}else{audioImport.dataset.insertIndex=String(index);delete audioImport.dataset.replaceIndex;audioImport.click()}}
function builtInSoundData(preset){const rate=22050,length=Math.floor(preset.duration*rate),data=new Float32Array(length),melody=[523.25,587.33,659.25,783.99,659.25,587.33,523.25,440],harmony=[261.63,293.66,329.63,220];for(let index=0;index<length;index++){const time=index/rate;let sample=0;if(preset.id==='flute'){const step=Math.floor(time/1.65)%melody.length,local=time%1.65,frequency=melody[step],fluteEnvelope=Math.min(1,local/.16)*Math.min(1,(1.65-local)/.42),flute=(Math.sin(2*Math.PI*frequency*time)+.18*Math.sin(2*Math.PI*frequency*2*time)+.06*Math.sin(2*Math.PI*frequency*3*time))*fluteEnvelope*.18,root=harmony[Math.floor(time/3.3)%harmony.length],pluckLocal=time%.825,pluckEnvelope=Math.exp(-pluckLocal*3.2),strings=(Math.sin(2*Math.PI*root*time)+.48*Math.sin(2*Math.PI*root*1.5*time)+.18*Math.sin(2*Math.PI*root*2*time))*pluckEnvelope*.07,pad=(Math.sin(2*Math.PI*root*.5*time)+.45*Math.sin(2*Math.PI*root*.75*time))*.025;sample=flute+strings+pad}else if(preset.id==='piano'){const step=Math.floor(time/1.15)%melody.length,local=time%1.15,frequency=melody[step]/2,envelope=Math.exp(-local*2.6),piano=(Math.sin(2*Math.PI*frequency*time)+.45*Math.sin(2*Math.PI*frequency*2*time)+.16*Math.sin(2*Math.PI*frequency*3*time))*envelope*.17,bass=harmony[Math.floor(time/2.3)%harmony.length]*.5;sample=piano+Math.sin(2*Math.PI*bass*time)*Math.exp(-(time%2.3)*1.8)*.045}else{const root=harmony[Math.floor(time/2.5)%harmony.length];sample=(Math.sin(2*Math.PI*root*time)+.5*Math.sin(2*Math.PI*(root*1.498)*time)+.25*Math.sin(2*Math.PI*(root*.5)*time))*.055*(.7+.3*Math.sin(2*Math.PI*.12*time))}data[index]=sample}return {rate,data}}
function builtInSoundBlob(preset){const {rate,data}=builtInSoundData(preset);return encodeWav([data],rate)}
function stopSoundPreview(){if(!soundPreview)return;try{soundPreview.source.stop()}catch(_){}soundPreview.context.close().catch(()=>{});soundPreview=null}
async function previewBuiltInSound(preset){stopSoundPreview();try{const {rate,data}=builtInSoundData(preset),context=new AudioContext(),buffer=context.createBuffer(1,data.length,rate),source=context.createBufferSource();buffer.copyToChannel(data,0);source.buffer=buffer;source.connect(context.destination);soundPreview={context,source};source.onended=()=>{if(soundPreview?.source===source){context.close().catch(()=>{});soundPreview=null}};await context.resume();source.start();setStatus(`Đang nghe thử “${preset.name.replace('✦ ','')}”.`)}catch(_){setStatus('Trình duyệt đang chặn nghe thử. Hãy bấm lại nút Nghe thử.',true)}}
async function insertBuiltInSound(index,preset){const item=audioClip();item.name=preset.name.replace('✦ ','');item.audioKey=item.id;item.duration=preset.duration;item.status='ready';item.hasAudio=true;item.volume=58;await putAudio(item.audioKey,builtInSoundBlob(preset));project.segments.splice(index,0,item);expandedSegmentId=item.id;closeSoundPicker();save();render();setStatus(`Đã chèn “${item.name}”.`)}
function closeSoundPicker(){stopSoundPreview();if(soundPicker?.open)soundPicker.close();soundInsertIndex=null}
function openSoundPicker(index){if(!soundPicker||!soundPickerList)return;soundInsertIndex=index;soundPickerList.replaceChildren();SOUND_LIBRARY.forEach(preset=>{const option=document.createElement('article'),copy=document.createElement('div'),name=document.createElement('strong'),description=document.createElement('span'),preview=document.createElement('button'),insert=document.createElement('button');option.className='studioSoundOption';name.textContent=preset.name;description.textContent=preset.description;copy.append(name,description);preview.type='button';preview.className='secondary small';preview.textContent='▶ Nghe thử';preview.addEventListener('click',()=>previewBuiltInSound(preset));insert.type='button';insert.className='primary small';insert.textContent='＋ Chèn';insert.addEventListener('click',()=>insertBuiltInSound(index,preset));option.append(copy,preview,insert);soundPickerList.appendChild(option)});document.querySelectorAll('.studioInsertionMenu').forEach(menu=>menu.hidden=true);if(!soundPicker.open)soundPicker.showModal()}
function render(){
  if(expandedSegmentId&&!project.segments.some(item=>item.id===expandedSegmentId))expandedSegmentId=null
  segmentsEl.replaceChildren()
  if(!project.segments.length){const hint=document.createElement('p');hint.className='studioEmpty muted';hint.textContent='Chưa có segment. Bấm “Thêm segment” để bắt đầu.';segmentsEl.appendChild(hint);renderInspector();return}
  const timeline=document.createElement('section'),ruler=document.createElement('div'),track=document.createElement('div'),editorHost=document.createElement('section'),timelineFooter=document.createElement('div')
  timeline.className='studioTimeline';timeline.setAttribute('aria-label','Dòng thời gian của project')
  ruler.className='studioTimelineRuler';ruler.innerHTML='<span id="studioTimelineClock">00:00</span><span>Timeline project</span><span>kéo ngang để xem thêm</span>'
  track.className='studioTimelineTrack';editorHost.className='studioEditorHost';timelineFooter.className='studioTimelineFooter'
  const playhead=document.createElement('i');playhead.className='studioPlayhead';playhead.setAttribute('aria-hidden','true');track.appendChild(playhead)
  timeline.append(ruler,track,timelineFooter);segmentsEl.append(timeline,editorHost)
  project.segments.forEach((item,index)=>{
    if(item.type==='tts')ensureVoice(item)
    const expanded=item.id===expandedSegmentId,card=document.createElement('article'),header=document.createElement('div'),number=document.createElement('span'),summary=document.createElement('div'),voiceSummary=document.createElement('span'),durationSummary=document.createElement('span'),badge=document.createElement('span'),progress=document.createElement('span'),quickPlay=document.createElement('button'),toggle=document.createElement('button')
    card.className=`studioSegment${expanded?' expanded':''}${playback.itemId===item.id&&playback.state!=='idle'?' playing':''}`;card.dataset.id=item.id;card.style.setProperty('--clip-width',`${Math.max(118,Math.min(300,itemDuration(item)?itemDuration(item)*18:Math.max(145,String(item.text||item.name||'').length*2.4)))}px`)
    header.className='studioSegmentHeader';number.className='studioSegmentNumber';number.textContent=`${index+1}`
    summary.className='studioSegmentSummary';voiceSummary.className='studioSegmentVoice';voiceSummary.textContent=item.type==='audio'?`🎵 ${item.name||'Âm thanh'}`:item.type==='silence'?'⏸ Khoảng nghỉ':`🎙 ${String(item.text||'Đoạn đọc mới').replace(/\s+/g,' ').slice(0,72)}`;durationSummary.textContent=formatTime(itemDuration(item));badge.className=`studioBadge ${item.status}`;badge.textContent=statusLabel(item);progress.className='studioPlaybackProgress';if(playback.itemId===item.id&&playback.audio)progress.textContent=`Đang phát ${formatTime(playback.audio.currentTime)} / ${formatTime(playback.audio.duration||itemDuration(item))}`;summary.append(voiceSummary,durationSummary,badge,progress)
    header.title=expanded?'Bấm để thu gọn segment':'Bấm để mở segment'
    header.addEventListener('click',event=>{if(event.target.closest('button'))return;expandedSegmentId=expandedSegmentId===item.id?null:item.id;render()})
    quickPlay.type='button';quickPlay.className='secondary small';quickPlay.dataset.action='play';quickPlay.textContent=playback.itemId===item.id&&playback.state!=='idle'?(playback.state==='paused'?'▶ Tiếp':'⏸'):'▶ Nghe';quickPlay.disabled=item.type==='silence'||!item.hasAudio||item.voiceChanged;quickPlay.title=item.voiceChanged?'Hãy Regenerate để nghe giọng mới':'Nghe segment';toggle.type='button';toggle.className='secondary small';toggle.dataset.action='toggle';toggle.setAttribute('aria-expanded',String(expanded));toggle.textContent=expanded?'Thu gọn':'Sửa';header.append(number,summary,quickPlay,toggle);card.appendChild(header)
    if(expanded&&item.type==='tts'){
      const body=document.createElement('div'),originalHint=document.createElement('strong'),text=document.createElement('textarea'),pauseTools=document.createElement('div'),pauseLabel=document.createElement('span'),controls=document.createElement('div'),voice=document.createElement('select'),speed=document.createElement('input'),speedRow=document.createElement('label'),speedCaption=document.createElement('span'),speedValue=document.createElement('output'),generate=document.createElement('button'),actions=document.createElement('div'),details=document.createElement('p')
      const isPodcastBrand=item.voice===PODCAST_BRAND_VOICE_ID
      body.className='studioSegmentBody';originalHint.className='studioFieldLabel';originalHint.textContent='Văn bản đọc';text.rows=5;text.placeholder='Nhập văn bản; đặt con trỏ giữa các câu để chèn nhịp nghỉ';text.value=item.text;text.setAttribute('aria-label','Văn bản đọc');text.addEventListener('input',()=>{item.text=text.value;item.settings.prosody_markup=/\|/.test(item.text);generate.disabled=generating||!item.text.trim();save()})
      pauseTools.className='studioPauseTools';pauseLabel.textContent='Chèn nhịp thủ công:';pauseTools.appendChild(pauseLabel);for(const [marker,label] of [['|','Ngắn'],['||','Vừa'],['|||','Dài']]){const button=document.createElement('button');button.type='button';button.className='secondary small';button.textContent=`${marker} ${label}`;button.title=`Chèn nhịp nghỉ ${label.toLocaleLowerCase('vi-VN')}`;button.disabled=isPodcastBrand;button.addEventListener('click',()=>{const start=text.selectionStart??text.value.length,end=text.selectionEnd??start;text.setRangeText(` ${marker} `,start,end,'end');item.text=text.value;item.settings.prosody_markup=true;generate.disabled=generating||!item.text.trim();save();text.focus()});pauseTools.appendChild(button)}
      controls.className='studioSegmentControls';voices.forEach(value=>{const option=document.createElement('option');option.value=value;option.textContent=value;option.selected=value===item.voice;voice.appendChild(option)})
      voice.disabled=!voices.length;voice.setAttribute('aria-label','Chọn giọng đọc');voice.addEventListener('change',()=>{if(item.voice===voice.value)return;item.voice=voice.value;item.voiceChanged=true;item.status='draft';if(playback.itemId===item.id)stopPlayback();save();setStatus(`Đã chọn giọng “${item.voice}”. Bấm Regenerate để tạo audio mới.`);render()})
      speedRow.className='studioSpeedControl';speedCaption.textContent='Tốc độ đọc';speed.type='range';speed.min='.5';speed.max='2';speed.step='.01';speed.value=isPodcastBrand ? .98 : item.speed;speed.disabled=isPodcastBrand;speed.setAttribute('aria-label','Tốc độ đọc');speedValue.textContent=`${Number(speed.value).toFixed(2)}×`;speed.addEventListener('input',()=>{item.speed=Number(speed.value);speedValue.textContent=`${item.speed.toFixed(2)}×`;save()});speedRow.append(speedCaption,speedValue,speed)
      generate.type='button';generate.className='primary small';generate.dataset.action='generate';generate.textContent=item.hasAudio?'↻ Regenerate':'▶ Generate';generate.disabled=generating||!item.text.trim();controls.classList.add('studioReadingControls');controls.append(voice,speedRow,generate)
      actions.className='studioSegmentActions';for(const [caption,action,disabled] of [['▶ Play','play',!item.hasAudio||item.voiceChanged],['⧉ Duplicate','duplicate',false],['↑ Lên','up',index===0],['↓ Xuống','down',index===project.segments.length-1],['Xóa','delete',false]]){const button=document.createElement('button');button.type='button';button.className='secondary small';button.dataset.action=action;button.textContent=caption;button.disabled=disabled;actions.appendChild(button)}
      details.className='muted small studioSettings';details.textContent=isPodcastBrand?'Đang dùng thiết lập tối ưu của Podcast Brand Voice.':`Advanced · T ${item.settings.temperature} · K ${item.settings.top_k} · P ${item.settings.top_p} · Rep ${item.settings.repetition_penalty} · Smart ${item.settings.smart_text_processing?'ON':'OFF'}`
      body.append(originalHint,text,pauseTools,controls,actions,details);editorHost.appendChild(editorPanel(index,voiceSummary.textContent,body))
    }else if(expanded&&item.type==='audio'){
      const body=document.createElement('div'),name=document.createElement('p'),volumeRow=document.createElement('label'),volumeLabel=document.createElement('span'),volume=document.createElement('input'),actions=document.createElement('div')
      body.className='studioSegmentBody';name.className='muted small';name.textContent=`🎵 ${item.name||'Audio Clip'} · ${formatTime(item.duration)} · clip cục bộ`
      volumeRow.className='studioVolumeControl';volumeLabel.textContent=`Âm lượng · ${Number(item.volume??100)}%`;volume.type='range';volume.min='0';volume.max='100';volume.value=String(item.volume??100);volume.setAttribute('aria-label','Âm lượng Audio Clip');volume.addEventListener('input',()=>{item.volume=Number(volume.value);volumeLabel.textContent=`Âm lượng · ${item.volume}%`;if(playback.itemId===item.id&&playback.audio)playback.audio.volume=item.volume/100;save()});volumeRow.append(volumeLabel,volume)
      actions.className='studioSegmentActions';for(const [caption,action,disabled] of [['▶ Play','play',!item.hasAudio],['Thay tệp','replace',false],['⧉ Duplicate','duplicate',false],['↑ Lên','up',index===0],['↓ Xuống','down',index===project.segments.length-1],['Xóa','delete',false]]){const button=document.createElement('button');button.type='button';button.className='secondary small';button.dataset.action=action;button.textContent=caption;button.disabled=disabled;actions.appendChild(button)}
      body.append(name,volumeRow,actions);editorHost.appendChild(editorPanel(index,voiceSummary.textContent,body))
    }else if(expanded&&item.type==='silence'){
      const body=document.createElement('div'),caption=document.createElement('strong'),controls=document.createElement('div'),input=document.createElement('input'),remove=document.createElement('button')
      body.className='studioSilenceBody';caption.textContent=`⏸ Nghỉ • ${(Number(item.duration_ms)/1000).toFixed(1)} giây`;input.type='number';input.min='.1';input.max='30';input.step='.1';input.value=(Number(item.duration_ms)/1000).toFixed(1);input.setAttribute('aria-label','Thời lượng nghỉ theo giây');input.addEventListener('change',()=>{const seconds=Math.min(30,Math.max(.1,Number(input.value)||2.5));item.duration_ms=Math.round(seconds*1000);item.duration=seconds;input.value=seconds.toFixed(1);save();render()});for(const seconds of [.5,1,1.5,2,2.5,3]){const preset=document.createElement('button');preset.type='button';preset.className='secondary small';preset.textContent=`${seconds}s`;preset.addEventListener('click',()=>{item.duration_ms=seconds*1000;item.duration=seconds;save();render()});controls.appendChild(preset)}remove.type='button';remove.className='secondary small';remove.textContent='Xóa';remove.addEventListener('click',()=>{project.segments.splice(index,1);save();render()});body.append(caption,input,controls,remove);editorHost.appendChild(editorPanel(index,voiceSummary.textContent,body))
    }
    track.appendChild(card)
    if(index<project.segments.length-1)track.appendChild(insertionPoint(index+1))
  })
  timelineFooter.appendChild(insertionPoint(project.segments.length))
  if(playback.state!=='idle'&&playback.itemId){const active=project.segments.find(item=>item.id===playback.itemId);if(active)requestAnimationFrame(()=>updateTimelinePlayback(active,playback.audio?.currentTime||0))}
  save()
}
function editorPanel(index,label,body){const panel=document.createElement('article'),heading=document.createElement('div'),title=document.createElement('strong'),hint=document.createElement('span');panel.className='studioEditorPanel';panel.dataset.id=project.segments[index].id;heading.className='studioEditorHeading';title.textContent=`Đang chỉnh Segment ${index+1}`;hint.textContent=label;heading.append(title,hint);panel.append(heading,body);return panel}
function currentIndex(button){const itemId=button.closest('[data-id]')?.dataset.id;return project.segments.findIndex(item=>item.id===itemId)}
function addSegment(){const next=segment();project.segments.push(next);expandedSegmentId=next.id;save();render();requestAnimationFrame(()=>segmentsEl.querySelector(`[data-id="${next.id}"] textarea`)?.focus())}
segmentsEl.addEventListener('click',event=>{const button=event.target.closest('[data-action]');if(!button||button.disabled)return;const index=currentIndex(button);if(index<0)return;const action=button.dataset.action,item=project.segments[index];if(action==='toggle'){expandedSegmentId=expandedSegmentId===item.id?null:item.id;render();return}if(action==='generate')generate(index);else if(action==='play')play(item);else if(action==='replace'){audioImport.dataset.replaceIndex=String(index);audioImport.click()}else if(action==='duplicate'){const copy=item.type==='audio'?{...item,id:id(),name:`${item.name||'Audio Clip'} (bản sao)`}:{...item,id:id(),hasAudio:false,status:'draft',duration:0,settings:{...item.settings}};project.segments.splice(index+1,0,copy);expandedSegmentId=copy.id;save();render()}else if(action==='up'||action==='down'){const target=index+(action==='up'?-1:1);[project.segments[index],project.segments[target]]=[project.segments[target],project.segments[index]];save();render()}else if(action==='delete'){project.segments.splice(index,1);expandedSegmentId=null;save();render()}})

function duration(blob){return new Promise(resolve=>{const audio=document.createElement('audio'),url=URL.createObjectURL(blob),done=value=>{URL.revokeObjectURL(url);resolve(value)};audio.onloadedmetadata=()=>done(Number.isFinite(audio.duration)?audio.duration:0);audio.onerror=()=>done(0);audio.src=url})}
async function importAudio(file,replaceIndex,insertIndex){if(!file)return;const allowed=/\.(wav|mp3|m4a)$/i.test(file.name||'');if(!allowed){setStatus('Chỉ hỗ trợ WAV, MP3 hoặc M4A.',true);return}const probe=new AudioContext();try{const decoded=await probe.decodeAudioData(await file.arrayBuffer());if(!decoded.length)throw Error();let item=Number.isInteger(replaceIndex)?project.segments[replaceIndex]:null;if(!item){item=audioClip();if(Number.isInteger(insertIndex))project.segments.splice(insertIndex,0,item);else project.segments.push(item)}item.type='audio';item.name=file.name||'Audio Clip';item.audioKey=item.audioKey||item.id;item.duration=decoded.duration;item.status='ready';item.hasAudio=true;item.volume=Number(item.volume??100);await putAudio(item.audioKey,file);expandedSegmentId=item.id;save();render();setStatus(`Đã thêm Audio Clip “${item.name}”.`)}catch(_){setStatus('Không đọc được tệp âm thanh này.',true)}finally{await probe.close()}}
function elapsed(ms){const seconds=Math.floor(ms/1000);return `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`}
async function waitForJob(job,index){const started=Date.now();for(;;){await new Promise(resolve=>setTimeout(resolve,1000));const response=await fetch(`${API}/api/long-audio/jobs/${job.job_id}`);if(!response.ok)throw Error('job-status');const state=await response.json(),total=state.total_chunks||'?';if(state.state==='RUNNING')setStatus(`Đang xử lý Segment ${index+1}: đoạn ${state.active_chunk||state.completed_chunks+1}/${total} · ${elapsed(Date.now()-started)}`);else if(state.state==='ASSEMBLING')setStatus(`Đang ghép audio cho Segment ${index+1} · ${elapsed(Date.now()-started)}`);if(state.state==='COMPLETED')return state;if(state.state==='CANCELLED')throw Error('cancelled');if(state.state==='FAILED')throw Error(state.error||'failed')}}
// The visible editor is the only synthesis source; old hidden scripts cannot override it.
function studioGenerationPayload(item){return {...item.settings,text:item.text,voice:item.voice,speed:item.speed,tts_script:null,prosody_markup:/\|/.test(item.text),idempotency_key:`studio-${Date.now().toString(36)}`}}
async function generate(index){const item=project.segments[index];if(!item||item.type!=='tts'||generating)return;if(!item.voice&&voices.length){item.voice=defaultVoice();save()}if(!item.voice){setStatus('Đang tải danh sách giọng. Hãy thử lại sau ít giây.',true);return}if(playback.itemId===item.id)stopPlayback();setGenerating(true);item.status='generating';expandedSegmentId=item.id;setStatus(`Đang tạo Segment ${index+1} bằng giọng “${item.voice}”...`);render();try{const payload=studioGenerationPayload(item);const response=await fetch(API+'/api/long-audio/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!response.ok){let detail='start';try{const body=await response.json();detail=body.detail||JSON.stringify(body)}catch(_){}throw Error(detail)}activeJob=await response.json();await waitForJob(activeJob,index);const audio=await fetch(`${API}/api/long-audio/jobs/${activeJob.job_id}/audio`);if(!audio.ok)throw Error('audio');const blob=await audio.blob();if(!blob||blob.size<=44)throw Error('audio');item.audioKey=item.id;await putAudio(item.audioKey,blob);item.duration=await duration(blob);item.status='ready';item.hasAudio=true;item.voiceChanged=false;save();setStatus(`Segment ${index+1} đã tạo lại bằng giọng “${item.voice}”.`)}catch(error){item.status=item.hasAudio?'ready':'draft';const detail=error.message==='cancelled'?'Đã hủy. Đoạn đang tạo sẽ dừng sau lần suy luận hiện tại.':`Không thể tạo Segment ${index+1}: ${error.message}`;setStatus(detail,true)}finally{activeJob=null;setGenerating(false);render()}}
function stopPlayback(){playback.queueToken++;if(playback.silenceTimer)clearTimeout(playback.silenceTimer);if(playback.silenceFrame)cancelAnimationFrame(playback.silenceFrame);if(playback.audio){playback.audio.pause();playback.audio.currentTime=0}if(playback.objectUrl)URL.revokeObjectURL(playback.objectUrl);Object.assign(playback,{state:'idle',mode:null,audio:null,itemId:null,silenceTimer:null,silenceFrame:null,objectUrl:null});updatePlaybackControls();render()}
function togglePlaybackPause(){if(playback.state==='idle')return;if(playback.state==='playing'){playback.audio?.pause();playback.state='paused'}else{playback.audio?.play();playback.state='playing'}updatePlaybackControls();render()}
function updateTimelinePlayback(item,elapsed=0){const card=segmentsEl.querySelector(`.studioTimelineTrack [data-id="${item.id}"]`),head=segmentsEl.querySelector('.studioPlayhead'),clock=document.getElementById('studioTimelineClock');if(!card||!head)return;const duration=Math.max(.01,itemDuration(item)),progress=Math.max(0,Math.min(1,Number(elapsed)||0)/duration),before=project.segments.slice(0,project.segments.findIndex(entry=>entry.id===item.id)).reduce((total,entry)=>total+itemDuration(entry),0),x=card.offsetLeft+card.offsetWidth*progress;card.style.setProperty('--play-progress',`${progress*100}%`);head.style.transform=`translateX(${x}px)`;head.classList.add('active');if(clock)clock.textContent=`${formatTime(before+(Number(elapsed)||0))} / ${formatTime(metrics().duration)}`;const viewport=segmentsEl.querySelector('.studioTimeline');if(viewport&&((x-viewport.scrollLeft)<70||(x-viewport.scrollLeft)>viewport.clientWidth-90))viewport.scrollLeft=Math.max(0,x-viewport.clientWidth*.45)}
function bindPlaybackProgress(audio,item){audio.ontimeupdate=()=>{const progress=segmentsEl.querySelector(`[data-id="${item.id}"] .studioPlaybackProgress`);if(progress)progress.textContent=`Đang phát ${formatTime(audio.currentTime)} / ${formatTime(audio.duration||itemDuration(item))}`;updateTimelinePlayback(item,audio.currentTime)}}
function playSilence(item,token){return new Promise(resolve=>{const duration=Math.max(.1,Math.min(30,Number(item.duration_ms)||2500))/1000,started=performance.now(),tick=now=>{if(token!==playback.queueToken)return resolve();const elapsed=Math.min(duration,(now-started)/1000);updateTimelinePlayback(item,elapsed);if(elapsed>=duration){playback.silenceFrame=null;return resolve()}playback.silenceFrame=requestAnimationFrame(tick)};playback.silenceFrame=requestAnimationFrame(tick)})}
async function play(item){if(playback.itemId===item.id&&playback.state!=='idle'){togglePlaybackPause();return}stopPlayback();if(item.type==='silence'){setStatus('Khoảng nghỉ không phát riêng.');return}const blob=await getAudio(item.audioKey||item.id);if(!(blob instanceof Blob)){item.hasAudio=false;save();render();setStatus('Không tìm thấy audio của đoạn này.',true);return}const audio=new Audio(URL.createObjectURL(blob));Object.assign(playback,{state:'playing',mode:'single',audio,itemId:item.id,objectUrl:audio.src});audio.volume=Math.max(0,Math.min(1,Number(item.volume??100)/100));bindPlaybackProgress(audio,item);audio.onended=()=>stopPlayback();await audio.play();updatePlaybackControls();render()}
async function playAll(){stopPlayback();const token=playback.queueToken,queue=project.segments.slice();playback.mode='project';for(const item of queue){if(token!==playback.queueToken)return;playback.itemId=item.id;playback.state='playing';updatePlaybackControls();render();if(item.type==='silence'){await playSilence(item,token);continue}if(!item.hasAudio||item.voiceChanged)continue;const blob=await getAudio(item.audioKey||item.id);if(!(blob instanceof Blob))continue;await new Promise(async resolve=>{const audio=new Audio(URL.createObjectURL(blob));playback.audio=audio;playback.objectUrl=audio.src;audio.volume=Math.max(0,Math.min(1,Number(item.volume??100)/100));bindPlaybackProgress(audio,item);audio.onended=resolve;audio.onerror=resolve;await audio.play()});if(token!==playback.queueToken)return}if(token===playback.queueToken)stopPlayback()}
function encodeWav(channels,sr){const length=channels[0].length,buffer=new ArrayBuffer(44+length*channels.length*2),view=new DataView(buffer),u32=(at,value)=>view.setUint32(at,value,true);view.setUint32(0,0x46464952,true);u32(4,36+length*channels.length*2);view.setUint32(8,0x45564157,true);view.setUint32(12,0x20746d66,true);u32(16,16);view.setUint16(20,1,true);view.setUint16(22,channels.length,true);u32(24,sr);u32(28,sr*channels.length*2);view.setUint16(32,channels.length*2);view.setUint16(34,16);view.setUint32(36,0x61746164,true);u32(40,length*channels.length*2);let at=44;for(let i=0;i<length;i++)for(const channel of channels){const value=Math.max(-1,Math.min(1,channel[i]));view.setInt16(at,value<0?value*0x8000:value*0x7fff,true);at+=2}return new Blob([buffer],{type:'audio/wav'})}
async function resampleBuffer(buffer,targetRate){if(buffer.sampleRate===targetRate)return buffer;const ctx=new OfflineAudioContext(buffer.numberOfChannels,Math.ceil(buffer.duration*targetRate),targetRate),source=ctx.createBufferSource();source.buffer=buffer;source.connect(ctx.destination);source.start();return ctx.startRendering()}
async function exportWav(){const timeline=project.segments.filter(item=>item.hasAudio||item.type==='silence');if(!timeline.length){setStatus('Chưa có timeline item nào để xuất WAV.',true);return}const context=new AudioContext();try{const decoded=[];for(const item of timeline)if(item.type!=='silence'){const blob=await getAudio(item.audioKey||item.id);if(!(blob instanceof Blob))throw Error();decoded.push({item,buffer:await context.decodeAudioData(await blob.arrayBuffer())})}if(!decoded.length)throw Error();const targetRate=decoded.find(entry=>entry.item.type==='tts')?.buffer.sampleRate||decoded[0].buffer.sampleRate,channels=Math.max(...decoded.map(entry=>entry.buffer.numberOfChannels)),buffers=[];for(const item of timeline){if(item.type==='silence')buffers.push({item,buffer:null,length:Math.round(Math.max(100,Math.min(30000,Number(item.duration_ms)||2500))*targetRate/1000)});else{const entry=decoded.find(candidate=>candidate.item===item),buffer=await resampleBuffer(entry.buffer,targetRate);buffers.push({item,buffer,length:buffer.length})}}const length=buffers.reduce((total,entry)=>total+entry.length,0),merged=Array.from({length:channels},()=>new Float32Array(length));let offset=0;for(const {item,buffer,length:partLength} of buffers){if(buffer){const gain=item.type==='audio'?Math.max(0,Math.min(1,Number(item.volume??100)/100)):1;for(let channel=0;channel<channels;channel++){const source=buffer.getChannelData(Math.min(channel,buffer.numberOfChannels-1));for(let i=0;i<source.length;i++)merged[channel][offset+i]=source[i]*gain}}offset+=partLength}const url=URL.createObjectURL(encodeWav(merged,targetRate)),link=document.createElement('a');link.href=url;link.download=`${project.title.replace(/[^\w-]+/g,'-')||'audio-project'}.wav`;link.click();setTimeout(()=>URL.revokeObjectURL(url),2000);setStatus('Đã xuất WAV.')}catch(_){setStatus('Không thể xuất WAV. Hãy kiểm tra các timeline item đã sẵn sàng.',true)}finally{context.close()}}

async function loadVoices(){try{const [health,response]=await Promise.all([fetch(API+'/api/health'),fetch(API+'/api/voices')]);const info=health.ok?await health.json():null;healthEl.textContent=info?'● TTS cục bộ đang hoạt động':'● Backend không khả dụng';healthEl.style.color=info?'#78e08f':'#ff9b9b';const data=await response.json();voices=(data.voices||[]).map(item=>item.id).filter(Boolean);render()}catch(_){healthEl.textContent='● Backend không khả dụng';healthEl.style.color='#ff9b9b'}}
function applyTheme(theme){document.documentElement.setAttribute('data-theme',theme);localStorage.setItem('theme',theme);themeToggle.textContent=theme==='light'?'☀️':'🌙'}
themeToggle.addEventListener('click',()=>applyTheme(document.documentElement.getAttribute('data-theme')==='light'?'dark':'light'))
addBtn.addEventListener('click',addSegment);fabAddBtn?.addEventListener('click',addSegment)
addAudioBtn?.addEventListener('click',()=>{delete audioImport.dataset.replaceIndex;audioImport.click()})
audioImport.addEventListener('change',async()=>{const replaceIndex=Number(audioImport.dataset.replaceIndex),insertIndex=Number(audioImport.dataset.insertIndex);await importAudio(audioImport.files?.[0],Number.isInteger(replaceIndex)?replaceIndex:null,Number.isInteger(insertIndex)?insertIndex:null);audioImport.value='';delete audioImport.dataset.replaceIndex;delete audioImport.dataset.insertIndex})
soundPickerClose?.addEventListener('click',closeSoundPicker)
soundPicker?.addEventListener('close',stopSoundPreview)
soundPickerUpload?.addEventListener('click',()=>{if(!Number.isInteger(soundInsertIndex))return;audioImport.dataset.insertIndex=String(soundInsertIndex);delete audioImport.dataset.replaceIndex;closeSoundPicker();audioImport.click()})
saveProjectBtn.addEventListener('click',()=>{save();setStatus('Đã lưu project cục bộ.')})
cancelBtn.addEventListener('click',async()=>{if(!activeJob)return;cancelBtn.disabled=true;await fetch(`${API}/api/long-audio/jobs/${activeJob.job_id}`,{method:'DELETE'}).catch(()=>{});setStatus('Đã yêu cầu hủy; VieNeu sẽ dừng trước đoạn kế tiếp.')})
newProjectBtn.addEventListener('click',()=>{save();project=normalize(null);projects.push(project);expandedSegmentId=null;titleInput.value=project.title;save();render();setStatus('Đã tạo project mới. Project cũ vẫn được lưu trong danh sách.')})
playAllBtn.addEventListener('click',playAll);pauseBtn.addEventListener('click',togglePlaybackPause);stopBtn.addEventListener('click',stopPlayback);exportBtn.addEventListener('click',exportWav)
inspectorPlayAllBtn?.addEventListener('click',playAll);inspectorExportBtn?.addEventListener('click',exportWav)
projectSearch?.addEventListener('input',()=>{projectSearchQuery=projectSearch.value;renderProjectList()})
titleInput.addEventListener('input',save)
document.addEventListener('click',event=>{if(!event.target.closest('.studioInsertion')){document.querySelectorAll('.studioInsertionMenu').forEach(menu=>menu.hidden=true);document.querySelectorAll('.studioInsertButton').forEach(button=>button.setAttribute('aria-expanded','false'))}})
applyTheme(localStorage.getItem('theme')||'dark');load();loadVoices()
