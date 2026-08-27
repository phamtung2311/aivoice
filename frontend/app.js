const API = 'http://127.0.0.1:8000'
const AIVOICE_FRONTEND_BUILD = '21.0'

const voiceSelect = document.getElementById('voice')
const speedInput = document.getElementById('speed')
const speedVal = document.getElementById('speedVal')
const textArea = document.getElementById('text')
const speakBtn = document.getElementById('speak')
const status = document.getElementById('status')
const audioEl = document.getElementById('audio')
const uploadInput = document.getElementById('uploadInput')
const charCount = document.getElementById('charCount')
const healthEl = document.getElementById('health')
const downloadBtn = document.getElementById('downloadBtn')
const cancelBtn = document.getElementById('cancelBtn')
const clearTextBtn = document.getElementById('clearTextBtn')
const historyList = document.getElementById('historyList')
const clearHistoryBtn = document.getElementById('clearHistoryBtn')
const progressBar = document.getElementById('progressBar')
const curTime = document.getElementById('curTime')
const durTime = document.getElementById('durTime')
const themeToggle = document.getElementById('themeToggle')
// saved-voices controls
const saveVoiceNameInput = document.getElementById('saveVoiceName')
const saveVoiceBtn = document.getElementById('saveVoiceBtn')
const savedVoicesList = document.getElementById('savedVoicesList')
const saveVoiceInfo = document.getElementById('saveVoiceInfo')
// voice preview list (Phase 13)
const voicePreviewList = document.getElementById('voicePreviewList')
// Phase 14: clone dropzone + result card
const cloneDropzone = document.getElementById('cloneDropzone')
const cloneFileMeta = document.getElementById('cloneFileMeta')
const cloneFileNameEl = document.getElementById('cloneFileName')
const cloneFileSizeEl = document.getElementById('cloneFileSize')
const cloneFileFormatEl = document.getElementById('cloneFileFormat')
const cloneFileRemove = document.getElementById('cloneFileRemove')
const resultPlaceholder = document.getElementById('resultPlaceholder')
const resultSuccess = document.getElementById('resultSuccess')
const regenerateBtn = document.getElementById('regenerateBtn')
// Phase 18: Voice Lab controls
const voiceLabRuntime = document.getElementById('voiceLabRuntime')
const voiceLabSentence = document.getElementById('voiceLabSentence')
const voiceLabSentenceText = document.getElementById('voiceLabSentenceText')
const voiceLabRound = document.getElementById('voiceLabRound')
const voiceLabRun = document.getElementById('voiceLabRun')
const voiceLabTemperature = document.getElementById('voiceLabTemperature')
const voiceLabTopP = document.getElementById('voiceLabTopP')
const voiceLabRepetition = document.getElementById('voiceLabRepetition')
const voiceLabTopK = document.getElementById('voiceLabTopK')
const voiceLabSpeed = document.getElementById('voiceLabSpeed')
const voiceLabGenerate = document.getElementById('voiceLabGenerate')
const voiceLabStatus = document.getElementById('voiceLabStatus')
const voiceLabAudio = document.getElementById('voiceLabAudio')
const voiceLabCurrentSample = document.getElementById('voiceLabCurrentSample')
const voiceLabSaveVoiceName = document.getElementById('voiceLabSaveVoiceName')
const voiceLabSaveVoiceDescription = document.getElementById('voiceLabSaveVoiceDescription')
const voiceLabSaveVoiceBtn = document.getElementById('voiceLabSaveVoiceBtn')
const voiceLabSaveVoiceHelp = document.getElementById('voiceLabSaveVoiceHelp')
const voiceLabRubric = document.getElementById('voiceLabRubric')
const voiceLabNotes = document.getElementById('voiceLabNotes')
const voiceLabMissingWords = document.getElementById('voiceLabMissingWords')
const voiceLabMissingWordNote = document.getElementById('voiceLabMissingWordNote')
const voiceLabCandidateVoice = document.getElementById('voiceLabCandidateVoice')
const voiceLabCandidateTemperature = document.getElementById('voiceLabCandidateTemperature')
const voiceLabSelectTemperature = document.getElementById('voiceLabSelectTemperature')
const voiceLabCandidateStatus = document.getElementById('voiceLabCandidateStatus')
const voiceLabSaveEvaluation = document.getElementById('voiceLabSaveEvaluation')
const voiceLabExperimentList = document.getElementById('voiceLabExperimentList')
const voiceLabRefresh = document.getElementById('voiceLabRefresh')
const voiceLabReferenceInputs = {
  reference_a: document.getElementById('voiceLabRefAInput'),
  reference_b: document.getElementById('voiceLabRefBInput'),
  reference_c: document.getElementById('voiceLabRefCInput'),
}
const voiceLabReferenceMetaEls = {
  reference_a: document.getElementById('voiceLabRefAMeta'),
  reference_b: document.getElementById('voiceLabRefBMeta'),
  reference_c: document.getElementById('voiceLabRefCMeta'),
}
const CLONE_ACCEPTED_EXTENSIONS = ['.wav', '.mp3', '.m4a']
const SAVE_VOICE_FORMAT_HELP = 'Hỗ trợ lưu giọng từ WAV, MP3 và M4A. File sẽ được xử lý cục bộ trên máy.'

let currentBlobUrl = null
let currentBlob = null
let maxTextLength = 10000 // fallback; will try to read from /api/health if provided
const TTS_REQUEST_TIMEOUT_MS = 180000
const AUDIO_DECODE_TIMEOUT_MS = 10000
const REF_MAX_SECONDS = 8.0
const REF_MAX_BYTES = 5 * 1024 * 1024 // 5 MiB, must match server REF_MAX_BYTES
const HISTORY_STORAGE_KEY = 'tts_history'
const SELECTED_VOICE_STORAGE_KEY = 'aivoice_selected_voice'
const HISTORY_MAX_ITEMS = 20
const HISTORY_TEXT_MAX_LENGTH = 10000
const TXT_FILE_MAX_BYTES = 1024 * 1024
let activeTtsRequest = null
let nextTtsRequestId = 0
let isGenerating = false
let savedVoiceNames = []
let validVoiceIds = new Set()
let voicesReady = false
let voicesLoadSequence = 0
let voiceLabCorpus = null
let voiceLabExperiments = []
let voiceLabCurrentExperimentId = null
let voiceLabCurrentAudioUrl = null
let voiceLabCurrentSampleState = null
let voiceLabGenerating = false
const voiceLabReferences = new Map()
let temperatureCandidates = new Map()

// ── Phase 13: constants & state ──────────────────────────────────────────────
// Fixed sample sentence used ONLY for voice preview (never inserted into the
// main textarea, never added to history).
const VOICE_PREVIEW_TEXT = 'Xin chào, đây là giọng đọc mẫu của aivoice.'
// Maximum number of history entries that keep their generated audio.
const HISTORY_AUDIO_MAX = 10
// IndexedDB database for persisted history audio blobs.
const IDB_NAME = 'aivoice_history'
// Version 3 additively repairs installations missing either audio store.
const IDB_VERSION = 3
const IDB_STORE = 'history_audio'
const IDB_VOICE_LAB_STORE = 'voice_lab_audio'
const VOICE_LAB_AUDIO_MAX = 25
let historyPlaybackUrl = null
let lastStorageError = null

function storageErrorSummary(error){
  const name = error && error.name ? String(error.name) : 'Error'
  const message = error && error.message ? String(error.message) : String(error || 'Unknown storage error')
  return `${name}: ${message}`.slice(0, 300)
}

function recordStorageError(error){
  lastStorageError = storageErrorSummary(error)
  return error
}

function storageFailureUserMessage(baseMessage){
  return lastStorageError && lastStorageError.startsWith('BlockedError:')
    ? `${baseMessage} Hãy đóng các tab AIVoice cũ rồi tải lại trang.`
    : baseMessage
}

console.info(`[AIVoice] frontend build ${AIVOICE_FRONTEND_BUILD}`, {origin:window.location.origin})

function setStatus(msg, isError=false){
  status.textContent = msg
  status.style.color = isError ? '#ff9b9b' : ''
  status.setAttribute('role', isError ? 'alert' : 'status')
  status.setAttribute('aria-live', isError ? 'assertive' : 'polite')
  status.setAttribute('aria-atomic', 'true')
}

function setGeneratingState(generating){
  isGenerating = generating
  updateTextValidation()
  speakBtn.setAttribute('aria-busy', String(generating))
  speakBtn.disabled = generating
  if(generating && speakBtn.dataset.originalLabel === undefined){
    speakBtn.dataset.originalLabel = speakBtn.textContent
  }
  if(generating){
    const usingClone = !!selectedRefFile
    speakBtn.textContent = usingClone ? '⏳ Đang xử lý tham chiếu & tạo giọng...' : '⏳ Đang tạo giọng...'
  }else{
    if(speakBtn.dataset.originalLabel !== undefined) speakBtn.textContent = speakBtn.dataset.originalLabel
  }
  cancelBtn.hidden = !generating
  cancelBtn.disabled = !generating
}

function isActiveRequest(request){ return activeTtsRequest === request }

function finishRequest(request){
  if(!isActiveRequest(request)) return false
  if(request.timeoutId !== null) clearTimeout(request.timeoutId)
  activeTtsRequest = null
  setGeneratingState(false)
  return true
}

function abortActiveRequest(reason, announce=true){
  const request = activeTtsRequest
  if(!request) return false

  request.abortReason = reason
  finishRequest(request)
  request.controller.abort()

  if(announce){
    if(reason === 'timeout'){
      setStatus('Chuyển đổi mất quá nhiều thời gian. Hãy thử lại với đoạn văn ngắn hơn.', true)
    }else{
      setStatus('Đã hủy chuyển đổi. Bạn có thể thử lại.')
    }
  }
  return true
}

function safeApiDetail(detail){
  return typeof detail === 'string' && detail.trim() ? detail.trim().slice(0, 300) : ''
}

async function readApiErrorDetail(response){
  try{
    const body = await response.clone().json()
    return safeApiDetail(body && body.detail)
  }catch(_error){ return '' }
}

function userMessageForHttpStatus(statusCode, detail=''){
  const safeDetail = safeApiDetail(detail)
  if(safeDetail) return safeDetail
  if(statusCode === 400) return 'Yêu cầu không hợp lệ. Hãy kiểm tra văn bản và giọng đọc rồi thử lại.'
  if(statusCode === 413) return `Văn bản quá dài. Hãy rút ngắn xuống tối đa ${maxTextLength} ký tự.`
  if(statusCode === 422) return 'Dữ liệu không hợp lệ. Hãy kiểm tra văn bản, giọng đọc và tốc độ rồi thử lại.'
  if(statusCode >= 400 && statusCode < 500) return 'Yêu cầu không thể được xử lý. Hãy kiểm tra nội dung rồi thử lại.'
  if(statusCode >= 500) return 'Máy chủ TTS gặp lỗi khi xử lý. Hãy thử lại.'
  return 'Không thể tạo âm thanh. Hãy thử lại.'
}

function isExpectedAudioResponse(response, blob){
  const contentType = (response.headers.get('content-type') || '').toLowerCase()
  const mediaType = contentType.split(';', 1)[0].trim()
  return response.body && mediaType === 'audio/wav' && blob && blob.size > 44 && blob.type.toLowerCase() === 'audio/wav'
}

function setHealth(online, label){
  healthEl.textContent = (online? '● TTS cục bộ đang hoạt động' : '● Backend không khả dụng') + (label? ' — '+label : '')
  healthEl.style.color = online? '#78e08f' : '#ff9b9b'
}

function formatTime(sec){
  if(!isFinite(sec)) return '00:00'
  const s = Math.floor(sec%60).toString().padStart(2,'0')
  const m = Math.floor(sec/60).toString().padStart(2,'0')
  return `${m}:${s}`
}

