// ---------- storage ----------
const STORE = {
  farms: 'agrios_farms',
  observations: 'agrios_observations',
  traps: 'agrios_traps',
  riskContext: 'agrios_risk_context',
  followUps: 'agrios_follow_ups',
};
const LOCAL_MODEL_URL = './models/mobile1_efficientnetb0.onnx';
const LOCAL_LABELS = [
  'cotton__alternaria_leaf_spot', 'cotton__bacterial_blight', 'cotton__bollworm',
  'cotton__healthy', 'grape__bacterial_leaf_spot', 'grape__downy_mildew',
  'grape__healthy', 'grape__powdery_mildew', 'onion__healthy',
  'onion__purple_blotch', 'onion__stemphylium_leaf_blight', 'tomato__early_blight',
  'tomato__healthy', 'tomato__late_blight', 'tomato__leaf_mold',
];
let localModelSession;

function loadAll(key){
  try { return JSON.parse(localStorage.getItem(key)) || []; }
  catch { return []; }
}
function saveAll(key, arr){ localStorage.setItem(key, JSON.stringify(arr)); }
function uid(){ return Date.now().toString(36) + Math.random().toString(36).slice(2,7); }

let farms = loadAll(STORE.farms);
let observations = loadAll(STORE.observations);
let traps = loadAll(STORE.traps);
let riskContext = loadAll(STORE.riskContext)[0] || { weather:'humid', stage:'Vegetative', variety:'', soil:'balanced', treatment:'' };
let followUps = loadAll(STORE.followUps);
let currentDiagnosis = null;
let reviewStatus = 'Awaiting expert validation';

let map, layerGroup;
let activeQuickFilter = 'all';

// ---------- helpers ----------
function $(id){ return document.getElementById(id); }
function fmtDate(iso){
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { day:'2-digit', month:'short', year:'numeric' });
}
function farmById(id){ return farms.find(f => f.id === id); }
function severityRank(s){ return { Mild:1, Moderate:2, Severe:3 }[s] || 0; }

function useLocation(latId, lngId){
  if (!navigator.geolocation){
    alert('Geolocation is not available on this device.');
    return;
  }
  navigator.geolocation.getCurrentPosition(
    pos => {
      $(latId).value = pos.coords.latitude.toFixed(6);
      $(lngId).value = pos.coords.longitude.toFixed(6);
    },
    () => alert('Could not read your location. Enter coordinates manually.')
  );
}

function readImage(input){
  return new Promise(resolve => {
    const file = input.files && input.files[0];
    if (!file) return resolve(null);
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => resolve(null);
    reader.readAsDataURL(file);
  });
}

function note(id, msg, isError){
  const el = $(id);
  el.textContent = msg;
  el.classList.toggle('error', !!isError);
  el.classList.remove('pulse');
  void el.offsetWidth; // restart animation
  el.classList.add('pulse');
  if (!isError) setTimeout(() => { if (el.textContent === msg) el.textContent = ''; }, 3500);
}

function updateSyncLabel(){
  const el = $('lastSyncLabel');
  if (!el) return;
  const timestamp = new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(new Date());
  el.textContent = `${timestamp} IST`;
}