function formatCharacterCount(count){ return Number(count).toLocaleString('vi-VN') }

function updateTextValidation(){
  const text = textArea.value || ''
  const length = text.length
  const remaining = maxTextLength - length
  const nearLimit = length >= Math.ceil(maxTextLength * 0.9) && remaining >= 0
  const overLimit = remaining < 0

  charCount.classList.toggle('counterWarning', nearLimit)
  charCount.classList.toggle('counterError', overLimit)
  if(overLimit){
    charCount.textContent = `${formatCharacterCount(length)} / ${formatCharacterCount(maxTextLength)} ký tự · Vượt ${formatCharacterCount(Math.abs(remaining))} ký tự`
  }else if(nearLimit){
    charCount.textContent = `${formatCharacterCount(length)} / ${formatCharacterCount(maxTextLength)} ký tự · Còn ${formatCharacterCount(remaining)} ký tự`
  }else{
    charCount.textContent = `${formatCharacterCount(length)} / ${formatCharacterCount(maxTextLength)} ký tự`
  }
  charCount.setAttribute('aria-label', `${formatCharacterCount(length)} trên ${formatCharacterCount(maxTextLength)} ký tự`)

  clearTextBtn.disabled = length === 0
  speakBtn.disabled = isGenerating || !voicesReady || !text.trim() || overLimit
}

function resolveValidVoice(preferredVoice){
  const candidates = [preferredVoice, voiceSelect.value, localStorage.getItem(SELECTED_VOICE_STORAGE_KEY)]
  for(const candidate of candidates){
    if(candidate && validVoiceIds.has(candidate)) return candidate
  }
  return validVoiceIds.values().next().value || null
}

function selectValidVoice(preferredVoice){
  const selected = resolveValidVoice(preferredVoice)
  if(!selected) return null
  voiceSelect.value = selected
  localStorage.setItem(SELECTED_VOICE_STORAGE_KEY, selected)
  return selected
}

// load voices and health
async function loadHealthAndVoices(preferredVoice=null){
  const loadId = ++voicesLoadSequence
  try{
    const r = await fetch(API + '/api/health')
    if(r.ok){
      const j = await r.json()
      if(j.max_text_length) maxTextLength = j.max_text_length
      setHealth(true, j.model || '')
      if(voiceLabRuntime){
        const runtimeName = [j.engine_library, j.engine_version, j.runtime_family, j.runtime_backend, j.device].filter(Boolean).join(' · ')
        voiceLabRuntime.textContent = runtimeName || 'Runtime metadata chưa khả dụng'
      }
      updateTextValidation()
    }else{
      setHealth(false)
    }
  }catch(e){ setHealth(false) }

  try{
    const res = await fetch(API + '/api/voices')
    if(!res.ok) throw new Error('voices failed')
    const j = await res.json()
    if(loadId !== voicesLoadSequence) return false
    const voicesList = (Array.isArray(j.voices) ? j.voices : (Array.isArray(j) ? j : []))
      .filter(v => v && typeof v.id === 'string' && v.id.trim())
    if(!voicesList.length) throw new Error('Backend returned no valid voices')
    // Group by type (preset vs saved); keep legacy fallback (no type => preset).
    const presets = []
    const saved = []
    voicesList.forEach(v => {
      const item = { id: v.id, name: v.name, type: v.type === 'saved' ? 'saved' : 'preset' }
      ;(item.type === 'saved' ? saved : presets).push(item)
    })
    voiceSelect.innerHTML = ''
    voiceSelect.disabled = false
    const addGroup = (label, items) => {
      if(!items.length) return
      const g = document.createElement('optgroup'); g.label = label
      items.forEach(v => {
        const opt = document.createElement('option')
        opt.value = v.id
        opt.textContent = v.name
        g.appendChild(opt)
      })
      voiceSelect.appendChild(g)
    }
    addGroup('Giọng mặc định', presets)
    addGroup('Giọng đã lưu', saved)
    validVoiceIds = new Set(voicesList.map(v => v.id))
    voicesReady = Boolean(selectValidVoice(preferredVoice))
    // maintain a display map of saved voices for the saved-voices panel
    savedVoiceNames = saved.map(v => v.id)
    // Phase 13: preview list (preset + saved voices with per-voice ▶ button)
    renderVoicePreviewList(presets, saved)
    renderSavedVoices()
    renderTemperatureCandidateState()
    updateTextValidation()
    return true
  }catch(e){
    if(loadId !== voicesLoadSequence) return false
    console.error(e)
    validVoiceIds = new Set()
    voicesReady = false
    voiceSelect.innerHTML = '<option value="">Không tải được danh sách giọng</option>'
    voiceSelect.disabled = true
    updateTextValidation()
    setStatus('Không thể tải danh sách giọng. Hãy kiểm tra backend rồi tải lại trang.', true)
    return false
  }
}

// theme
function applyTheme(theme){
  const nextTheme = theme === 'light' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', nextTheme)
  themeToggle.textContent = nextTheme === 'dark' ? '☀' : '🌙'
  themeToggle.setAttribute('aria-label', nextTheme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối')
  themeToggle.setAttribute('aria-pressed', String(nextTheme === 'light'))
  localStorage.setItem('theme', nextTheme)
}
themeToggle.addEventListener('click', ()=>{
  const current = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark'
  const next = current === 'dark' ? 'light' : 'dark'
  applyTheme(next)
})
const savedTheme = localStorage.getItem('theme') || 'dark'
applyTheme(savedTheme)

speedInput.addEventListener('input', ()=>{ speedVal.textContent = parseFloat(speedInput.value).toFixed(1) + 'x' })
voiceSelect.addEventListener('change', ()=>{
  if(validVoiceIds.has(voiceSelect.value)) localStorage.setItem(SELECTED_VOICE_STORAGE_KEY, voiceSelect.value)
  renderTemperatureCandidateState()
})
textArea.addEventListener('input', updateTextValidation)

const emotionSelect = document.getElementById('emotion')
const cloneInput = document.getElementById('cloneInput')
const cloneInfo = document.getElementById('cloneInfo')
let selectedRefFile = null

// Advanced sampling controls
const advancedToggle = document.getElementById('advancedToggle')
const advancedContents = document.getElementById('advancedContents')
const temperatureInput = document.getElementById('temperatureInput')
const topKInput = document.getElementById('topKInput')
const topPInput = document.getElementById('topPInput')
const repetitionPenaltyInput = document.getElementById('repetitionPenaltyInput')
const resetSamplingBtn = document.getElementById('resetSamplingBtn')
let advancedOpen = false

if(advancedToggle){
  advancedToggle.addEventListener('click', ()=>{
    advancedOpen = !advancedOpen
    advancedToggle.setAttribute('aria-expanded', String(advancedOpen))
    if(advancedContents) advancedContents.hidden = !advancedOpen
  })
}
if(resetSamplingBtn){
  resetSamplingBtn.addEventListener('click', ()=>{
    const preferred = preferredSamplingForVoice(voiceSelect.value)
    if(temperatureInput) temperatureInput.value = String(preferred?.temperature ?? 0.8)
    if(topKInput) topKInput.value = String(preferred?.top_k ?? 25)
    if(topPInput) topPInput.value = String(preferred?.top_p ?? 0.95)
    if(repetitionPenaltyInput) repetitionPenaltyInput.value = String(preferred?.repetition_penalty ?? 1.2)
  })
}

async function probeWavDuration(file){
  try{
    const blob = new Blob([await file.arrayBuffer()], {type: 'audio/wav'})
    const controller = new AbortController()
    await waitForAudioDecode(blob, controller)
    const audio = document.createElement('audio')
    const url = URL.createObjectURL(blob)
    return await new Promise((resolve, reject)=>{
      audio.addEventListener('loadedmetadata', ()=>{ const d = audio.duration; URL.revokeObjectURL(url); resolve(d) })
      audio.addEventListener('error', ()=>{ URL.revokeObjectURL(url); reject(new Error('invalid-audio')) })
      audio.src = url
      audio.load()
    })
  }catch(e){ throw e }
}

function clearCloneFile(){
  selectedRefFile = null
  if(cloneInput) cloneInput.value = ''
  if(cloneFileMeta) cloneFileMeta.hidden = true
  updateSaveVoiceState()
}

function formatFileSize(bytes){
  if(bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  return (bytes / 1024).toFixed(0) + ' KB'
}

function extensionOf(name){
  const normalized = String(name || '').toLowerCase()
  const i = normalized.lastIndexOf('.')
  return i === -1 ? '' : normalized.slice(i)
}

function canSaveVoiceReference(file){
  return Boolean(file && CLONE_ACCEPTED_EXTENSIONS.includes(extensionOf(file.name)))
}

async function handleCloneFile(f){
  if(!f){ clearCloneFile(); return }
  const ext = extensionOf(f.name)
  if(!CLONE_ACCEPTED_EXTENSIONS.includes(ext)){
    setStatus('Định dạng không được hỗ trợ. Vui lòng dùng tệp WAV, M4A hoặc MP3.', true)
    clearCloneFile()
    return
  }
  if(f.size > REF_MAX_BYTES){
    setStatus(`Tệp tham chiếu quá lớn (${formatFileSize(f.size)}). Tối đa 5 MB.`, true)
    clearCloneFile()
    return
  }

  // Show metadata immediately for every supported format.
  selectedRefFile = f
  if(cloneFileMeta){
    cloneFileMeta.hidden = false
    if(cloneFileNameEl) cloneFileNameEl.textContent = f.name
    if(cloneFileSizeEl) cloneFileSizeEl.textContent = formatFileSize(f.size)
    if(cloneFileFormatEl) cloneFileFormatEl.textContent = ext.slice(1).toUpperCase()
  }
  updateSaveVoiceState()

  if(cloneInfo) cloneInfo.textContent = 'Đang kiểm tra tệp âm thanh...'
  if(ext !== '.wav'){
    // Server converts M4A/MP3 to WAV during generation; duration is validated there.
    if(cloneInfo) cloneInfo.textContent = `✓ Đã chuẩn bị file âm thanh ✓ — sẽ tự động chuyển đổi sang WAV khi tạo giọng (${formatFileSize(f.size)})`
    setStatus(`Đã chọn tệp ${ext.slice(1).toUpperCase()}. Bấm “Tạo giọng nói” để dùng giọng này.`)
    return
  }
  try{
    const dur = await probeWavDuration(f)
    if(dur > REF_MAX_SECONDS){
      setStatus(`Tệp tham chiếu quá dài (${dur.toFixed(1)}s). Tối đa ${REF_MAX_SECONDS}s.`, true)
      clearCloneFile()
      if(cloneInfo) cloneInfo.textContent = ''
      return
    }
    if(cloneInfo) cloneInfo.textContent = `✓ Đã chuẩn bị file âm thanh ✓ — ${dur.toFixed(1)}s · ${formatFileSize(f.size)}. Bấm “Tạo giọng nói” hoặc lưu làm giọng cá nhân bên dưới.`
    setStatus('Đã chọn tệp WAV tham chiếu.')
  }catch(e){
    console.error('WAV probe failed:', e)
    setStatus('Không thể đọc tệp WAV. Tệp có thể bị hỏng.', true)
    clearCloneFile()
    if(cloneInfo) cloneInfo.textContent = ''
  }
}

if(cloneInput){
  cloneInput.addEventListener('change', async (ev)=>{
    const f = ev.target.files && ev.target.files[0]
    await handleCloneFile(f)
  })
}
if(cloneDropzone){
  cloneDropzone.addEventListener('click', (e)=>{
    // Avoid re-opening the picker when clicking the nested label.
    if(e.target && e.target.closest && e.target.closest('label')) return
    if(cloneInput) cloneInput.click()
  })
  cloneDropzone.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); if(cloneInput) cloneInput.click() }
  })
  ;['dragenter','dragover'].forEach(ev => cloneDropzone.addEventListener(ev, (e)=>{ e.preventDefault(); cloneDropzone.classList.add('drag') }))
  ;['dragleave','drop'].forEach(ev => cloneDropzone.addEventListener(ev, (e)=>{ e.preventDefault(); cloneDropzone.classList.remove('drag') }))
  cloneDropzone.addEventListener('drop', async (e)=>{
    const files = e.dataTransfer && e.dataTransfer.files
    if(!files || files.length === 0){ setStatus('Không tìm thấy tệp âm thanh để thả vào.', true); return }
    if(files.length > 1){ setStatus('Chỉ hỗ trợ một tệp âm thanh mỗi lần.', true); return }
    await handleCloneFile(files[0])
  })
}
if(cloneFileRemove){
  cloneFileRemove.addEventListener('click', ()=>{
    clearCloneFile()
    if(cloneInfo) cloneInfo.textContent = ''
    setStatus('Đã xóa tệp tham chiếu.')
  })
}

// ── Phase 12.1: emotion insertion toolbar (inserts native inline cues at cursor)
document.querySelectorAll('[data-emotion-tag]').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    const tag = btn.getAttribute('data-emotion-tag')
    if(!tag) return
    const el = textArea
    const start = el.selectionStart ?? el.value.length
    const end = el.selectionEnd ?? el.value.length
    const before = el.value.slice(0, start)
    const after = el.value.slice(end)
    const insert = (before && !/\n$/.test(before) ? '\n' : '') + tag + '\n'
    el.value = before + insert + after
    const pos = start + insert.length
    el.focus()
    el.setSelectionRange(pos, pos)
    el.dispatchEvent(new Event('input'))
    setStatus(`Đã chèn biểu cảm ${tag}.`)
  })
})

// ── Phase 12.1: saved voice profiles ──────────────────────────────────────────
function updateSaveVoiceState(){
  const name = (saveVoiceNameInput ? saveVoiceNameInput.value : '').trim()
  const canSaveReference = canSaveVoiceReference(selectedRefFile)
  if(saveVoiceBtn){
    saveVoiceBtn.disabled = !(name && canSaveReference)
    saveVoiceBtn.title = ''
  }
  if(selectedRefFile && canSaveReference){
    setSaveVoiceInfo(SAVE_VOICE_FORMAT_HELP, false, 'format')
  }else if(saveVoiceInfo && saveVoiceInfo.dataset.reason === 'format'){
    setSaveVoiceInfo('')
  }
}

function setSaveVoiceInfo(msg, isError, reason=''){
  if(!saveVoiceInfo) return
  saveVoiceInfo.textContent = msg || ''
  saveVoiceInfo.style.color = isError ? '#ff9b9b' : ''
  if(reason) saveVoiceInfo.dataset.reason = reason
  else delete saveVoiceInfo.dataset.reason
}

function renderSavedVoices(){
  if(!savedVoicesList) return
  savedVoicesList.innerHTML = ''
  if(!Array.isArray(savedVoiceNames) || savedVoiceNames.length === 0){
    const empty = document.createElement('div'); empty.className = 'savedVoicesEmpty'; empty.textContent = 'Chưa có giọng đã lưu.'; savedVoicesList.appendChild(empty)
    return
  }
  savedVoiceNames.forEach(name=>{
    const item = document.createElement('div'); item.className = 'savedVoiceItem'
    const nameEl = document.createElement('span'); nameEl.className = 'svName'; nameEl.textContent = name
    const playBtn = document.createElement('button'); playBtn.type='button'; playBtn.className='secondary svPlay small'
    playBtn.textContent = '▶'; playBtn.setAttribute('aria-label', `Nghe thử giọng đã lưu ${name}`)
    playBtn.onclick = ()=> startVoicePreview(name, playBtn)
    const useBtn = document.createElement('button'); useBtn.type='button'; useBtn.className='secondary svUse'; useBtn.textContent='Dùng'; useBtn.setAttribute('aria-label', `Dùng giọng ${name}`)
    useBtn.addEventListener('click', ()=>{ selectValidVoice(name); setStatus(`Đã chọn giọng "${name}".`) })
    const delBtn = document.createElement('button'); delBtn.type='button'; delBtn.className='secondary'; delBtn.textContent='Xóa'; delBtn.setAttribute('aria-label', `Xóa giọng ${name}`)
    delBtn.addEventListener('click', async ()=>{
      if(!window.confirm(`Xóa giọng "${name}" khỏi máy này?`)) return
      try{
        const r = await fetch(API + '/api/voices/' + encodeURIComponent(name), { method: 'DELETE' })
        if(!r.ok){
          const err = await r.json().catch(()=>({}))
          setSaveVoiceInfo((err.detail) || 'Không thể xóa giọng.', true)
          return
        }
        loadHealthAndVoices()
        setStatus(`Đã xóa giọng "${name}".`)
      }catch(e){
        setSaveVoiceInfo('Không thể xóa giọng.', true)
      }
    })
    item.appendChild(nameEl); item.appendChild(playBtn); item.appendChild(useBtn); item.appendChild(delBtn)
    savedVoicesList.appendChild(item)
  })
}

// ── Phase 13: voice preview (ONE at a time; never touches history/textarea) ──
const previewCache = new Map() // key: `${voice}|${speed}` -> Blob (memory only)
let previewAudioEl = null
let previewAbort = null
let previewActiveBtn = null

function getPreviewAudioEl(){
  if(!previewAudioEl){
    previewAudioEl = new Audio()
    previewAudioEl.setAttribute('aria-hidden', 'true')
    previewAudioEl.addEventListener('ended', ()=> resetPreviewButtons())
    previewAudioEl.addEventListener('error', (e)=>{ console.error('Preview audio error:', e); resetPreviewButtons() })
  }
  return previewAudioEl
}

function stopVoicePreviewPlayback(){
  try{ getPreviewAudioEl().pause() }catch(e){ /* ignore */ }
}

function resetPreviewButtons(){
  document.querySelectorAll('.vplPlay, .svPlay').forEach(b=>{
    b.disabled = false
    if(b.textContent !== '▶') b.textContent = '▶'
    b.removeAttribute('aria-busy')
  })
  previewActiveBtn = null
}

function markPreviewButton(btn){
  resetPreviewButtons()
  previewActiveBtn = btn
  if(btn){ btn.disabled = true; btn.textContent = '⏳'; btn.setAttribute('aria-busy', 'true') }
}

async function startVoicePreview(voiceName, btn){
  if(!voiceName) return
  const key = `${voiceName}|1.0`

  // Same voice currently playing → toggle stop.
  if(previewActiveBtn === btn && previewAudioEl && !previewAudioEl.paused){
    stopVoicePreviewPlayback()
    resetPreviewButtons()
    setStatus('Đã dừng nghe thử.')
    return
  }

  // ONE preview at a time: abort the previous fetch and stop its playback.
  if(previewAbort){ try{ previewAbort.abort() }catch(e){ /* ignore */ } previewAbort = null }
  stopVoicePreviewPlayback()

  const controller = new AbortController()
  previewAbort = controller
  markPreviewButton(btn)
  setStatus(`Đang tạo preview cho giọng "${voiceName}"...`)

  try{
    let blob = previewCache.get(key)
    if(!blob){
      const res = await fetch(API + '/api/tts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ text: VOICE_PREVIEW_TEXT, voice: voiceName, speed: 1.0 }),
        signal: controller.signal,
      })
      if(!res.ok) throw { kind: 'http', status: res.status }
      blob = await res.blob()
      if(!isExpectedAudioResponse(res, blob)) throw { kind: 'invalid-audio' }
      previewCache.set(key, blob)
    }
    if(controller.signal.aborted) return

    stopVoicePreviewPlayback()
    const el = getPreviewAudioEl()
    const url = URL.createObjectURL(blob)
    el.src = url
    setStatus(`Đang phát preview: ${voiceName}`)
    await el.play()
    setTimeout(()=>{ if(el.currentSrc === url || el.src === url) URL.revokeObjectURL(url) }, 120000)
    // Playback started: keep this button as a stop toggle, re-enable the rest.
    if(btn){ btn.disabled = false; btn.textContent = '■' }
    else resetPreviewButtons()
  }catch(err){
    if(err && err.name === 'AbortError') return // superseded by a newer preview
    console.error('Preview failed:', err)
    setStatus('Không thể tạo preview.', true)
    resetPreviewButtons()
  }finally{
    if(previewAbort === controller) previewAbort = null
  }
}

function renderVoicePreviewList(presets, saved){
  if(!voicePreviewList) return
  voicePreviewList.innerHTML = ''
  const addRow = (name)=>{
    const row = document.createElement('div'); row.className = 'vplRow'
    const playBtn = document.createElement('button'); playBtn.type = 'button'; playBtn.className = 'vplPlay secondary small'
    playBtn.textContent = '▶'; playBtn.setAttribute('aria-label', `Nghe thử giọng ${name}`)
    playBtn.onclick = ()=> startVoicePreview(name, playBtn)

    const nameBtn = document.createElement('button'); nameBtn.type = 'button'; nameBtn.className = 'vplName'
    nameBtn.textContent = name
    nameBtn.title = `Chọn giọng ${name}`
    nameBtn.setAttribute('aria-label', `Chọn giọng ${name}`)
    if(voiceSelect.value === name) nameBtn.classList.add('vplSelected')
    nameBtn.onclick = ()=>{
      selectValidVoice(name)
      voicePreviewList.querySelectorAll('.vplName').forEach(n=> n.classList.remove('vplSelected'))
      nameBtn.classList.add('vplSelected')
      setStatus(`Đã chọn giọng "${name}".`)
    }

    row.appendChild(playBtn); row.appendChild(nameBtn)
    voicePreviewList.appendChild(row)
  }
  const addGroup = (label, items)=>{
    if(!items || !items.length) return
    const h = document.createElement('div'); h.className = 'vplGroup muted small'; h.textContent = label
    voicePreviewList.appendChild(h)
    items.forEach(v => addRow(typeof v === 'string' ? v : v.id))
  }
  addGroup('Giọng mặc định', presets)
  addGroup('Giọng đã lưu', saved)
}

if(saveVoiceNameInput) saveVoiceNameInput.addEventListener('input', updateSaveVoiceState)
if(saveVoiceBtn){
  saveVoiceBtn.addEventListener('click', async ()=>{
    const name = (saveVoiceNameInput ? saveVoiceNameInput.value : '').trim()
    if(!selectedRefFile){ setSaveVoiceInfo('Chọn tệp WAV, MP3 hoặc M4A tham chiếu trước khi lưu.', true); return }
    if(!canSaveVoiceReference(selectedRefFile)){ setSaveVoiceInfo('Định dạng tham chiếu không được hỗ trợ.', true); return }
    if(!name){ setSaveVoiceInfo('Nhập tên giọng trước khi lưu.', true); return }
    setSaveVoiceInfo('Đang lưu giọng...')
    const form = new FormData()
    form.append('name', name)
    form.append('ref_audio', selectedRefFile, selectedRefFile.name)
    try{
      const r = await fetch(API + '/api/voices/save', { method: 'POST', body: form })
      const body = await r.json().catch(()=>({}))
      if(!r.ok){
        setSaveVoiceInfo((body.detail) || 'Không thể lưu giọng.', true)
        return
      }
      setSaveVoiceInfo('')
      if(saveVoiceNameInput) saveVoiceNameInput.value = ''
      updateSaveVoiceState()
      await loadHealthAndVoices(name)
      setStatus(`Đã lưu giọng "${name}". Bạn có thể chọn ở mục giọng.`)
    }catch(e){
      setSaveVoiceInfo('Không thể lưu giọng.', true)
    }
  })
}