// ---------- animated counters ----------
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function animateCount(el, target){
  const from = parseInt(el.dataset.value || '0', 10);
  el.dataset.value = target;
  if (prefersReducedMotion || from === target){ el.textContent = target; return; }
  const duration = 500;
  const start = performance.now();
  function tick(now){
    const p = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(from + (target - from) * eased);
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ---------- farm dropdowns ----------
function refreshFarmSelects(){
  const selects = [$('obsFarm'), $('trapFarm')];
  selects.forEach(sel => {
    const current = sel.value;
    sel.innerHTML = '<option value="">Select a registered farm</option>' +
      farms.map(f => `<option value="${f.id}">${escapeHtml(f.name)} — ${escapeHtml(f.taluk)}</option>`).join('');
    if (farms.some(f => f.id === current)) sel.value = current;
  });
}

function escapeHtml(str){
  return String(str ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

async function runLocalPrediction(file){
  if (!window.ort) throw new Error('Local model runtime is unavailable');
  if (!localModelSession) localModelSession = await ort.InferenceSession.create(LOCAL_MODEL_URL, { executionProviders: ['wasm'] });
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement('canvas');
  canvas.width = 224;
  canvas.height = 224;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(bitmap, 0, 0, 224, 224);
  bitmap.close();
  const pixels = context.getImageData(0, 0, 224, 224).data;
  const mean = [0.485, 0.456, 0.406];
  const std = [0.229, 0.224, 0.225];
  const input = new Float32Array(3 * 224 * 224);
  for (let index = 0; index < 224 * 224; index += 1){
    for (let channel = 0; channel < 3; channel += 1){
      const value = pixels[index * 4 + channel] / 255;
      input[channel * 224 * 224 + index] = (value - mean[channel]) / std[channel];
    }
  }
  const tensor = new ort.Tensor('float32', input, [1, 3, 224, 224]);
  const output = await localModelSession.run({ input: tensor });
  const logits = output.logits.data;
  const maxLogit = Math.max(...logits);
  const exponentials = Array.from(logits, value => Math.exp(value - maxLogit));
  const total = exponentials.reduce((sum, value) => sum + value, 0);
  return {
    best_label: LOCAL_LABELS[exponentials.indexOf(Math.max(...exponentials))] || 'unknown',
    confidence: Math.max(...exponentials) / total,
    top_predictions: exponentials.map((value, index) => ({ label: LOCAL_LABELS[index], confidence: value / total }))
      .sort((a, b) => b.confidence - a.confidence).slice(0, 3),
  };
}

// ---------- forms ----------
$('farmForm').addEventListener('submit', e => {
  e.preventDefault();
  const farm = {
    id: uid(),
    name: $('farmName').value.trim(),
    farmerName: $('farmerName').value.trim(),
    taluk: $('taluk').value.trim(),
    district: $('district').value.trim(),
    crop: $('crop').value.trim(),
    lat: parseFloat($('farmLat').value),
    lng: parseFloat($('farmLng').value),
    createdAt: new Date().toISOString(),
  };
  if (Number.isNaN(farm.lat) || Number.isNaN(farm.lng)){
    note('farmNote', 'Latitude and longitude are required.', true);
    return;
  }
  farms.push(farm);
  saveAll(STORE.farms, farms);
  e.target.reset();
  note('farmNote', `Saved "${farm.name}".`);
  refreshFarmSelects();
  populateFilterOptions();
  renderEverything();
});

$('obsForm').addEventListener('submit', async e => {
  e.preventDefault();
  const farmId = $('obsFarm').value;
  const farm = farmById(farmId);
  if (!farm){ note('obsNote', 'Select the farm this observation belongs to.', true); return; }
  const lat = parseFloat($('obsLat').value), lng = parseFloat($('obsLng').value);
  if (Number.isNaN(lat) || Number.isNaN(lng)){ note('obsNote', 'Latitude and longitude are required.', true); return; }

  const imageFile = $('obsImage').files?.[0] || null;
  if (imageFile){
    const diagnosis = $('aiDiagnosisResult');
    diagnosis.classList.remove('hidden', 'error');
    diagnosis.textContent = 'Running local prediction...';
    try {
      const prediction = await runLocalPrediction(imageFile);
      const data = {
        disease_detected: prediction.best_label,
        predicted_label: prediction.best_label,
        confidence: prediction.confidence,
        top_predictions: prediction.top_predictions,
        forecast: { week_1: 'Local image prediction complete. Extension officer review is recommended.', follow_up_due_in_days: 7 },
        management: { immediate_actions: ['Review the image and confirm the diagnosis in the field.'] },
        case_status: 'local_prediction_ready',
      };

      renderAiDiagnosis(data);
      note('obsNote', 'Prediction ready.');
      return;
    } catch (err) {
      const diagnosis = $('aiDiagnosisResult');
      diagnosis.classList.remove('hidden');
      diagnosis.classList.add('error');
      diagnosis.textContent = 'Could not classify this image locally.';
      note('obsNote', 'Prediction unavailable.', true);
      return;
    }
  }

  const image = await readImage($('obsImage'));
  const obs = {
    id: uid(),
    farmId,
    crop: $('obsCrop').value.trim(),
    growthStage: $('growthStage').value.trim(),
    symptom: $('symptom').value.trim(),
    diseasePest: $('diseasePest').value.trim(),
    severity: $('severity').value,
    lat, lng, image,
    createdAt: new Date().toISOString(),
  };
  observations.push(obs);
  saveAll(STORE.observations, observations);
  e.target.reset();
  note('obsNote', 'Observation saved.');
  populateFilterOptions();
  renderEverything();
});

function renderAiDiagnosis(data){
  currentDiagnosis = data;
  const box = $('aiDiagnosisResult');
  const management = data.management || {};
  const actions = Object.values(management).flat().filter(Boolean).slice(0, 5);
  box.classList.remove('hidden', 'error');
  box.innerHTML = `
    <div class="ai-result-head"><div><small>AI field diagnosis</small><strong>${escapeHtml(data.disease_detected || data.predicted_label || 'Unrecognized pattern')}</strong></div><span>${Math.round((data.confidence || 0) * 100)}% confidence</span></div>
    <p>${escapeHtml(data.forecast?.week_1 || 'Officer review is required before treatment is finalized.')}</p>
    <div class="ai-result-grid"><div><small>7-day follow-up</small><b>${escapeHtml(data.forecast?.follow_up_due_in_days || 7)} days</b></div><div><small>Case state</small><b>Officer review</b></div><div><small>Top action</small><b>${escapeHtml(actions[0] || 'Request field verification')}</b></div></div>
    <details><summary>View treatment plan</summary><ul>${actions.map(action => `<li>${escapeHtml(action)}</li>`).join('') || '<li>Request a second image and field check.</li>'}</ul></details>`;
  renderAdvisory();
  renderReviewState();
}

const ADVISORY_TEXT = {
  en: {
    title: 'Integrated crop-health response',
    intro: 'Start with confirmation, sanitation, monitoring, and biological or cultural controls. Do not apply a chemical product from this screen without officer approval and current label verification.',
    confirm: 'Confirm: compare symptoms with a second image or field inspection before intervention.',
    monitor: 'Monitor: mark affected plants, inspect neighbouring plants, and repeat the check in 48–72 hours.',
    refer: 'Refer: use a field visit or laboratory sample when symptoms are atypical, spreading quickly, or the confidence is low.',
  },
  ta: {
    title: 'ஒருங்கிணைந்த பயிர் சுகாதார ஆலோசனை',
    intro: 'முதலில் அறிகுறியை உறுதி செய்து, சுத்தம், கண்காணிப்பு மற்றும் உயிரியல் அல்லது பண்பாட்டு முறைகளைப் பயன்படுத்தவும். அலுவலர் ஒப்புதல் மற்றும் தற்போதைய லேபிள் சரிபார்ப்பு இல்லாமல் இரசாயனத்தைப் பயன்படுத்த வேண்டாம்.',
    confirm: 'உறுதி: தலையீட்டிற்கு முன் இரண்டாவது படம் அல்லது வயல் ஆய்வுடன் அறிகுறிகளை ஒப்பிடவும்.',
    monitor: 'கண்காணிப்பு: பாதிக்கப்பட்ட செடிகளை குறியிட்டு, அருகிலுள்ள செடிகளை ஆய்வு செய்து 48–72 மணி நேரத்தில் மீண்டும் பார்க்கவும்.',
    refer: 'பரிந்துரை: அறிகுறிகள் வழக்கத்திற்கு மாறாகவோ வேகமாகப் பரவினாலோ அல்லது நம்பிக்கை குறைவாக இருந்தாலோ வயல் ஆய்வு அல்லது ஆய்வக மாதிரி கோரவும்.',
  },
};

function getRiskAlerts(){
  const alerts = [];
  const recentObs = observations.filter(item => Date.now() - new Date(item.createdAt).getTime() < 14 * 86400000);
  const severe = recentObs.filter(item => item.severity === 'Severe').length;
  const trapPressure = traps.reduce((sum, item) => sum + Number(item.pestCount || 0), 0);
  const weather = riskContext.weather;
  if (weather === 'rain' || weather === 'humid') alerts.push({ level:'High', title:'Fungal and bacterial spread window', text:'Humidity or rain can increase leaf infection and spread. Inspect lower leaf surfaces and improve canopy airflow.' });
  if (weather === 'heat' || riskContext.soil === 'dry') alerts.push({ level:'Moderate', title:'Heat and moisture stress', text:'Prioritise irrigation assessment, mulch or soil moisture conservation, and avoid treating stress symptoms as disease without confirmation.' });
  if (riskContext.soil === 'wet') alerts.push({ level:'High', title:'Root-zone stress', text:'Waterlogging increases root and wilt risk. Check drainage, root condition, and whether symptoms are uniform across the field.' });
  if (trapPressure >= 40) alerts.push({ level:'High', title:'Trap pressure is elevated', text:`${trapPressure} pest counts are recorded in the current device data. Increase scouting and inspect the next crop block.` });
  if (severe >= 2) alerts.push({ level:'Critical', title:'Multiple severe observations', text:`${severe} severe observations were recorded in the last 14 days. Prioritise officer review and consider a coordinated field visit.` });
  if (!alerts.length) alerts.push({ level:'Low', title:'Routine surveillance window', text:'No immediate high-risk combination is visible from the current local inputs. Continue weekly scouting and retain trap records.' });
  return alerts;
}

function renderRiskDashboard(){
  if (!$('riskSummary')) return;
  const alerts = getRiskAlerts();
  const highest = alerts.some(item => item.level === 'Critical') ? 'Critical' : alerts.some(item => item.level === 'High') ? 'High' : alerts.some(item => item.level === 'Moderate') ? 'Moderate' : 'Low';
  $('riskSummary').innerHTML = `<div class="risk-score ${highest.toLowerCase()}"><small>Local risk level</small><strong>${highest}</strong></div><div class="risk-facts"><span><b>${observations.length}</b> field observations</span><span><b>${traps.length}</b> trap records</span><span><b>${riskContext.stage}</b> crop stage</span><span><b>${riskContext.weather}</b> weather signal</span></div>`;
  $('riskAlerts').innerHTML = alerts.map(alert => `<article class="alert-card ${alert.level.toLowerCase()}"><div class="alert-level">${alert.level}</div><div><h3>${escapeHtml(alert.title)}</h3><p>${escapeHtml(alert.text)}</p></div></article>`).join('');
}

function renderAdvisory(){
  const box = $('advisoryContent');
  if (!box) return;
  const language = $('advisoryLanguage')?.value || 'en';
  const text = ADVISORY_TEXT[language];
  const diagnosis = currentDiagnosis?.disease_detected || currentDiagnosis?.predicted_label || 'No image diagnosis yet';
  const top = currentDiagnosis?.top_predictions?.slice(0, 3) || [];
  box.innerHTML = `<div class="advisory-hero"><div><small>Current working diagnosis</small><h3>${escapeHtml(diagnosis)}</h3></div><span>${currentDiagnosis ? `${Math.round(currentDiagnosis.confidence * 100)}% confidence` : 'Awaiting image'}</span></div><p class="advisory-intro">${text.intro}</p><div class="advisory-columns"><div><h3>Do now</h3><ul><li>${text.confirm}</li><li>${text.monitor}</li><li>${text.refer}</li></ul></div><div><h3>Model alternatives</h3>${top.length ? `<ol>${top.map(item => `<li>${escapeHtml(item.label)} <b>${Math.round(item.confidence * 100)}%</b></li>`).join('')}</ol>` : '<p class="empty-hint">Upload a crop image to see ranked alternatives.</p>'}</div></div>`;
}

function renderReviewState(){
  if (!$('reviewState')) return;
  const diagnosis = currentDiagnosis?.disease_detected || currentDiagnosis?.predicted_label || 'No diagnosis submitted';
  $('reviewState').innerHTML = `<span class="review-badge">${escapeHtml(reviewStatus)}</span><strong>${escapeHtml(diagnosis)}</strong><p>AI output supports triage; an extension officer validates diagnosis, treatment, field visit, or laboratory referral.</p>`;
}

function renderFollowUps(){
  if (!$('followUpTimeline')) return;
  $('followUpTimeline').innerHTML = followUps.length ? followUps.slice().reverse().map(item => `<div class="timeline-item"><span>${fmtDate(item.createdAt)}</span><strong>${escapeHtml(item.status)}</strong><p>${escapeHtml(item.action || 'No action recorded')} ${item.note ? `· ${escapeHtml(item.note)}` : ''}</p></div>`).join('') : '<p class="empty-hint">No follow-up checkpoints recorded yet.</p>';
}

function syncRiskFields(){
  if (!$('riskWeather')) return;
  $('riskWeather').value = riskContext.weather;
  $('riskStage').value = riskContext.stage;
  $('riskVariety').value = riskContext.variety || '';
  $('riskSoil').value = riskContext.soil;
  $('riskTreatment').value = riskContext.treatment || '';
}

$('riskContextForm')?.addEventListener('submit', event => {
  event.preventDefault();
  riskContext = { weather:$('riskWeather').value, stage:$('riskStage').value, variety:$('riskVariety').value.trim(), soil:$('riskSoil').value, treatment:$('riskTreatment').value.trim() };
  saveAll(STORE.riskContext, [riskContext]);
  note('riskContextNote', 'Local alerts refreshed.');
  renderRiskDashboard();
});

$('advisoryLanguage')?.addEventListener('change', renderAdvisory);
$('approveAdvisoryBtn')?.addEventListener('click', () => { reviewStatus = 'Advisory approved for monitored use'; renderReviewState(); });
$('visitReferralBtn')?.addEventListener('click', () => { reviewStatus = 'Field visit requested'; renderReviewState(); });
$('labReferralBtn')?.addEventListener('click', () => { reviewStatus = 'Laboratory referral requested'; renderReviewState(); });
$('followUpForm')?.addEventListener('submit', event => {
  event.preventDefault();
  followUps.push({ status:$('followUpStatus').value, action:$('followUpAction').value.trim(), note:$('followUpNote').value.trim(), createdAt:new Date().toISOString() });
  saveAll(STORE.followUps, followUps);
  event.target.reset();
  renderFollowUps();
});

$('trapForm').addEventListener('submit', async e => {
  e.preventDefault();
  const farmId = $('trapFarm').value;
  if (!farmId){ note('trapNote', 'Select the farm this trap belongs to.', true); return; }
  const lat = parseFloat($('trapLat').value), lng = parseFloat($('trapLng').value);
  if (Number.isNaN(lat) || Number.isNaN(lng)){ note('trapNote', 'Latitude and longitude are required.', true); return; }

  const image = await readImage($('trapImage'));
  const trap = {
    id: uid(),
    farmId,
    trapType: $('trapType').value,
    pestName: $('pestName').value.trim(),
    pestCount: parseInt($('pestCount').value, 10) || 0,
    lat, lng, image,
    createdAt: new Date().toISOString(),
  };
  traps.push(trap);
  saveAll(STORE.traps, traps);
  e.target.reset();
  $('pestCount').value = 0;
  note('trapNote', 'Trap input saved.');
  populateFilterOptions();
  renderEverything();
});

// ---------- filters ----------
function uniqueSorted(arr){ return [...new Set(arr.filter(Boolean))].sort((a,b) => a.localeCompare(b)); }

function populateFilterOptions(){
  fillSelect('filterDistrict', uniqueSorted(farms.map(f => f.district)), 'All districts');
  fillSelect('filterTaluk', uniqueSorted(farms.map(f => f.taluk)), 'All taluks');
  fillSelect('filterCrop', uniqueSorted([...farms.map(f => f.crop), ...observations.map(o => o.crop)]), 'All crops');
  fillSelect('filterDisease', uniqueSorted([...observations.map(o => o.diseasePest), ...traps.map(t => t.pestName)]), 'All diseases / pests');
}

function fillSelect(id, values, allLabel){
  const sel = $(id);
  const current = sel.value;
  sel.innerHTML = `<option value="">${allLabel}</option>` + values.map(v => `<option>${escapeHtml(v)}</option>`).join('');
  if (values.includes(current)) sel.value = current;
}

function getFilters(){
  return {
    district: $('filterDistrict').value,
    taluk: $('filterTaluk').value,
    crop: $('filterCrop').value,
    disease: $('filterDisease').value,
    severity: $('filterSeverity').value,
    date: $('filterDate').value,
    search: ($('filterSearch')?.value || '').trim().toLowerCase(),
    quick: activeQuickFilter,
  };
}

function farmMatchesLocationFilters(farm, f){
  if (!farm) return !f.district && !f.taluk;
  if (f.district && farm.district !== f.district) return false;
  if (f.taluk && farm.taluk !== f.taluk) return false;
  return true;
}

function getFilteredData(){
  const f = getFilters();
  const dateCutoff = f.date ? new Date(f.date) : null;
  const recentCutoff = f.quick === 'recent' ? new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) : null;
  const searchTerm = f.search;

  const appliesSearch = (value) => !searchTerm || String(value || '').toLowerCase().includes(searchTerm);

  const filteredFarms = farms.filter(farm => {
    if (!farmMatchesLocationFilters(farm, f)) return false;
    if (f.crop && farm.crop !== f.crop) return false;
    if (searchTerm && ![
      farm.name, farm.farmerName, farm.taluk, farm.district, farm.crop
    ].some(appliesSearch)) return false;
    return true;
  });

  const filteredObs = observations.filter(o => {
    const farm = farmById(o.farmId);
    if (!farmMatchesLocationFilters(farm, f)) return false;
    if (f.crop && o.crop !== f.crop && (!farm || farm.crop !== f.crop)) return false;
    if (f.disease && o.diseasePest !== f.disease) return false;
    if (f.severity && o.severity !== f.severity) return false;
    if (f.quick === 'severe' && o.severity !== 'Severe') return false;
    if (dateCutoff && new Date(o.createdAt) < dateCutoff) return false;
    if (recentCutoff && new Date(o.createdAt) < recentCutoff) return false;
    if (searchTerm && ![
      o.crop, o.growthStage, o.symptom, o.diseasePest, o.severity,
      farm?.name, farm?.district, farm?.taluk
    ].some(appliesSearch)) return false;
    return true;
  });

  const filteredTraps = traps.filter(t => {
    const farm = farmById(t.farmId);
    if (!farmMatchesLocationFilters(farm, f)) return false;
    if (f.crop && farm && farm.crop !== f.crop) return false;
    if (f.disease && t.pestName !== f.disease) return false;
    if (f.severity) return false; // traps have no severity of their own
    if (dateCutoff && new Date(t.createdAt) < dateCutoff) return false;
    if (recentCutoff && new Date(t.createdAt) < recentCutoff) return false;
    if (searchTerm && ![
      t.trapType, t.pestName, String(t.pestCount),
      farm?.name, farm?.district, farm?.taluk
    ].some(appliesSearch)) return false;
    return true;
  });

  return { filteredFarms, filteredObs, filteredTraps };
}

['filterDistrict','filterTaluk','filterCrop','filterDisease','filterSeverity','filterDate','filterSearch'].forEach(id => {
  const el = $(id);
  if (!el) return;
  el.addEventListener('change', renderEverything);
  if (el.matches('input[type="search"]')) {
    el.addEventListener('input', renderEverything);
  }
});
$('filterSearch')?.addEventListener('input', renderEverything);
$('clearFilters').addEventListener('click', () => {
  ['filterDistrict','filterTaluk','filterCrop','filterDisease','filterSeverity','filterDate','filterSearch'].forEach(id => {
    const el = $(id); if (el) el.value = '';
  });
  activeQuickFilter = 'all';
  document.querySelectorAll('.chip-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.quick === 'all'));
  renderEverything();
});

document.querySelectorAll('.chip-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    activeQuickFilter = btn.dataset.quick || 'all';
    document.querySelectorAll('.chip-btn').forEach(node => node.classList.toggle('active', node === btn));
    renderEverything();
  });
});

// ---------- stats ----------
const STAT_KEYS = [
  { key: 'farms', label: 'Farms in view' },
  { key: 'obs', label: 'Observations' },
  { key: 'traps', label: 'Trap readings' },
  { key: 'pests', label: 'Pests counted' },
  { key: 'severe', label: 'Severe cases' },
];
let statsGridBuilt = false;
updateSyncLabel();
setInterval(updateSyncLabel, 30000);

function ensureStatsGrid(){
  if (statsGridBuilt) return;
  $('statsGrid').innerHTML = STAT_KEYS.map(s =>
    `<div class="stat-tile"><b id="stat-${s.key}" data-value="0">0</b><span>${s.label}</span></div>`
  ).join('');
  statsGridBuilt = true;
}

function renderStats(data){
  ensureStatsGrid();
  const { filteredFarms, filteredObs, filteredTraps } = data;
  const pestTotal = filteredTraps.reduce((sum, t) => sum + (t.pestCount || 0), 0);
  const severe = filteredObs.filter(o => o.severity === 'Severe').length;

  animateCount($('stat-farms'), filteredFarms.length);
  animateCount($('stat-obs'), filteredObs.length);
  animateCount($('stat-traps'), filteredTraps.length);
  animateCount($('stat-pests'), pestTotal);
  animateCount($('stat-severe'), severe);

  const bySeverity = { Mild:0, Moderate:0, Severe:0 };
  filteredObs.forEach(o => { if (bySeverity[o.severity] !== undefined) bySeverity[o.severity]++; });
  const maxSeverity = Math.max(1, ...Object.values(bySeverity));
  $('severityBars').innerHTML = Object.entries(bySeverity).map(([label, count]) => `
    <div class="bar-row">
      <span>${label}</span>
      <div class="bar-track"><div class="bar-fill ${label.toLowerCase()}" style="width:${(count / maxSeverity) * 100}%"></div></div>
      <span class="count">${count}</span>
    </div>`).join('');

  const tally = {};
  filteredObs.forEach(o => { if (o.diseasePest) tally[o.diseasePest] = (tally[o.diseasePest]||0) + 1; });
  filteredTraps.forEach(t => { if (t.pestName) tally[t.pestName] = (tally[t.pestName]||0) + (t.pestCount || 1); });
  const ranked = Object.entries(tally).sort((a,b) => b[1]-a[1]).slice(0,6);
  $('topPests').innerHTML = ranked.length
    ? ranked.map(([name, count]) => `<li>${escapeHtml(name)} <b>· ${count}</b></li>`).join('')
    : '<li class="empty-hint">No pests or diseases logged yet.</li>';

  const districtRisk = {};
  filteredObs.forEach(o => {
    const farm = farmById(o.farmId);
    const key = farm ? farm.district : 'Unknown';
    if (!districtRisk[key]) districtRisk[key] = { total:0, severe:0 };
    districtRisk[key].total += 1;
    if (o.severity === 'Severe') districtRisk[key].severe += 1;
  });
  const districtSummary = Object.entries(districtRisk).sort((a,b) => b[1].severe - a[1].severe || b[1].total - a[1].total);
  const topDistrict = districtSummary[0] ? districtSummary[0][0] : 'No district data';
  const riskScore = Math.min(100, Math.round((severe / Math.max(1, filteredObs.length || 1)) * 100 + (filteredTraps.length ? 15 : 0)));

  $('dashboardInsights').innerHTML = `
    <div class="insight-card">
      <small>Risk score</small>
      <strong>${riskScore}%</strong>
      <span>${severe} severe observations in view</span>
    </div>
    <div class="insight-card">
      <small>Highest pressure</small>
      <strong>${escapeHtml(topDistrict)}</strong>
      <span>${districtSummary[0] ? `${districtSummary[0][1].severe} severe cases` : 'No severe cases recorded'}</span>
    </div>
    <div class="insight-card">
      <small>Detected pests</small>
      <strong>${Object.keys(tally).length || 0}</strong>
      <span>${ranked[0] ? `${escapeHtml(ranked[0][0])} is most active` : 'No active pest alerts'}</span>
    </div>
  `;
}

// ---------- map ----------
function initMap(){
  map = L.map('map').setView([11.0, 78.5], 7); // Tamil Nadu-centred default view
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map);
  layerGroup = L.layerGroup().addTo(map);
}

function severityColor(sev){
  return sev === 'Severe' ? '#A04A2C' : sev === 'Moderate' ? '#8C6A1F' : sev === 'Mild' ? '#B87F26' : '#57503f';
}

function circleMarker(lat, lng, color, radius){
  return L.circleMarker([lat, lng], { radius: radius || 7, color, fillColor: color, fillOpacity: 0.85, weight: 2 });
}

function loadMapData(){
  if (!map) initMap();
  layerGroup.clearLayers();
  const { filteredFarms, filteredObs, filteredTraps } = getFilteredData();
  const bounds = [];

  filteredFarms.forEach(f => {
    circleMarker(f.lat, f.lng, '#232017', 6)
      .bindPopup(`<b>${escapeHtml(f.name)}</b><br>${escapeHtml(f.farmerName)}<br>${escapeHtml(f.crop)} · ${escapeHtml(f.taluk)}, ${escapeHtml(f.district)}`)
      .addTo(layerGroup);
    bounds.push([f.lat, f.lng]);
  });

  filteredObs.forEach(o => {
    const farm = farmById(o.farmId);
    circleMarker(o.lat, o.lng, severityColor(o.severity), 8)
      .bindPopup(`<b>${escapeHtml(o.diseasePest || o.symptom || 'Observation')}</b><br>${escapeHtml(farm ? farm.name : '')}<br>Severity: ${o.severity || 'Not assessed'}`)
      .addTo(layerGroup);
    bounds.push([o.lat, o.lng]);
  });

  filteredTraps.forEach(t => {
    const farm = farmById(t.farmId);
    circleMarker(t.lat, t.lng, '#47643A', 7)
      .bindPopup(`<b>${escapeHtml(t.trapType)}</b><br>${escapeHtml(t.pestName || 'Unnamed pest')} · ${t.pestCount}<br>${escapeHtml(farm ? farm.name : '')}`)
      .addTo(layerGroup);
    bounds.push([t.lat, t.lng]);
  });

  if (bounds.length) map.fitBounds(bounds, { padding: [30,30], maxZoom: 13 });
}