async function hasWavSignature(blob){
  const header = new Uint8Array(await blob.slice(0, 12).arrayBuffer())
  const expected = [82, 73, 70, 70, null, null, null, null, 87, 65, 86, 69] // RIFF....WAVE
  return header.length === 12 && expected.every((value, index)=> value === null || header[index] === value)
}

function waitForAudioDecode(blob, signal){
  return new Promise((resolve, reject)=>{
    const probe = document.createElement('audio')
    const probeUrl = URL.createObjectURL(blob)
    let settled = false
    let timeoutId = null

    const cleanup = ()=>{
      if(timeoutId !== null) clearTimeout(timeoutId)
      signal.removeEventListener('abort', onAbort)
      probe.removeEventListener('loadedmetadata', onLoadedMetadata)
      probe.removeEventListener('error', onError)
      probe.pause()
      probe.removeAttribute('src')
      probe.load()
      probe.remove()
      URL.revokeObjectURL(probeUrl)
    }
    const finish = (callback, value)=>{
      if(settled) return
      settled = true
      cleanup()
      callback(value)
    }
    const onLoadedMetadata = ()=> finish(resolve)
    const onError = ()=> finish(reject, {kind:'invalid-audio'})
    const onAbort = ()=> finish(reject, new DOMException('Aborted', 'AbortError'))

    if(signal.aborted){ onAbort(); return }
    probe.preload = 'auto'
    probe.addEventListener('loadedmetadata', onLoadedMetadata, {once:true})
    probe.addEventListener('error', onError, {once:true})
    signal.addEventListener('abort', onAbort, {once:true})
    timeoutId = setTimeout(()=> finish(reject, {kind:'invalid-audio'}), AUDIO_DECODE_TIMEOUT_MS)
    probe.hidden = true
    document.body.appendChild(probe)
    probe.src = probeUrl
    probe.load()
  })
}

async function replaceActiveAudio(blob, request){
  const previousBlobUrl = currentBlobUrl
  const previousBlob = currentBlob
  const previousSource = audioEl.src
  const nextBlobUrl = URL.createObjectURL(blob)

  audioEl.src = nextBlobUrl
  try{
    await audioEl.play()
    if(!isActiveRequest(request)) throw new DOMException('Superseded', 'AbortError')

    currentBlob = blob
    currentBlobUrl = nextBlobUrl
    // The player has accepted the new source, so the prior active result is no longer used.
    if(previousBlobUrl) URL.revokeObjectURL(previousBlobUrl)
    return true
  }catch(error){
    // A newer request may have committed while this request was awaiting play().
    // Only restore the prior result if this request still owns the player source.
    if(audioEl.src === nextBlobUrl){
      audioEl.pause()
      if(previousSource){
        audioEl.src = previousSource
        audioEl.load()
      }else{
        audioEl.removeAttribute('src')
        audioEl.load()
      }
      currentBlob = previousBlob
      currentBlobUrl = previousBlobUrl
    }
    URL.revokeObjectURL(nextBlobUrl)
    if(!isActiveRequest(request)) return false
    throw {kind:'playback-failed', cause:error}
  }
}

function enableDownload(blob){
  downloadBtn.disabled = false
  downloadBtn.onclick = ()=>{
    const ts = new Date().toISOString().replace(/[:.]/g,'-')
    const name = `tts-${ts}.wav`
    const a = document.createElement('a')
    const url = URL.createObjectURL(blob)
    a.href = url
    a.download = name
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(()=>URL.revokeObjectURL(url), 2000)
  }
}

// ── Phase 13: IndexedDB helpers for persisted history audio ─────────────────
function idbOpen(){
  return new Promise((resolve, reject)=>{
    if(!('indexedDB' in window)){
      const error = recordStorageError(new Error('IndexedDB unavailable'))
      reject(error)
      return
    }
    let settled = false
    const fail = error=>{
      recordStorageError(error)
      if(settled) return
      settled = true
      reject(error)
    }
    const req = indexedDB.open(IDB_NAME, IDB_VERSION)
    req.onupgradeneeded = event=>{
      const db = req.result
      console.info('[AIVoice storage] upgrading', {oldVersion:event.oldVersion, newVersion:event.newVersion})
      if(!db.objectStoreNames.contains(IDB_STORE)) db.createObjectStore(IDB_STORE)
      if(!db.objectStoreNames.contains(IDB_VOICE_LAB_STORE)) db.createObjectStore(IDB_VOICE_LAB_STORE)
    }
    req.onsuccess = ()=>{
      const db = req.result
      db.onversionchange = ()=> db.close()
      if(settled){ db.close(); return }
      settled = true
      resolve(db)
    }
    req.onblocked = ()=>{
      const error = new Error('Hãy đóng các tab AIVoice cũ rồi tải lại trang.')
      error.name = 'BlockedError'
      console.warn('[AIVoice storage] upgrade blocked; close other AIVoice tabs for this origin')
      fail(error)
    }
    req.onerror = ()=>{
      console.error('[AIVoice storage] open failed', req.error)
      fail(req.error || new Error('IndexedDB open failed'))
    }
  })
}

function idbRun(mode, fn, storeName=IDB_STORE){
  return idbOpen().then(db => new Promise((resolve, reject)=>{
    try{
      const tx = db.transaction(storeName, mode)
      const store = tx.objectStore(storeName)
      const request = fn(store)
      if(request && typeof request === 'object' && 'onerror' in request){
        request.onerror = ()=> console.error('[AIVoice storage] request failed', {storeName, mode, error:request.error})
      }
      tx.oncomplete = ()=>{
        const value = request && 'result' in request ? request.result : undefined
        db.close()
        resolve(value)
      }
      tx.onerror = ()=>{
        const error = recordStorageError(tx.error || new Error('IndexedDB transaction failed'))
        db.close()
        console.error('[AIVoice storage] transaction failed', {storeName, mode, error})
        reject(error)
      }
      tx.onabort = ()=>{
        const error = recordStorageError(tx.error || new Error('IndexedDB transaction aborted'))
        db.close()
        console.error('[AIVoice storage] transaction aborted', {storeName, mode, error})
        reject(error)
      }
    }catch(e){
      recordStorageError(e)
      db.close()
      console.error('[AIVoice storage] transaction start failed', {storeName, mode, error:e})
      reject(e)
    }
  }))
}

function idbPutAudio(id, blob){ return idbRun('readwrite', store => store.put(blob, id)) }
function idbGetAudio(id){ return idbRun('readonly', store => store.get(id)) }
function idbDeleteAudio(id){ return idbRun('readwrite', store => store.delete(id)) }
function idbPutVoiceLabAudio(id, blob){ return idbRun('readwrite', store => store.put(blob, id), IDB_VOICE_LAB_STORE) }
function idbGetVoiceLabAudio(id){ return idbRun('readonly', store => store.get(id), IDB_VOICE_LAB_STORE) }
function idbDeleteVoiceLabAudio(id){ return idbRun('readwrite', store => store.delete(id), IDB_VOICE_LAB_STORE) }
function idbCount(storeName){ return idbRun('readonly', store => store.count(), storeName) }

async function aivoiceStorageDiagnostics(){
  const base = {
    frontendBuild:AIVOICE_FRONTEND_BUILD,
    origin:window.location.origin,
    historyMetadataCount:loadHistory().length,
  }
  try{
    const db = await idbOpen()
    const schema = {version:db.version, stores:Array.from(db.objectStoreNames)}
    db.close()
    return {
      ...base,
      ...schema,
      historyAudioCount:schema.stores.includes(IDB_STORE) ? await idbCount(IDB_STORE) : null,
      voiceLabAudioCount:schema.stores.includes(IDB_VOICE_LAB_STORE) ? await idbCount(IDB_VOICE_LAB_STORE) : null,
      lastStorageError,
    }
  }catch(error){
    recordStorageError(error)
    return {...base, version:null, stores:[], historyAudioCount:null, voiceLabAudioCount:null, lastStorageError}
  }
}
window.aivoiceStorageDiagnostics = aivoiceStorageDiagnostics

async function idbClearAllAudio(){
  // Best-effort: remove every stored history blob (used by "clear all").
  try{
    await idbRun('readwrite', store => store.clear())
  }catch(e){ console.error('Failed to clear audio store:', e) }
}


// History metadata persists in localStorage. Audio blobs persist in IndexedDB,
// linked by item.id; hasAudio marks entries that should have playable audio.
function normalizeHistoryItem(item){
  if(!item || typeof item.text !== 'string' || !item.text.trim() || item.text.length > HISTORY_TEXT_MAX_LENGTH) return null
  const speed = Number(item.speed)
  if(!Number.isFinite(speed) || speed < 0.5 || speed > 2.0) return null
  const createdAt = Number(item.createdAt ?? item.ts)
  return {
    id: typeof item.id === 'string' && item.id ? item.id : null,
    text: item.text,
    voice: typeof item.voice === 'string' && item.voice ? item.voice : 'default',
    speed,
    createdAt: Number.isFinite(createdAt) ? createdAt : Date.now(),
    hasAudio: Boolean(item.hasAudio),
  }
}

function saveHistory(hist){
  const normalized = (Array.isArray(hist) ? hist : [])
    .map(normalizeHistoryItem)
    .filter(Boolean)
    .slice(-HISTORY_MAX_ITEMS)
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(normalized))
  return normalized
}

function loadHistory(){
  const raw = localStorage.getItem(HISTORY_STORAGE_KEY)
  if(!raw) return []
  try{
    const parsed = JSON.parse(raw)
    if(!Array.isArray(parsed)) return []
    const normalized = parsed.map(normalizeHistoryItem).filter(Boolean).slice(-HISTORY_MAX_ITEMS)
    // This migrates legacy entries and removes their stale blobUrl field on first load.
    if(JSON.stringify(parsed) !== JSON.stringify(normalized)) localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(normalized))
    return normalized
  }catch(e){ return [] }
}

// ── Phase 13: audio-backed history entries ───────────────────────────────────
function makeHistoryId(){
  return 'h_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
}

async function addHistoryEntryWithAudio(text, voice, speed, blob){
  const id = makeHistoryId()
  const entry = { id, text, voice, speed, createdAt: Date.now(), hasAudio: false }
  let stored = false
  try{
    if(!(blob instanceof Blob) || blob.size <= 44) throw new Error('Generated audio Blob is invalid')
    console.info('[AIVoice history] storing audio', {id, size:blob.size, type:blob.type || 'unknown'})
    await idbPutAudio(id, blob)
    const verified = await idbGetAudio(id)
    if(!(verified instanceof Blob) || verified.size !== blob.size) throw new Error('IndexedDB post-save verification failed')
    stored = true
    entry.hasAudio = true
    console.info('[AIVoice history] audio stored', {id, size:verified.size})
  }catch(e){
    // Storage failure must never break the main TTS flow: keep metadata only.
    recordStorageError(e)
    console.error('Failed to persist history audio:', e)
    entry.hasAudio = false
  }
  try{
    const hist = loadHistory()
    hist.push(entry)
    saveHistory(hist)
    renderHistory()
  }catch(error){
    recordStorageError(error)
    console.error('[AIVoice history] metadata save failed', error)
    return false
  }
  if(stored){
    try{ await pruneHistoryAudio() }
    catch(error){ recordStorageError(error); console.error('[AIVoice history] cleanup failed', error) }
  }
  return stored
}

// Keep all metadata (up to 20) but only the newest audio blobs. This preserves
// legacy/replay context and never leaves a stale hasAudio=true flag behind.
async function pruneHistoryAudio(){
  const hist = loadHistory()
  const withAudioIdxs = []
  hist.forEach((it, i)=>{ if(it.hasAudio && it.id) withAudioIdxs.push(i) })
  if(withAudioIdxs.length <= HISTORY_AUDIO_MAX) return
  const toRemove = withAudioIdxs.slice(0, withAudioIdxs.length - HISTORY_AUDIO_MAX)
  for(const i of toRemove){
    const item = hist[i]
    try{ if(item.id) await idbDeleteAudio(item.id) }catch(e){ console.error('Failed to delete old audio blob:', e) }
    item.hasAudio = false
  }
  saveHistory(hist)
}