// ---------- saved cases ----------
function getAllCases(){
  const obsCases = observations.map(o => ({ kind: 'Observation', severity: o.severity, ...o, label: o.diseasePest || o.symptom || 'Observation' }));
  const trapCases = traps.map(t => ({ kind: 'Trap', severity: null, ...t, label: `${t.trapType || 'Trap'}${t.pestName ? ' · ' + t.pestName : ''}` }));
  return [...obsCases, ...trapCases].sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt));
}

function caseMatchesFilters(c, f, farm){
  if (!farmMatchesLocationFilters(farm, f)) return false;
  if (f.crop){
    const cropMatch = (c.crop && c.crop === f.crop) || (farm && farm.crop === f.crop);
    if (!cropMatch) return false;
  }
  if (f.disease){
    const diseaseMatch = c.diseasePest === f.disease || c.pestName === f.disease;
    if (!diseaseMatch) return false;
  }
  if (f.severity && c.severity !== f.severity) return false;
  const dateCutoff = f.date ? new Date(f.date) : null;
  if (dateCutoff && new Date(c.createdAt) < dateCutoff) return false;
  return true;
}

function renderCases(){
  const f = getFilters();
  const rows = getAllCases().filter(c => caseMatchesFilters(c, f, farmById(c.farmId)));
  const list = $('cases');

  if (!rows.length){
    list.innerHTML = '<p class="empty-hint">No cases match the current filters.</p>';
    $('railCases').textContent = '0';
    return;
  }
  $('railCases').textContent = rows.length;

  list.innerHTML = rows.map(c => {
    const farm = farmById(c.farmId);
    const chip = c.severity ? `<span class="severity-chip ${c.severity.toLowerCase()}">${c.severity}</span>` : '<span class="severity-chip">—</span>';
    return `<button type="button" class="case-row" data-id="${c.id}" data-kind="${c.kind}">
      <span class="case-kind">${c.kind}</span>
      <span class="case-main"><b>${escapeHtml(c.label)}</b><span>${escapeHtml(farm ? farm.name : 'Unknown farm')}</span></span>
      ${chip}
      <span class="case-date">${fmtDate(c.createdAt)}</span>
    </button>`;
  }).join('');

  list.querySelectorAll('.case-row').forEach(btn => {
    btn.addEventListener('click', () => openCaseModal(btn.dataset.id, btn.dataset.kind));
  });
}

function openCaseModal(id, kind){
  const source = kind === 'Trap' ? traps : observations;
  const c = source.find(x => x.id === id);
  if (!c) return;
  const farm = farmById(c.farmId);

  const rows = kind === 'Trap'
    ? [
        ['Trap type', c.trapType || '—'],
        ['Pest', c.pestName || '—'],
        ['Count', c.pestCount],
        ['Farm', farm ? farm.name : '—'],
        ['Location', farm ? `${farm.taluk}, ${farm.district}` : '—'],
        ['Coordinates', `${c.lat.toFixed(5)}, ${c.lng.toFixed(5)}`],
        ['Logged', fmtDate(c.createdAt)],
      ]
    : [
        ['Crop', c.crop || '—'],
        ['Growth stage', c.growthStage || '—'],
        ['Symptom', c.symptom || '—'],
        ['Disease / pest', c.diseasePest || '—'],
        ['Severity', c.severity || 'Not assessed'],
        ['Farm', farm ? farm.name : '—'],
        ['Location', farm ? `${farm.taluk}, ${farm.district}` : '—'],
        ['Coordinates', `${c.lat.toFixed(5)}, ${c.lng.toFixed(5)}`],
        ['Logged', fmtDate(c.createdAt)],
      ];

  $('caseModalTitle').textContent = kind === 'Trap' ? 'Trap input' : 'Field observation';
  $('caseDetails').innerHTML =
    rows.map(([label, value]) => `<div class="detail-row"><span>${label}</span><span>${escapeHtml(value)}</span></div>`).join('') +
    (c.image ? `<img class="detail-img" src="${c.image}" alt="Field photo">` : '');

  $('caseModal').classList.remove('hidden');
}
function closeCaseModal(){ $('caseModal').classList.add('hidden'); }
$('caseModal').addEventListener('click', e => { if (e.target.id === 'caseModal') closeCaseModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeCaseModal(); });