function sanitizeVoiceForFilename(voice){
  const ascii = String(voice || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/gi, 'd')
  const cleaned = ascii.replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 24)
  return cleaned || 'voice'
}

function formatTimestampForFilename(ms){
  const d = new Date(ms)
  const p = (x)=> String(x).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}_${p(d.getHours())}-${p(d.getMinutes())}-${p(d.getSeconds())}`
}

async function downloadHistoryItem(item){
  if(!item.hasAudio || !item.id){
    setStatus('Mục này không còn tệp âm thanh khả dụng.', true)
    return
  }
  let blob = null
  try{ blob = await idbGetAudio(item.id) }catch(e){ console.error(e) }
  if(!blob || !(blob instanceof Blob) || blob.size < 44){
    markHistoryAudioUnavailable(item.id)
    setStatus('Tệp âm thanh đã được dọn dẹp; mục lịch sử vẫn giữ nội dung.', true)
    return
  }
  const name = `aivoice_${sanitizeVoiceForFilename(item.voice)}_${formatTimestampForFilename(item.createdAt)}.wav`
  const url = URL.createObjectURL(blob)
  try{
    const a = document.createElement('a')
    a.href = url
    a.download = name
    document.body.appendChild(a)
    a.click()
    a.remove()
  }finally{
    setTimeout(()=> URL.revokeObjectURL(url), 5000)
  }
}

async function playHistoryItem(item){
  if(!item.hasAudio || !item.id){
    setStatus('Mục này không còn tệp âm thanh khả dụng.', true)
    return
  }
  let blob = null
  try{ blob = await idbGetAudio(item.id) }catch(e){ console.error(e) }
  if(!blob || !(blob instanceof Blob) || blob.size < 44){
    markHistoryAudioUnavailable(item.id)
    setStatus('Tệp âm thanh đã được dọn dẹp; mục lịch sử vẫn giữ nội dung.', true)
    return
  }
  stopVoicePreviewPlayback()
  if(historyPlaybackUrl) URL.revokeObjectURL(historyPlaybackUrl)
  const url = URL.createObjectURL(blob)
  historyPlaybackUrl = url
  audioEl.src = url
  audioEl.load()
  audioEl.play().then(()=>{
    setTimeout(()=>{
      if(historyPlaybackUrl === url){ URL.revokeObjectURL(url); historyPlaybackUrl = null }
    }, 60000)
  }).catch((e)=>{
    console.error('History playback failed:', e)
    URL.revokeObjectURL(url)
    if(historyPlaybackUrl === url) historyPlaybackUrl = null
    setStatus('Không thể phát tệp âm thanh này.', true)
  })
}

function markHistoryAudioUnavailable(id){
  if(!id) return
  const hist = loadHistory()
  let changed = false
  hist.forEach(item=>{ if(item.id === id && item.hasAudio){ item.hasAudio = false; changed = true } })
  if(changed){ saveHistory(hist); renderHistory() }
}

function regenerateFromHistory(item){
  textArea.value = item.text
  textArea.dispatchEvent(new Event('input'))
  const voice = selectValidVoice(item.voice)
  speedInput.value = String(item.speed)
  speedInput.dispatchEvent(new Event('input'))
  synthesize(item.text, voice, item.speed)
}

function maybeUpdateHistoryControls(){
  const hist = loadHistory()
  clearHistoryBtn.disabled = hist.length === 0
  clearHistoryBtn.setAttribute('aria-disabled', String(hist.length === 0))
}

function clearHistory(){
  const hist = loadHistory()
  if(hist.length === 0){
    setStatus('Chưa có mục lịch sử nào để xóa.', true)
    return
  }
  const confirmed = window.confirm('Bạn có chắc muốn xóa toàn bộ lịch sử nghe thử (kèm tệp âm thanh đã lưu)?')
  if(!confirmed) return
  localStorage.removeItem(HISTORY_STORAGE_KEY)
  idbClearAllAudio()
  renderHistory()
  setStatus('Đã xóa toàn bộ lịch sử nghe thử.')
}

function renderHistory(){
  const hist = loadHistory()
  historyList.innerHTML = ''
  if(hist.length === 0){
    const empty = document.createElement('div'); empty.className = 'historyEmpty'; empty.textContent = 'Chưa có lịch sử nghe thử.'; historyList.appendChild(empty)
    maybeUpdateHistoryControls()
    return
  }
  hist.slice().reverse().forEach((item, idx)=>{
    const div = document.createElement('div'); div.className = 'historyItem'
    const txt = document.createElement('div'); txt.textContent = item.text.length>120? item.text.slice(0,120)+'…' : item.text
    const meta = document.createElement('div'); meta.className = 'historyMeta'; meta.textContent = `Giọng đọc: ${item.voice} • Tốc độ: ${item.speed}x • ${new Date(item.createdAt).toLocaleString()}`
    const actions = document.createElement('div'); actions.className = 'historyActions'

    if(item.hasAudio && item.id){
      const play = document.createElement('button')
      play.className = 'secondary small'
      play.textContent = '▶ Nghe'; play.setAttribute('aria-label', `Nghe lại mục lịch sử ${hist.length - idx}`)
      play.onclick = ()=>{ play.disabled = true; playHistoryItem(item).finally(()=>{ play.disabled = false }) }
      const dl = document.createElement('button')
      dl.className = 'secondary small'
      dl.textContent = '⬇ Tải'; dl.setAttribute('aria-label', `Tải tệp âm thanh mục lịch sử ${hist.length - idx}`)
      dl.onclick = ()=>{ dl.disabled = true; downloadHistoryItem(item).finally(()=>{ dl.disabled = false }) }
      actions.appendChild(play); actions.appendChild(dl)
    }else{
      const play = document.createElement('button'); play.className = 'secondary small'; play.textContent = '▶ Nghe lại'; play.disabled = true
      play.title = 'Bản cũ chỉ lưu nội dung'; actions.appendChild(play)
      const unavail = document.createElement('div'); unavail.className = 'historyUnavailable muted small'
      unavail.textContent = 'Chỉ lưu nội dung'
      actions.appendChild(unavail)
    }

    const regenerate = document.createElement('button'); regenerate.className = 'secondary small'; regenerate.textContent = 'Tạo lại'; regenerate.setAttribute('aria-label', `Tạo lại mục lịch sử ${hist.length - idx}`); regenerate.onclick = ()=>{ regenerateFromHistory(item) }
    const del = document.createElement('button'); del.className = 'secondary small historyDelete'; del.textContent = 'Xóa'; del.setAttribute('aria-label', `Xóa mục lịch sử ${hist.length - idx}`)
    del.onclick = ()=>{
      const h = loadHistory()
      const removed = h.splice(h.length-1-idx,1)[0]
      if(removed && removed.hasAudio && removed.id){
        idbDeleteAudio(removed.id).catch(e=> console.error('Failed to delete audio blob:', e))
      }
      saveHistory(h); renderHistory()
    }
    actions.appendChild(regenerate); actions.appendChild(del)
    div.appendChild(txt); div.appendChild(meta); div.appendChild(actions); historyList.appendChild(div)
  })
  maybeUpdateHistoryControls()
}

async function synthesize(text, voice, speed){
  // This also protects against a programmatic second invocation while a request is active.
  abortActiveRequest('cancelled', false)

  if(!text.trim()){
    setStatus('Văn bản không được để trống.', true)
    return
  }
  if(text.length > maxTextLength){
    setStatus(`Văn bản vượt quá giới hạn ${formatCharacterCount(maxTextLength)} ký tự.`, true)
    return
  }
  if(speed < 0.5 || speed > 2.0){
    setStatus('Tốc độ không hợp lệ. Hãy chọn tốc độ từ 0,5x đến 2,0x.', true)
    return
  }
  voice = resolveValidVoice(voice)
  if(!voice){
    setStatus('Chưa có giọng đọc hợp lệ. Hãy tải lại danh sách giọng.', true)
    return
  }

  const controller = new AbortController()
  const request = {
    id: ++nextTtsRequestId,
    controller,
    timeoutId: null,
    abortReason: null,
  }
  activeTtsRequest = request
  setGeneratingState(true)
  setStatus(selectedRefFile
    ? 'Đang chuyển đổi tham chiếu (nếu cần) & tạo giọng nói... Bạn có thể hủy.'
    : 'Đang tạo giọng nói... Bạn có thể hủy nếu không muốn chờ tiếp.')
  request.timeoutId = setTimeout(()=>{
    if(isActiveRequest(request)) abortActiveRequest('timeout')
  }, TTS_REQUEST_TIMEOUT_MS)

  try{
    const t0 = performance.now()
    let res
    if(selectedRefFile){
      // clone path: multipart form
      const form = new FormData()
      form.append('text', text)
      if(voice) form.append('voice', voice)
      form.append('speed', String(speed))
      const emotionVal = (emotionSelect && emotionSelect.value) ? emotionSelect.value : ''
      if(emotionVal) form.append('emotion', emotionVal)
      form.append('ref_audio', selectedRefFile, selectedRefFile.name)
        // include sampling params only when advanced panel is open
        if(advancedOpen){
          if(temperatureInput) form.append('temperature', String(temperatureInput.value))
          if(topKInput) form.append('top_k', String(topKInput.value))
          if(topPInput) form.append('top_p', String(topPInput.value))
          if(repetitionPenaltyInput) form.append('repetition_penalty', String(repetitionPenaltyInput.value))
        }
        res = await fetch(API + '/api/tts/clone', {method:'POST', body: form, signal: controller.signal})
    }else{
      const payload = {text, voice, speed}
        const preferred = !advancedOpen ? preferredSamplingForVoice(voice) : null
        if(advancedOpen){
          if(temperatureInput) payload.temperature = parseFloat(temperatureInput.value)
          if(topKInput) payload.top_k = parseInt(topKInput.value)
          if(topPInput) payload.top_p = parseFloat(topPInput.value)
          if(repetitionPenaltyInput) payload.repetition_penalty = parseFloat(repetitionPenaltyInput.value)
        }else if(preferred){
          payload.temperature = preferred.temperature
          payload.top_k = preferred.top_k
          payload.top_p = preferred.top_p
          payload.repetition_penalty = preferred.repetition_penalty
        }
      res = await fetch(API + '/api/tts', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload),
        signal: controller.signal,
      })
    }
    const t1 = performance.now()

    // An aborted or superseded request must never replace a newer audio result.
    if(!isActiveRequest(request)) return
    if(!res.ok) throw {kind:'http', status:res.status, detail:await readApiErrorDetail(res)}

    const blob = await res.blob()
    if(!isActiveRequest(request)) return
    if(!isExpectedAudioResponse(res, blob)) throw {kind:'invalid-audio'}
    if(!(await hasWavSignature(blob))) throw {kind:'invalid-audio'}
    await waitForAudioDecode(blob, controller.signal)
    if(!isActiveRequest(request)) return

    // Keep the current result until the candidate WAV is decodable and the player accepts it.
    const replaced = await replaceActiveAudio(blob, request)
    if(!replaced || !isActiveRequest(request)) return
    enableDownload(blob)
    setStatus(`Hoàn thành (${Math.round(t1-t0)} ms)`)

    // Result card: success state + regenerate.
    if(resultPlaceholder) resultPlaceholder.hidden = true
    if(resultSuccess) resultSuccess.hidden = false
    if(regenerateBtn) regenerateBtn.disabled = false

    // Persist this generated audio into history (IndexedDB blob + metadata).
    const historyAudioSaved = await addHistoryEntryWithAudio(text, voice, speed, blob)
    if(!historyAudioSaved) setStatus(storageFailureUserMessage('Đã tạo audio nhưng chưa lưu được vào lịch sử.'), false)
  }catch(err){
    // Cancellation and timeout announce their own terminal state immediately.
    if(!isActiveRequest(request)) return

    if(err && err.kind === 'http'){
      setStatus(userMessageForHttpStatus(err.status, err.detail), true)
    }else if(err && err.kind === 'invalid-audio'){
      setStatus('Máy chủ trả về dữ liệu âm thanh không hợp lệ. Hãy thử lại.', true)
    }else if(err && err.kind === 'playback-failed'){
      setStatus('Không thể phát tệp âm thanh này. Hãy thử tạo lại.', true)
    }else if(request.abortReason === 'timeout'){
      setStatus('Chuyển đổi mất quá nhiều thời gian. Hãy thử lại với đoạn văn ngắn hơn.', true)
    }else if(request.abortReason === 'cancelled' || (err && err.name === 'AbortError')){
      setStatus('Đã hủy chuyển đổi. Bạn có thể thử lại.')
    }else{
      console.error(err)
      setStatus('Không thể kết nối tới máy chủ TTS cục bộ. Hãy kiểm tra backend đang chạy rồi thử lại.', true)
    }
  }finally{
    finishRequest(request)
  }
}

function isSupportedTextFile(file){ return Boolean(file && file.name && file.name.toLowerCase().endsWith('.txt')) }

async function importTextFile(file){
  if(!file){
    setStatus('Không tìm thấy tệp văn bản.', true)
    return false
  }
  if(!isSupportedTextFile(file)){
    setStatus('Chỉ hỗ trợ tệp văn bản TXT.', true)
    return false
  }
  if(file.size === 0){
    setStatus('Tệp văn bản đang trống.', true)
    return false
  }
  if(file.size > TXT_FILE_MAX_BYTES){
    setStatus('Tệp quá lớn. Hãy chọn tệp văn bản nhỏ hơn.', true)
    return false
  }

  try{
    const text = await file.text()
    if(text.length > maxTextLength){
      setStatus(`Văn bản vượt quá giới hạn ${formatCharacterCount(maxTextLength)} ký tự.`, true)
      return false
    }
    textArea.value = text
    textArea.dispatchEvent(new Event('input'))
    setStatus('Đã nạp tệp văn bản.')
    return true
  }catch(e){
    console.error(e)
    setStatus('Không thể đọc tệp văn bản.', true)
    return false
  }
}

const uploadLabel = document.querySelector('.uploadLabel')
if(uploadLabel){
  uploadLabel.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter' || e.key === ' '){
      e.preventDefault()
      uploadInput.click()
    }
  })
}

// File picker reset is deliberate: selecting the same TXT file must fire change again.
uploadInput.addEventListener('change', async (e)=>{
  const files = e.target.files
  try{
    if(files && files.length > 1){
      setStatus('Chỉ hỗ trợ một tệp TXT mỗi lần.', true)
    }else{
      await importTextFile(files && files[0])
    }
  }finally{
    uploadInput.value = ''
  }
})

// drag & drop
const editorWrap = document.getElementById('editorWrap')
const _dragEventsA = ['dragenter','dragover']
if(Array.isArray(_dragEventsA)) _dragEventsA.forEach(ev=> editorWrap.addEventListener(ev, (e)=>{ e.preventDefault(); editorWrap.classList.add('drag') }))
const _dragEventsB = ['dragleave','drop']
if(Array.isArray(_dragEventsB)) _dragEventsB.forEach(ev=> editorWrap.addEventListener(ev, (e)=>{ e.preventDefault(); editorWrap.classList.remove('drag') }))
editorWrap.addEventListener('drop', async (e)=>{
  const files = e.dataTransfer && e.dataTransfer.files
  if(!files || files.length === 0){
    setStatus('Không tìm thấy tệp văn bản.', true)
    return
  }
  if(files.length > 1){
    setStatus('Chỉ hỗ trợ một tệp TXT mỗi lần.', true)
    return
  }
  await importTextFile(files[0])
})

// audio events
audioEl.addEventListener('timeupdate', ()=>{
  const p = (audioEl.currentTime / (audioEl.duration || 1)) * 100
  const value = Number.isFinite(p) ? Math.min(100, Math.max(0, p)) : 0
  progressBar.style.width = value+'%'
  progressBar.setAttribute('aria-valuenow', String(Math.round(value)))
  progressBar.setAttribute('aria-valuetext', `${Math.round(value)} phần trăm`)
  curTime.textContent = formatTime(audioEl.currentTime)
  durTime.textContent = formatTime(audioEl.duration)
})
audioEl.addEventListener('loadedmetadata', ()=>{
  durTime.textContent = formatTime(audioEl.duration)
  progressBar.setAttribute('aria-valuemin', '0')
  progressBar.setAttribute('aria-valuemax', '100')
  progressBar.setAttribute('aria-valuenow', '0')
})

// speak button
speakBtn.addEventListener('click', ()=>{
  const text = textArea.value || ''
  const voice = voiceSelect.value || null
  const speed = parseFloat(speedInput.value)
  synthesize(text, voice, speed)
})

// Phase 14: result card — regenerate with the current text/voice/speed
if(regenerateBtn){
  regenerateBtn.addEventListener('click', ()=>{
    if(isGenerating) return
    if(!textArea.value.trim()){ setStatus('Chưa có văn bản để tạo lại.', true); return }
    synthesize(textArea.value, voiceSelect.value || null, parseFloat(speedInput.value))
  })
}

cancelBtn.addEventListener('click', ()=>{ abortActiveRequest('cancelled') })
clearTextBtn.addEventListener('click', ()=>{
  if(!textArea.value) return
  textArea.value = ''
  textArea.dispatchEvent(new Event('input'))
  setStatus(isGenerating ? 'Đã xóa văn bản. Quá trình tạo giọng nói vẫn đang chạy.' : 'Đã xóa văn bản.')
})
clearHistoryBtn.addEventListener('click', clearHistory)

// ── Phase 18: Voice Lab ─────────────────────────────────────────────────────
function setVoiceLabStatus(message, isError=false){
  voiceLabStatus.textContent = message
  voiceLabStatus.style.color = isError ? 'var(--danger)' : ''
  voiceLabStatus.setAttribute('role', isError ? 'alert' : 'status')
}

function selectedSavedVoiceId(){
  return savedVoiceNames.includes(voiceSelect.value) ? voiceSelect.value : null
}

function preferredSamplingForVoice(voiceId){
  const candidate = temperatureCandidates.get(voiceId)
  return candidate && candidate.speed === 1.0 && candidate.top_k === 25 && candidate.top_p === 0.95 && candidate.repetition_penalty === 1.2
    ? candidate : null
}

function renderTemperatureCandidateState(){
  const savedVoiceId = selectedSavedVoiceId()
  const candidate = preferredSamplingForVoice(savedVoiceId)
  if(voiceLabCandidateVoice) voiceLabCandidateVoice.textContent = savedVoiceId || 'Hãy chọn một giọng đã lưu ở phần Giọng đọc.'
  if(voiceLabCandidateStatus){
    voiceLabCandidateStatus.textContent = candidate
      ? `✓ Cấu hình Voice Lab: temperature ${candidate.temperature}; chỉ áp dụng khi không tự chỉnh Nâng cao.`
      : 'Chưa chọn temperature cho giọng ứng viên này.'
  }
  if(voiceLabSelectTemperature) voiceLabSelectTemperature.disabled = !savedVoiceId
  updateVoiceLabGenerateState()
}

async function loadTemperatureCandidates(){
  try{
    const response = await fetch(API + '/api/voice-lab/temperature-candidates')
    if(!response.ok) throw new Error('temperature candidates unavailable')
    const data = await response.json()
    temperatureCandidates = new Map(Object.entries(data.candidates || {}))
  }catch(error){
    console.warn('Voice Lab temperature candidates unavailable:', error)
    temperatureCandidates = new Map()
  }
  renderTemperatureCandidateState()
}

function activeVoiceLabReference(){
  const selected = document.querySelector('input[name="voiceLabReference"]:checked')
  return selected ? voiceLabReferences.get(selected.value) : null
}

function updateVoiceLabGenerateState(){
  const requiresSavedVoice = voiceLabRound.value === 'temperature'
  voiceLabGenerate.disabled = voiceLabGenerating || !voiceLabCorpus || (requiresSavedVoice ? !selectedSavedVoiceId() : !activeVoiceLabReference())
}

function updateVoiceLabSaveState(){
  const current = voiceLabCurrentSampleState
  const name = (voiceLabSaveVoiceName?.value || '').trim()
  const saveableReference = current && current.reference && current.reference.file && canSaveVoiceReference(current.reference.file)
  if(voiceLabSaveVoiceBtn) voiceLabSaveVoiceBtn.disabled = !(name && saveableReference)
  if(!voiceLabSaveVoiceHelp) return
  if(!current) voiceLabSaveVoiceHelp.textContent = 'Tạo sample từ một mẫu tham chiếu trước khi lưu giọng.'
  else if(!saveableReference) voiceLabSaveVoiceHelp.textContent = 'Định dạng reference hiện tại không được hỗ trợ để lưu giọng.'
  else voiceLabSaveVoiceHelp.textContent = `Sẽ lưu identity từ ${current.reference.metadata.filename}. ${SAVE_VOICE_FORMAT_HELP}`
}

function setVoiceLabCurrentSample(state){
  voiceLabCurrentSampleState = state
  if(!voiceLabCurrentSample) return
  if(!state){
    voiceLabCurrentSample.textContent = 'Chưa có mẫu hiện tại.'
  }else{
    voiceLabCurrentSample.textContent = `Mẫu hiện tại · ${state.reference.metadata.label} (${state.reference.metadata.filename}) · ${state.sentence.category || state.sentence.id} · Run ${state.runNumber}`
  }
  updateVoiceLabSaveState()
}

function nextVoiceLabRunNumber(referenceId, sentenceId, savedVoiceId=null){
  const runs = voiceLabExperiments
    .filter(item => item.reference?.id === referenceId && item.evaluation_text_id === sentenceId && item.round === voiceLabRound.value && (savedVoiceId === null || item.saved_voice_id === savedVoiceId))
    .map(item => Number(item.run_number) || 0)
  return Math.max(0, ...runs) + 1
}

async function syncVoiceLabAudioStatus(id, hasAudio){
  const response = await fetch(API + '/api/voice-lab/experiments/' + encodeURIComponent(id) + '/audio', {
    method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({has_audio:Boolean(hasAudio)}),
  })
  if(!response.ok) throw new Error('Không thể đồng bộ audio sample.')
  return response.json()
}

async function persistVoiceLabAudio(id, blob){
  if(!(blob instanceof Blob) || blob.size <= 44) throw new Error('Voice Lab audio Blob is invalid')
  console.info('[AIVoice Voice Lab] storing audio', {id, size:blob.size, type:blob.type || 'unknown'})
  await idbPutVoiceLabAudio(id, blob)
  const verified = await idbGetVoiceLabAudio(id)
  if(!(verified instanceof Blob) || verified.size !== blob.size){
    throw new Error('Voice Lab IndexedDB post-save verification failed')
  }
  console.info('[AIVoice Voice Lab] audio stored', {id, size:verified.size})
  return true
}

async function pruneVoiceLabAudio(){
  const withAudio = voiceLabExperiments.filter(item=> item.has_audio && item.id)
  const excess = withAudio.slice(0, Math.max(0, withAudio.length - VOICE_LAB_AUDIO_MAX))
  for(const item of excess){
    try{ await idbDeleteVoiceLabAudio(item.id); await syncVoiceLabAudioStatus(item.id, false) }
    catch(error){ console.error('Voice Lab audio cleanup failed:', error) }
  }
}

async function playVoiceLabExperiment(item, button){
  if(!item.has_audio){ setVoiceLabStatus('Sample cũ chỉ còn metadata; không cần tạo lại để xem điểm.', false); return }
  button.disabled = true
  try{
    const blob = await idbGetVoiceLabAudio(item.id)
    if(!(blob instanceof Blob) || blob.size < 44){
      await syncVoiceLabAudioStatus(item.id, false)
      setVoiceLabStatus('Audio sample đã được dọn dẹp; metadata vẫn được giữ.', false)
      await loadVoiceLabExperiments()
      return
    }
    if(voiceLabCurrentAudioUrl) URL.revokeObjectURL(voiceLabCurrentAudioUrl)
    voiceLabCurrentAudioUrl = URL.createObjectURL(blob)
    voiceLabAudio.src = voiceLabCurrentAudioUrl
    voiceLabAudio.load()
    await voiceLabAudio.play()
  }catch(error){
    console.error('Voice Lab replay failed:', error)
    setVoiceLabStatus('Không thể phát audio sample đã lưu.', true)
  }finally{ button.disabled = false }
}

function probeVoiceLabDuration(file){
  return new Promise((resolve, reject)=>{
    const audio = document.createElement('audio')
    const url = URL.createObjectURL(file)
    let timer = null
    const cleanup = ()=>{
      if(timer) clearTimeout(timer)
      audio.removeAttribute('src')
      audio.load()
      URL.revokeObjectURL(url)
    }
    audio.addEventListener('loadedmetadata', ()=>{
      const duration = audio.duration
      cleanup()
      Number.isFinite(duration) && duration > 0 ? resolve(duration) : reject(new Error('duration unavailable'))
    }, {once:true})
    audio.addEventListener('error', ()=>{ cleanup(); reject(new Error('audio metadata failed')) }, {once:true})
    timer = setTimeout(()=>{ cleanup(); reject(new Error('audio metadata timeout')) }, 8000)
    audio.preload = 'metadata'
    audio.src = url
    audio.load()
  })
}

async function setVoiceLabReference(slot, file){
  const input = voiceLabReferenceInputs[slot]
  const metaEl = voiceLabReferenceMetaEls[slot]
  const card = document.querySelector(`[data-reference-slot="${slot}"]`)
  const radio = card.querySelector('input[type="radio"]')
  if(!file){ return }
  const ext = extensionOf(file.name)
  if(!CLONE_ACCEPTED_EXTENSIONS.includes(ext)){
    setVoiceLabStatus('Voice Lab chỉ nhận WAV, MP3 hoặc M4A.', true)
    return
  }
  if(file.size <= 0 || file.size > REF_MAX_BYTES){
    setVoiceLabStatus('Reference phải có dữ liệu và không vượt quá 5 MB.', true)
    return
  }

  metaEl.textContent = 'Đang đọc metadata...'
  let duration = null
  try{ duration = await probeVoiceLabDuration(file) }catch(e){ console.warn('Voice Lab duration unavailable:', e) }
  if(duration !== null && duration > REF_MAX_SECONDS){
    setVoiceLabStatus(`Reference ${slot.slice(-1).toUpperCase()} dài ${duration.toFixed(1)} giây; giới hạn hiện tại là ${REF_MAX_SECONDS} giây.`, true)
    metaEl.textContent = 'File bị từ chối vì quá dài.'
    return
  }

  const label = `Reference ${slot.slice(-1).toUpperCase()}`
  const metadata = {
    id: slot,
    label,
    filename: file.name,
    format: ext.slice(1),
    size_bytes: file.size,
    duration_seconds: duration === null ? null : Number(duration.toFixed(2)),
  }
  voiceLabReferences.set(slot, {file, metadata})
  radio.disabled = false
  if(!activeVoiceLabReference()) radio.checked = true
  card.classList.add('labReady')
  const durationText = duration === null ? 'duration chưa đọc được' : `${duration.toFixed(1)} giây`
  const preference = ext === '.wav' ? 'ưu tiên cho identity' : 'hỗ trợ clone, nhưng nên dùng WAV khi có thể'
  metaEl.textContent = `${file.name} · ${ext.slice(1).toUpperCase()} · ${formatFileSize(file.size)} · ${durationText} · ${preference}`
  setVoiceLabStatus(`${label} đã sẵn sàng. Chỉ generate một sample mỗi lần.`)
  updateVoiceLabGenerateState()
  if(radio.checked && voiceLabCorpus) voiceLabRun.value = String(nextVoiceLabRunNumber(metadata.id, voiceLabSentence.value))
  input.value = ''
}

function renderVoiceLabCorpus(){
  voiceLabSentence.innerHTML = ''
  voiceLabCorpus.sentences.forEach(item=>{
    const option = document.createElement('option')
    option.value = item.id
    option.textContent = item.category.replaceAll('_', ' ')
    voiceLabSentence.appendChild(option)
  })
  renderVoiceLabSentence()

  voiceLabRubric.innerHTML = ''
  voiceLabCorpus.rubric.forEach(item=>{
    const row = document.createElement('div')
    row.className = 'labRubricItem'
    const label = document.createElement('label')
    label.htmlFor = `voiceLabScore_${item.id}`
    label.textContent = item.label
    const question = document.createElement('span')
    question.textContent = item.question
    label.appendChild(question)
    const select = document.createElement('select')
    select.id = `voiceLabScore_${item.id}`
    select.dataset.scoreId = item.id
    select.innerHTML = '<option value="">—</option>'
    for(let score=1; score<=5; score++){
      const option = document.createElement('option')
      option.value = String(score)
      option.textContent = String(score)
      select.appendChild(option)
    }
    row.appendChild(label)
    row.appendChild(select)
    voiceLabRubric.appendChild(row)
  })
}

function renderVoiceLabSentence(){
  if(!voiceLabCorpus) return
  const sentence = voiceLabCorpus.sentences.find(item => item.id === voiceLabSentence.value)
  voiceLabSentenceText.textContent = sentence ? sentence.text : ''
}

function voiceLabParameters(){
  const round = voiceLabRound.value
  const parameters = {
    speed: 1.0,
    temperature: Number(voiceLabTemperature.value),
    top_k: 25,
    top_p: Number(voiceLabTopP.value),
    repetition_penalty: Number(voiceLabRepetition.value),
  }
  if(!Number.isFinite(parameters.temperature) || !Number.isFinite(parameters.top_p) || !Number.isFinite(parameters.repetition_penalty)) throw new Error('Thông số Round 2 không hợp lệ.')
  if(round === 'reference_selection') return {speed:1.0, temperature:0.8, top_k:25, top_p:0.95, repetition_penalty:1.2}
  if(round === 'temperature'){
    if(![0.7, 0.8, 0.9].includes(parameters.temperature)) throw new Error('Temperature Round 2 chỉ dùng 0.7, 0.8 hoặc 0.9.')
    return {speed:1.0, temperature:parameters.temperature, top_k:25, top_p:0.95, repetition_penalty:1.2}
  }
  return parameters
}

function setVoiceLabGenerating(generating){
  voiceLabGenerating = generating
  voiceLabGenerate.textContent = generating ? 'Đang tạo một sample...' : 'Tạo một sample'
  voiceLabGenerate.setAttribute('aria-busy', String(generating))
  updateVoiceLabGenerateState()
}

function resetVoiceLabEvaluation(){
  voiceLabRubric.querySelectorAll('[data-score-id]').forEach(select=>{ select.value = '' })
  voiceLabNotes.value = ''
  if(voiceLabMissingWords) voiceLabMissingWords.checked = false
  if(voiceLabMissingWordNote) voiceLabMissingWordNote.value = ''
  voiceLabSaveEvaluation.disabled = !voiceLabCurrentExperimentId
}

async function generateVoiceLabSample(){
  if(voiceLabGenerating) return
  const temperatureRound = voiceLabRound.value === 'temperature'
  const savedVoiceId = temperatureRound ? selectedSavedVoiceId() : null
  const selectedReference = activeVoiceLabReference()
  if(temperatureRound && !savedVoiceId){ setVoiceLabStatus('Round Temperature chỉ dùng giọng đã lưu đang được chọn ở phần Giọng đọc.', true); return }
  if(!temperatureRound && !selectedReference){ setVoiceLabStatus('Hãy chọn Reference A, B hoặc C.', true); return }
  const reference = temperatureRound
    ? {metadata:{id:'saved_voice', label:'Giọng ứng viên', filename:savedVoiceId, format:'wav', size_bytes:1, duration_seconds:null}, file:null}
    : selectedReference
  let parameters
  try{ parameters = voiceLabParameters() }catch(error){ setVoiceLabStatus(error.message, true); return }
  const sentence = voiceLabCorpus.sentences.find(item => item.id === voiceLabSentence.value)
  if(!sentence){ setVoiceLabStatus('Không tìm thấy câu đánh giá cố định.', true); return }

  setVoiceLabGenerating(true)
  voiceLabCurrentExperimentId = null
  setVoiceLabCurrentSample(null)
  resetVoiceLabEvaluation()
  setVoiceLabStatus('Đang tạo đúng một sample qua inference queue hiện tại...')
  try{
    let response
    if(temperatureRound){
      response = await fetch(API + '/api/tts', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text:sentence.text, voice:savedVoiceId, ...parameters})})
      if(!response.ok) throw new Error(`TTS API trả HTTP ${response.status}.`)
    }else{
      const form = new FormData()
      form.append('text', sentence.text)
      form.append('speed', '1.0')
      form.append('temperature', String(parameters.temperature))
      form.append('top_k', String(parameters.top_k))
      form.append('top_p', String(parameters.top_p))
      form.append('repetition_penalty', String(parameters.repetition_penalty))
      form.append('ref_audio', reference.file, reference.file.name)
      response = await fetch(API + '/api/tts/clone', {method:'POST', body:form})
      if(!response.ok) throw new Error(`Clone API trả HTTP ${response.status}.`)
    }
    const blob = await response.blob()
    if(!isExpectedAudioResponse(response, blob) || !(await hasWavSignature(blob))) throw new Error('Backend không trả WAV hợp lệ.')

    if(voiceLabCurrentAudioUrl) URL.revokeObjectURL(voiceLabCurrentAudioUrl)
    voiceLabCurrentAudioUrl = URL.createObjectURL(blob)
    voiceLabAudio.src = voiceLabCurrentAudioUrl
    voiceLabAudio.load()

    // Generation has succeeded at this point. From here on, metadata/IndexedDB
    // failures must not discard the in-memory player or current reference.
    const runNumber = nextVoiceLabRunNumber(reference.metadata.id, sentence.id, savedVoiceId)
    voiceLabRun.value = String(runNumber + 1)
    setVoiceLabCurrentSample({experimentId:null, reference, sentence, runNumber})
    resetVoiceLabEvaluation()

    let record
    try{
      const experimentResponse = await fetch(API + '/api/voice-lab/experiments', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          reference:reference.metadata,
          saved_voice_id:savedVoiceId,
          evaluation_text_id:sentence.id,
          parameters,
          round:voiceLabRound.value,
          run_number:runNumber,
          has_audio:false,
        }),
      })
      if(!experimentResponse.ok) throw new Error(`Không thể lưu pending experiment (HTTP ${experimentResponse.status}).`)
      record = await experimentResponse.json()
      voiceLabCurrentExperimentId = record.id
      setVoiceLabCurrentSample({experimentId:record.id, reference, sentence, runNumber:Number(record.run_number)})
      resetVoiceLabEvaluation()
    }catch(error){
      console.error('[AIVoice Voice Lab] experiment metadata save failed', error)
      setVoiceLabStatus('Đã tạo sample nhưng chưa lưu được experiment. Audio hiện tại vẫn nghe được.', false)
      return
    }

    let audioStored = false
    try{
      await persistVoiceLabAudio(record.id, blob)
      await syncVoiceLabAudioStatus(record.id, true)
      audioStored = true
    }catch(error){
      recordStorageError(error)
      console.error('[AIVoice Voice Lab] audio persistence failed', error)
    }
    await loadVoiceLabExperiments()
    if(audioStored){
      await pruneVoiceLabAudio()
      setVoiceLabStatus('Sample đã sẵn sàng và đã lưu audio. Hãy nghe, chấm đủ 6 tiêu chí rồi lưu.')
    }else{
      setVoiceLabStatus(storageFailureUserMessage('Đã tạo audio nhưng chưa lưu được vào lịch sử thử nghiệm. Mẫu hiện tại vẫn nghe được.'), false)
    }
  }catch(error){
    console.error('Voice Lab generation failed:', error)
    setVoiceLabStatus(error.message || 'Không thể tạo Voice Lab sample.', true)
  }finally{
    setVoiceLabGenerating(false)
  }
}

function collectVoiceLabScores(){
  const scores = {}
  for(const select of voiceLabRubric.querySelectorAll('[data-score-id]')){
    if(!select.value) throw new Error('Hãy chấm đủ cả 6 tiêu chí trước khi lưu.')
    scores[select.dataset.scoreId] = Number(select.value)
  }
  return scores
}

async function saveVoiceLabEvaluation(){
  if(!voiceLabCurrentExperimentId){ setVoiceLabStatus('Chưa có sample đang chờ đánh giá.', true); return }
  let scores
  try{ scores = collectVoiceLabScores() }catch(error){ setVoiceLabStatus(error.message, true); return }
  voiceLabSaveEvaluation.disabled = true
  try{
    const response = await fetch(API + '/api/voice-lab/experiments/' + encodeURIComponent(voiceLabCurrentExperimentId), {
      method:'PATCH',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        scores,
        notes:voiceLabNotes.value.trim(),
        missing_words:Boolean(voiceLabMissingWords?.checked),
        missing_word_note:voiceLabMissingWordNote?.value.trim() || '',
      }),
    })
    if(!response.ok) throw new Error(`Không thể lưu đánh giá (HTTP ${response.status}).`)
    voiceLabCurrentExperimentId = null
    setVoiceLabStatus('Đã lưu đánh giá. Không có winner nào được tự động chọn.')
    await loadVoiceLabExperiments()
  }catch(error){
    console.error('Voice Lab evaluation save failed:', error)
    setVoiceLabStatus(error.message, true)
    voiceLabSaveEvaluation.disabled = false
  }
}

async function selectTemperatureCandidate(){
  const savedVoiceId = selectedSavedVoiceId()
  const temperature = Number(voiceLabCandidateTemperature?.value)
  if(!savedVoiceId || ![0.7, 0.8, 0.9].includes(temperature)){
    setVoiceLabStatus('Hãy chọn một giọng đã lưu và temperature 0.7, 0.8 hoặc 0.9.', true)
    return
  }
  if(!window.confirm(`Dùng temperature ${temperature} làm cấu hình ứng viên cho “${savedVoiceId}”? Bạn vẫn có thể thay đổi sau.`)) return
  voiceLabSelectTemperature.disabled = true
  try{
    const response = await fetch(API + '/api/voice-lab/temperature-candidates', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        payload:{
          saved_voice_id:savedVoiceId,
          temperature,
          top_k:25,
          top_p:0.95,
          repetition_penalty:1.2,
          speed:1.0,
        },
        user_confirmed:true,
      }),
    })
    const candidate = await response.json().catch(()=>null)
    if(!response.ok) throw new Error(candidate?.detail || 'Không thể lưu cấu hình ứng viên.')
    temperatureCandidates.set(savedVoiceId, candidate)
    renderTemperatureCandidateState()
    setVoiceLabStatus(`Đã chọn temperature ${temperature} cho giọng ứng viên. Không có “winner” tự động.`)
  }catch(error){
    setVoiceLabStatus(error.message || 'Không thể lưu cấu hình ứng viên.', true)
  }finally{ renderTemperatureCandidateState() }
}

async function saveVoiceLabVoice(){
  const current = voiceLabCurrentSampleState
  const name = (voiceLabSaveVoiceName?.value || '').trim()
  if(!current){ updateVoiceLabSaveState(); return }
  if(!canSaveVoiceReference(current.reference.file)){ updateVoiceLabSaveState(); return }
  if(!name){ updateVoiceLabSaveState(); return }
  voiceLabSaveVoiceBtn.disabled = true
  voiceLabSaveVoiceHelp.textContent = 'Đang lưu identity từ reference gốc...'
  try{
    const form = new FormData()
    form.append('name', name)
    form.append('description', (voiceLabSaveVoiceDescription?.value || '').trim())
    form.append('ref_audio', current.reference.file, current.reference.file.name)
    const response = await fetch(API + '/api/voices/save', {method:'POST', body:form})
    const body = await response.json().catch(()=>({}))
    if(!response.ok) throw new Error(body.detail || 'Không thể lưu giọng.')
    voiceLabSaveVoiceName.value = ''
    voiceLabSaveVoiceDescription.value = ''
    await loadHealthAndVoices(body.voice?.id || name)
    voiceLabSaveVoiceHelp.textContent = `Đã lưu “${name}”; giọng này đã có trong Giọng đọc và danh sách nghe thử.`
    setStatus(`Đã lưu giọng "${name}" từ ${current.reference.metadata.label}.`)
  }catch(error){
    voiceLabSaveVoiceHelp.textContent = error.message || 'Không thể lưu giọng.'
  }finally{ updateVoiceLabSaveState() }
}

function renderVoiceLabExperiments(){
  voiceLabExperimentList.innerHTML = ''
  if(!voiceLabExperiments.length){
    const empty = document.createElement('div')
    empty.className = 'labEmpty'
    empty.textContent = 'Chưa có experiment. Hệ thống đang READY FOR REFERENCES.'
    voiceLabExperimentList.appendChild(empty)
    return
  }
  voiceLabExperiments.slice().reverse().forEach(item=>{
    const row = document.createElement('div')
    row.className = 'labExperimentItem'
    const top = document.createElement('div')
    top.className = 'labExperimentTop'
    const title = document.createElement('span')
    title.textContent = `${item.reference.label} · ${item.evaluation_text_id} · run ${item.run_number}`
    const score = document.createElement('span')
    score.className = item.status === 'evaluated' ? 'labExperimentScore' : 'labExperimentScore labPending'
    score.textContent = item.status === 'evaluated' ? `TB ${Number(item.average_score).toFixed(2)} / 5` : 'Chờ chấm'
    top.appendChild(title)
    top.appendChild(score)
    const meta = document.createElement('div')
    meta.className = 'labExperimentMeta'
    const p = item.parameters
    meta.textContent = `${item.round} · T ${p.temperature} · K ${p.top_k} · P ${p.top_p} · Rep ${p.repetition_penalty} · Speed ${p.speed} · ${new Date(item.created_at).toLocaleString('vi-VN')}`
    row.appendChild(top)
    row.appendChild(meta)
    const actions = document.createElement('div')
    actions.className = 'labExperimentActions'
    const play = document.createElement('button')
    play.type = 'button'; play.className = 'secondary small'; play.textContent = '▶ Nghe lại'
    play.disabled = !item.has_audio
    if(!item.has_audio) play.title = 'Sample này chỉ còn metadata'
    play.onclick = ()=> playVoiceLabExperiment(item, play)
    actions.appendChild(play)
    if(!item.has_audio){
      const legacy = document.createElement('span'); legacy.className = 'muted small'; legacy.textContent = 'Chỉ lưu metadata'
      actions.appendChild(legacy)
    }
    row.appendChild(actions)
    if(item.notes){
      const notes = document.createElement('div')
      notes.className = 'labExperimentMeta'
      notes.textContent = `Ghi chú: ${item.notes}`
      row.appendChild(notes)
    }
    if(item.missing_words){
      const missing = document.createElement('div')
      missing.className = 'labExperimentMeta labMissingWarning'
      missing.textContent = `⚠ Có mất/nuốt chữ${item.missing_word_note ? `: ${item.missing_word_note}` : ''}`
      row.appendChild(missing)
    }
    voiceLabExperimentList.appendChild(row)
  })
}

async function loadVoiceLabExperiments(){
  try{
    const response = await fetch(API + '/api/voice-lab/experiments')
    if(!response.ok) throw new Error('experiments unavailable')
    const data = await response.json()
    voiceLabExperiments = Array.isArray(data.experiments) ? data.experiments : []
    renderVoiceLabExperiments()
  }catch(error){
    console.error(error)
    voiceLabExperimentList.innerHTML = '<div class="labEmpty">Không thể tải experiment history.</div>'
  }
}

async function loadVoiceLab(){
  try{
    const [identityResponse, qualityResponse] = await Promise.all([
      fetch(API + '/api/voice-lab/corpus'),
      fetch(API + '/api/voice-lab/quality-corpus'),
    ])
    if(!identityResponse.ok || !qualityResponse.ok) throw new Error('quality corpus unavailable')
    const identityCorpus = await identityResponse.json()
    const qualityCorpus = await qualityResponse.json()
    voiceLabCorpus = {...qualityCorpus, rubric:identityCorpus.rubric, score_scale:identityCorpus.score_scale}
    renderVoiceLabCorpus()
    updateVoiceLabGenerateState()
    const reference = activeVoiceLabReference()
    if(reference) voiceLabRun.value = String(nextVoiceLabRunNumber(reference.metadata.id, voiceLabSentence.value))
  }catch(error){
    console.error(error)
    setVoiceLabStatus('Không thể tải evaluation corpus.', true)
  }
  await loadVoiceLabExperiments()
  await loadTemperatureCandidates()
}

Object.entries(voiceLabReferenceInputs).forEach(([slot, input])=>{
  input.addEventListener('change', async event=>{
    const file = event.target.files && event.target.files[0]
    try{ await setVoiceLabReference(slot, file) }
    finally{ input.value = '' }
  })
})
document.querySelectorAll('input[name="voiceLabReference"]').forEach(radio=> radio.addEventListener('change', ()=>{
  updateVoiceLabGenerateState()
  const reference = activeVoiceLabReference()
  if(reference && voiceLabCorpus) voiceLabRun.value = String(nextVoiceLabRunNumber(reference.metadata.id, voiceLabSentence.value))
}))
voiceLabSentence.addEventListener('change', renderVoiceLabSentence)
voiceLabRound.addEventListener('change', ()=>{
  if(voiceLabRound.value === 'reference_selection'){
    voiceLabTemperature.value = '0.8'
    voiceLabTopP.value = '0.95'
    voiceLabRepetition.value = '1.2'
  }
  if(voiceLabRound.value === 'temperature'){
    voiceLabTopP.value = '0.95'
    voiceLabRepetition.value = '1.2'
    if(!['0.7', '0.8', '0.9'].includes(voiceLabTemperature.value)) voiceLabTemperature.value = '0.8'
  }
  const reference = activeVoiceLabReference()
  if(reference && voiceLabCorpus) voiceLabRun.value = String(nextVoiceLabRunNumber(reference.metadata.id, voiceLabSentence.value))
})
voiceLabGenerate.addEventListener('click', generateVoiceLabSample)
voiceLabSaveEvaluation.addEventListener('click', saveVoiceLabEvaluation)
voiceLabSelectTemperature.addEventListener('click', selectTemperatureCandidate)
voiceLabSaveVoiceName.addEventListener('input', updateVoiceLabSaveState)
voiceLabSaveVoiceBtn.addEventListener('click', saveVoiceLabVoice)
voiceLabRefresh.addEventListener('click', loadVoiceLabExperiments)
window.addEventListener('beforeunload', ()=>{ if(voiceLabCurrentAudioUrl) URL.revokeObjectURL(voiceLabCurrentAudioUrl) })

// init
updateTextValidation()
loadHealthAndVoices().then(()=>{ renderHistory() })
loadVoiceLab()
updateVoiceLabSaveState()