// ---------- rail toggle (mobile) ----------
$('railToggle').addEventListener('click', () => {
  const rail = $('rail');
  const open = rail.classList.toggle('open');
  $('railToggle').setAttribute('aria-expanded', open);
});
document.querySelectorAll('.rail-nav a').forEach(a => a.addEventListener('click', () => {
  $('rail').classList.remove('open');
}));

// ---------- export ----------
$('exportBtn').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify({ farms, observations, traps }, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `agrios-export-${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

// ---------- sample data ----------
function daysAgo(n){
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

function buildSampleData(){
  const sampleFarms = [
    { name:'Periyar Paddy Fields',   farmerName:'Murugan S.',      taluk:'Thanjavur',    district:'Thanjavur',     crop:'Paddy',      lat:10.7870, lng:79.1378 },
    { name:'Kaveri Delta Farm',      farmerName:'Kalaiselvi R.',   taluk:'Kumbakonam',   district:'Thanjavur',     crop:'Paddy',      lat:10.9601, lng:79.3788 },
    { name:'Nilgiri Slope Estate',   farmerName:'Bhavani K.',      taluk:'Gudalur',      district:'Nilgiris',      crop:'Tea',        lat:11.5000, lng:76.4900 },
    { name:'Erode Cotton Acres',     farmerName:'Palanisamy V.',   taluk:'Erode',        district:'Erode',         crop:'Cotton',     lat:11.3410, lng:77.7172 },
    { name:'Coimbatore Coconut Grove', farmerName:'Suresh Kumar',  taluk:'Mettupalayam', district:'Coimbatore',    crop:'Coconut',    lat:11.2994, lng:76.9366 },
    { name:'Salem Sugarcane Farm',   farmerName:'Ramanathan P.',   taluk:'Attur',        district:'Salem',         crop:'Sugarcane',  lat:11.5950, lng:78.6009 },
    { name:'Madurai Banana Fields',  farmerName:'Chitra M.',       taluk:'Melur',        district:'Madurai',       crop:'Banana',     lat:9.9950,  lng:78.3417 },
    { name:'Tirunelveli Groundnut Plot', farmerName:'Anbazhagan T.', taluk:'Tenkasi',    district:'Tirunelveli',   crop:'Groundnut',  lat:8.9600,  lng:77.3152 },
    { name:'Vellore Tomato Farm',    farmerName:'Latha S.',        taluk:'Gudiyatham',   district:'Vellore',       crop:'Tomato',     lat:12.9430, lng:78.8700 },
    { name:'Dindigul Maize Fields',  farmerName:'Karthik R.',      taluk:'Palani',       district:'Dindigul',      crop:'Maize',      lat:10.4494, lng:77.5178 },
  ];

  const farmIds = sampleFarms.map(() => uid());
  const seededFarms = sampleFarms.map((f, i) => ({ id: farmIds[i], ...f, createdAt: daysAgo(30 - i) }));

  const obsTemplates = [
    { farm:0, crop:'Paddy', growthStage:'Tillering',    symptom:'Yellowing leaf tips',        diseasePest:'Bacterial Leaf Blight', severity:'Moderate', dOff:2 },
    { farm:0, crop:'Paddy', growthStage:'Flowering',    symptom:'Brown lesions on leaves',    diseasePest:'Rice Blast',            severity:'Severe',   dOff:5 },
    { farm:1, crop:'Paddy', growthStage:'Vegetative',   symptom:'Stunted growth in patches',  diseasePest:'Rice Tungro Virus',     severity:'Mild',     dOff:8 },
    { farm:1, crop:'Paddy', growthStage:'Tillering',    symptom:'Chewed leaf margins',        diseasePest:'Leaf Folder',           severity:'Mild',     dOff:1 },
    { farm:2, crop:'Tea',   growthStage:'Mature',       symptom:'Reddish blistered leaves',   diseasePest:'Blister Blight',        severity:'Moderate', dOff:4 },
    { farm:3, crop:'Cotton',growthStage:'Boll formation', symptom:'Wilting of upper leaves', diseasePest:'Fusarium Wilt',          severity:'Severe',   dOff:3 },
    { farm:3, crop:'Cotton',growthStage:'Flowering',    symptom:'Curling of young leaves',    diseasePest:'Cotton Leaf Curl Virus',severity:'Moderate', dOff:6 },
    { farm:4, crop:'Coconut', growthStage:'Bearing',    symptom:'Yellowing of lower fronds',  diseasePest:'Root Wilt Disease',     severity:'Mild',     dOff:9 },
    { farm:5, crop:'Sugarcane', growthStage:'Grand growth', symptom:'Red streaks on stalk',  diseasePest:'Red Rot',               severity:'Severe',   dOff:2 },
    { farm:6, crop:'Banana', growthStage:'Shooting',    symptom:'Yellow streaking on leaves', diseasePest:'Banana Bunchy Top Virus', severity:'Severe', dOff:1 },
    { farm:6, crop:'Banana', growthStage:'Vegetative',  symptom:'Black sigatoka spots',       diseasePest:'Sigatoka Leaf Spot',    severity:'Moderate', dOff:7 },
    { farm:7, crop:'Groundnut', growthStage:'Pegging',  symptom:'Circular leaf spots',        diseasePest:'Tikka Leaf Spot',       severity:'Mild',     dOff:5 },
    { farm:8, crop:'Tomato', growthStage:'Flowering',   symptom:'Fruit borer holes',          diseasePest:'Fruit Borer',           severity:'Moderate', dOff:2 },
    { farm:9, crop:'Maize', growthStage:'Whorl stage',  symptom:'Window-pane feeding marks',  diseasePest:'Fall Armyworm',         severity:'Severe',   dOff:1 },
    { farm:9, crop:'Maize', growthStage:'Vegetative',   symptom:'Small holes in leaves',      diseasePest:'Stem Borer',            severity:'Mild',     dOff:10 },
  ];
  const seededObs = obsTemplates.map(t => {
    const farm = seededFarms[t.farm];
    return {
      id: uid(), farmId: farm.id, crop: t.crop, growthStage: t.growthStage,
      symptom: t.symptom, diseasePest: t.diseasePest, severity: t.severity,
      lat: farm.lat + (Math.random()-0.5)*0.01, lng: farm.lng + (Math.random()-0.5)*0.01,
      image: null, createdAt: daysAgo(t.dOff),
    };
  });

  const trapTemplates = [
    { farm:3, type:'Sticky Trap',   pest:'Whitefly',            count:34, dOff:2 },
    { farm:3, type:'Light Trap',    pest:'Pink Bollworm',       count:12, dOff:6 },
    { farm:6, type:'Manual Count',  pest:'Banana Weevil',       count:5,  dOff:3 },
    { farm:9, type:'Light Trap',    pest:'Fall Armyworm',       count:41, dOff:1 },
    { farm:9, type:'Sticky Trap',   pest:'Shoot Fly',           count:9,  dOff:8 },
    { farm:5, type:'Manual Count',  pest:'Early Shoot Borer',   count:7,  dOff:4 },
    { farm:8, type:'Sticky Trap',   pest:'Fruit Fly',           count:22, dOff:2 },
    { farm:0, type:'Light Trap',    pest:'Brown Planthopper',   count:56, dOff:1 },
    { farm:1, type:'Light Trap',    pest:'Brown Planthopper',   count:18, dOff:5 },
    { farm:7, type:'Manual Count',  pest:'Leaf Miner',          count:4,  dOff:9 },
  ];
  const seededTraps = trapTemplates.map(t => {
    const farm = seededFarms[t.farm];
    return {
      id: uid(), farmId: farm.id, trapType: t.type, pestName: t.pest, pestCount: t.count,
      lat: farm.lat + (Math.random()-0.5)*0.01, lng: farm.lng + (Math.random()-0.5)*0.01,
      image: null, createdAt: daysAgo(t.dOff),
    };
  });

  return { seededFarms, seededObs, seededTraps };
}

$('seedBtn').addEventListener('click', () => {
  if (farms.length || observations.length || traps.length){
    if (!confirm('This adds sample farms, observations, and trap readings to your existing data. Continue?')) return;
  }
  const { seededFarms, seededObs, seededTraps } = buildSampleData();
  farms = [...farms, ...seededFarms];
  observations = [...observations, ...seededObs];
  traps = [...traps, ...seededTraps];
  saveAll(STORE.farms, farms);
  saveAll(STORE.observations, observations);
  saveAll(STORE.traps, traps);
  refreshFarmSelects();
  populateFilterOptions();
  renderEverything();
});

$('clearDataBtn').addEventListener('click', () => {
  if (!confirm('This permanently deletes all farms, observations, and trap readings on this device. Continue?')) return;
  farms = []; observations = []; traps = [];
  saveAll(STORE.farms, farms);
  saveAll(STORE.observations, observations);
  saveAll(STORE.traps, traps);
  refreshFarmSelects();
  populateFilterOptions();
  renderEverything();
});

// ---------- orchestration ----------
function renderEverything(){
  const data = getFilteredData();
  renderStats(data);
  renderCases();
  loadMapData();
  renderRiskDashboard();
  renderAdvisory();
  renderReviewState();
  renderFollowUps();
  $('railFarms').textContent = farms.length;
}

// ---------- active section highlight ----------
function initSectionTracking(){
  const navLinks = [...document.querySelectorAll('.rail-nav a')];
  const sections = navLinks.map(a => document.querySelector(a.getAttribute('href')));
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const idx = sections.indexOf(entry.target);
      if (idx === -1) return;
      navLinks[idx].classList.toggle('active', entry.isIntersecting);
    });
  }, { rootMargin: '-20% 0px -70% 0px' });
  sections.forEach(sec => sec && observer.observe(sec));
}

function runJohnPreview(){
  const resultBox = $('modelPreviewResult');
  resultBox.classList.remove('error');
  const diagnosis = currentDiagnosis?.disease_detected || currentDiagnosis?.predicted_label || 'No image uploaded yet';
  const confidence = currentDiagnosis ? `${Math.round(currentDiagnosis.confidence * 100)}%` : 'Awaiting image';
  const alerts = getRiskAlerts().map(item => `${item.level}: ${item.title}`).join('\n');
  resultBox.textContent = `LOCAL MODEL PREVIEW\nDiagnosis: ${diagnosis}\nConfidence: ${confidence}\nCrop stage: ${riskContext.stage}\nWeather signal: ${riskContext.weather}\n\nRISK SIGNALS\n${alerts}\n\nNext step: ${reviewStatus}`;
}

$('runModelBtn')?.addEventListener('click', runJohnPreview);

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  syncRiskFields();
  refreshFarmSelects();
  populateFilterOptions();
  renderEverything();
  initSectionTracking();
});