<template>
  <div class="advanced-filter">

    <!-- HEADER -->
    <div class="af-header">
      <div class="af-title-row">
        <span class="af-title">Advanced Filter</span>
        <span class="af-subtitle">Filtra per litologia e tipo di mineralizzazione</span>
      </div>
      <div class="af-badge" v-if="pozziSelezionati !== null">
        {{ pozziSelezionati }} pozzi selezionati
      </div>
      
    </div>

    <!-- ====== FILTRO PROFONDITÀ GLOBALE ====== -->
    <div class="global-depth-bar">
      <div class="depth-info">
        <span class="depth-title">INTERVALLO DI PROFONDITÀ UNICO (m)</span>
        <div class="depth-inputs">
          <span>Da</span>
          <input type="number" v-model.number="profMin" class="depth-input" min="0" max="5000" step="50">
          <span>a</span>
          <input type="number" v-model.number="profMax" class="depth-input" min="0" max="5000" step="50">
          <span class="depth-unit">m</span>
        </div>
      </div>

      <div class="dual-slider-container">
        <div 
          class="slider-track" 
          :style="{
            left: (profMin / 5000 * 100) + '%',
            width: ((profMax - profMin) / 5000 * 100) + '%'
          }"
        ></div>
        
        <input 
          type="range" 
          v-model.number="profMin" 
          min="0" 
          max="5000" 
          step="50" 
          class="slider-range"
          :style="{ zIndex: profMin > 4500 ? '5' : '3' }"
        >
        <input 
          type="range" 
          v-model.number="profMax" 
          min="0" 
          max="5000" 
          step="50" 
          class="slider-range"
          style="z-index: 4;"
        >
      </div>
      
    </div>
    <!-- ====== BARRA INFERIORE ====== -->
    <div class="af-footer">
      <div class="footer-left">
        <span class="footer-count">
          Pozzi selezionati: <strong>{{ pozziSelezionati ?? '–' }}</strong> / {{ totaleDataset }} totali
        </span>
      </div>

      <div class="footer-chips">
        <span
          v-for="chip in filtriAttivi"
          :key="chip.label"
          class="active-chip"
          :style="{ borderColor: chip.color || '#999', color: chip.color || '#666' }"
        >
          {{ chip.label }}
        </span>
      </div>

      <div class="footer-actions">
        <button class="btn-reset" @click="resetFiltri">Reset</button>
        <button class="btn-apply" @click="applicaFiltri">Applica → Mappa</button>
      </div>
    </div>
    <!-- CORPO: LAYOUT A 3 COLONNE (CHIPS + MATRICE) -->
    <div class="af-body-new">

      <!-- ====== 1. PANNELLO LITOLOGIA ====== -->
      
      <!-- ====== 1. PANNELLO LITOLOGIA ====== -->
      <div class="filter-card">
        <div class="card-header">
          <h3>Litologia</h3>
        </div>
        
        <div class="search-bar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="text" v-model="searchLito" placeholder="Cerca litologia...">
        </div>

        <!-- NUOVO: SELETTORE RUOLO -->
        <div class="role-selector">
          <label class="role-radio">
            <input type="radio" v-model="ruoloLito" value="tutte"> Tutte
          </label>
          <label class="role-radio">
            <input type="radio" v-model="ruoloLito" value="primaria"> Primaria
          </label>
          <label class="role-radio">
            <input type="radio" v-model="ruoloLito" value="subordinata"> Subordinata
          </label>
        </div>

        <!-- ATTENZIONE: QUESTO BLOCCO NON DEVE MANCARE -->
        <div class="chips-container">
          <div
            v-for="t in filteredTerminiLito"
            :key="t.termine"
            class="selectable-chip"
            :class="{ 'is-active': selectedLito.includes(t.termine) }"
            :style="[
              getChipSizeStyle(t.n_pozzi, maxLitoCount),
              selectedLito.includes(t.termine) ? getLitoActiveStyle(t.termine) : {}
            ]"
            @click="toggleLito(t.termine)"
          >
            <div class="chip-icon">
              <svg v-if="selectedLito.includes(t.termine)" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>
            </div>
            <div class="chip-text">
              <span class="chip-title">{{ t.termine }}</span>
              <span class="chip-count">{{ t.n_pozzi }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 2. PANNELLO MINERALIZZAZIONE ====== -->
      <div class="filter-card">
        <div class="card-header">
          <h3>Mineralizzazione</h3>
        </div>
        
        <div class="search-bar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="text" v-model="searchFluido" placeholder="Cerca mineralizzazione...">
        </div>

        <div class="chips-container">
          <div
            v-for="f in filteredFluidiData"
            :key="f.codice"
            class="selectable-chip"
            :class="{ 'is-active': selectedFluidi.includes(f.codice) }"
            :style="[
              getChipSizeStyle(f.n_eventi, maxFluidoCount),
              selectedFluidi.includes(f.codice) ? getFluidoActiveStyle(f) : {}
            ]"
            @click="toggleFluido(f.codice)"
          >
            <div class="chip-icon">
              <svg v-if="selectedFluidi.includes(f.codice)" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>
            </div>
            <div class="chip-text">
              <span class="chip-title">{{ f.fluido }}</span>
              <span class="chip-count">{{ f.n_eventi }}</span>
            </div>
          </div>
        </div>
      
    
      </div>

      <!-- ====== 3. PANNELLO MATRICE ====== -->
      <div class="filter-card matrix-card">
        <div class="card-header">
          <h3>Correlazione Fluido ↔ Litologia</h3>
        </div>

        <p class="matrix-desc">
          Quante volte ciascun tipo di fluido è stato incontrato in ciascuna litologia.
        </p>

        <div class="matrix-scroll" v-if="matrice.length">
          <table class="matrix-table">
            <thead>
              <tr>
                <th class="lito-col">LITOLOGIA</th>
                <th v-for="f in colonneMatrice" :key="f" class="fluido-col">
                  <span class="fluido-dot-small" :style="{ background: getFluidoColorByName(f) }"></span>
                  {{ f.toUpperCase() }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in righeMatrice" :key="row.lito">
                <td class="lito-name">
                  {{ row.lito }}
                </td>
                <td
                  v-for="f in colonneMatrice"
                  :key="f"
                  class="matrix-cell"
                  :class="getCellClass(row[f])"
                >
                  <span v-if="row[f]">{{ row[f] }}</span>
                  <span v-else class="cell-empty">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="matrix-loading">Caricamento matrice...</div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'


const emit = defineEmits(['applica-filtri'])
const API_BASE = 'http://127.0.0.1:8000'
const props = defineProps({
  token: { type: String, default: null }
})

// ============ STATE UNIFICATO ============
const profMin = ref(0)
const profMax = ref(5000)
const ruoloLito = ref('tutte') // <--- NUOVO STATO

const selectedLito   = ref([])
const selectedFluidi = ref([])

const terminiLito  = ref([])
const fluidiData   = ref([])
const cooccorrenza = ref([])

const pozziSelezionati       = ref(null)
const totaleDataset          = ref(160)

// Ricerca locale
const searchLito = ref('')
const searchFluido = ref('')

// Filtri calcolati in base alla ricerca
const filteredTerminiLito = computed(() => {
  if (!searchLito.value) return terminiLito.value
  const q = searchLito.value.toLowerCase()
  return terminiLito.value.filter(t => t.termine.toLowerCase().includes(q))
})

const filteredFluidiData = computed(() => {
  if (!searchFluido.value) return fluidiData.value
  const q = searchFluido.value.toLowerCase()
  return fluidiData.value.filter(f => f.fluido.toLowerCase().includes(q))
})

// ============ DIMENSIONI PROPORZIONALI CHIPS ============
const maxLitoCount = computed(() => {
  if (!terminiLito.value.length) return 1
  return Math.max(...terminiLito.value.map(t => t.n_pozzi || 1))
})

const maxFluidoCount = computed(() => {
  if (!fluidiData.value.length) return 1
  return Math.max(...fluidiData.value.map(f => f.n_eventi || 1))
})

function getChipSizeStyle(count, maxCount) {
  if (!maxCount || !count) return {}
  const ratio = Math.min(count / maxCount, 1)
  const padX = 10 + ratio * 16   
  const fontSize = 11 + ratio * 3 
  
  return {
    padding: `8px ${padX}px`,
    fontSize: `${fontSize}px`
  }
}

// ============ COLORI FLUIDI ============
const FLUIDO_COLORS = {
  1: '#4fc3f7',
  2: '#81c784',
  3: '#ef5350',
  4: '#8d6e63',
  5: '#ffa726',
  6: '#ab47bc',
  7: '#26c6da',
  8: '#d4e157',
}

function getFluidoColor(codice) {
  return FLUIDO_COLORS[codice] || '#999'
}

function getFluidoColorByName(nome) {
  const fluido = fluidiData.value.find(f => f.fluido === nome)
  return fluido ? getFluidoColor(fluido.codice) : '#999'
}

function getLitoActiveStyle(termine) {
  const index = terminiLito.value.findIndex(t => t.termine === termine)
  const bgColors = ['#083d77', '#1d5f9e', '#347ec0', '#569ce3', '#83bdf2']
  const bg = bgColors[Math.min(index > -1 ? index : 4, bgColors.length - 1)]
  return { backgroundColor: bg, color: 'white', borderColor: bg }
}

function getFluidoActiveStyle(f) {
  const name = f.fluido.toLowerCase()
  if (name.includes('acqua salata')) return { backgroundColor: '#007aff', color: 'white', borderColor: '#007aff' }
  if (name.includes('gas')) return { backgroundColor: '#f5a623', color: 'white', borderColor: '#f5a623' }
  if (name.includes('olio')) return { backgroundColor: '#2e7d32', color: 'white', borderColor: '#2e7d32' }
  
  const baseColor = getFluidoColor(f.codice)
  return { backgroundColor: baseColor, color: 'white', borderColor: baseColor }
}

// ============ MATRICE CO-OCCORRENZA ============
const colonneMatrice = computed(() => {
  const fluidiNomi = [...new Set(cooccorrenza.value.map(r => r.fluido))]
  return fluidiNomi.slice(0, 10)
})

const righeMatrice = computed(() => {
  if (!cooccorrenza.value.length || !terminiLito.value.length) return []
  return terminiLito.value.map(t => {
    const row = { lito: t.termine }
    colonneMatrice.value.forEach(fluido => {
      const entry = cooccorrenza.value.find(
        e => e.fluido === fluido && e.litologia === t.termine
      )
      row[fluido] = entry ? entry.n_eventi : null
    })
    return row
  })
})

const matrice = computed(() => righeMatrice.value)

function getCellClass(value) {
  if (!value) return 'cell-zero'
  if (value <= 5)  return 'cell-low'
  if (value <= 25) return 'cell-mid'
  return 'cell-high'
}

// ============ FILTRI ATTIVI ============
const filtriAttivi = computed(() => {
  const chips = []
  selectedLito.value.forEach(termine => {
    chips.push({ label: termine, color: '#083d77' })
  })
  selectedFluidi.value.forEach(cod => {
    const f = fluidiData.value.find(f => f.codice === cod)
    if (f) chips.push({ label: f.fluido, color: getFluidoColor(cod) })
  })
  if (profMin.value > 0 || profMax.value < 5000) {
    chips.push({ label: `${profMin.value}–${profMax.value} m`, color: '#666' })
  }
  // NUOVO: Mostra il ruolo se non è "tutte"
  if (ruoloLito.value !== 'tutte') {
    chips.push({ label: `Ruolo: ${ruoloLito.value}`, color: '#666' })
  }
  return chips
})

// ============ TOGGLE ============
function toggleLito(termine) {
  const idx = selectedLito.value.indexOf(termine)
  if (idx === -1) selectedLito.value.push(termine)
  else selectedLito.value.splice(idx, 1)
  aggiornaPozziSelezionati()
}

function toggleFluido(cod) {
  const idx = selectedFluidi.value.indexOf(cod)
  if (idx === -1) selectedFluidi.value.push(cod)
  else selectedFluidi.value.splice(idx, 1)
  aggiornaPozziSelezionati()
}

// ============ FETCH ============
async function fetchTerminiLito() {
  try {
    const params = new URLSearchParams()
    if (profMin.value > 0) params.append('prof_min', profMin.value)
    if (profMax.value < 5000) params.append('prof_max', profMax.value)
    if (ruoloLito.value !== 'tutte') params.append('ruolo', ruoloLito.value)
    const res = await fetch(`${API_BASE}/pozzi/litologie/termini?${params}`)
    if (!res.ok) return
    // 1. Salvi la risposta completa
    const responseData = await res.json()
    
    // 2. Assegni solo l'array dei termini alla tua variabile reattiva
    terminiLito.value = responseData.dati
  } catch (e) {
    console.error('Errore fetch termini:', e)
  }
}

async function fetchFluidi() {
  try {
    const params = new URLSearchParams()
    params.append('ruolo', ruoloLito.value)  // ← Passa SEMPRE il ruolo
    
    const res = await fetch(`${API_BASE}/pozzi/mineralizzazioni/tipi?${params}`)
    if (!res.ok) return
    const data = await res.json()
    fluidiData.value = data
  } catch (e) {
    console.error('Errore fetch fluidi:', e)
  }
}

/*
async function fetchCooccorrenza() {
  try {
    const params = new URLSearchParams()
    if (profMin.value > 0) params.append('prof_min', profMin.value)
    if (profMax.value < 5000) params.append('prof_max', profMax.value)
    if (ruoloLito.value !== 'tutte') params.append('ruolo', ruoloLito.value)
    const res = await fetch(`${API_BASE}/pozzi/mineralizzazioni/cooccorrenza?${params}`)
    if (!res.ok) return
    cooccorrenza.value = await res.json()
  } catch (e) {
    console.error('Errore fetch co-occorrenza:', e)
  }
}
  */
async function fetchCooccorrenza() {
  try {
    const params = new URLSearchParams()
    if (profMin.value > 0) params.append('prof_min', profMin.value)
    if (profMax.value < 5000) params.append('prof_max', profMax.value)
    if (ruoloLito.value !== 'tutte') params.append('ruolo', ruoloLito.value)

    const res = await fetch(`${API_BASE}/pozzi/mineralizzazioni/cooccorrenza?${params}`, {
      headers: props.token ? { Authorization: `Bearer ${props.token}` } : {}
    })
    if (!res.ok) {
      console.error('Errore co-occorrenza:', res.status)
      cooccorrenza.value = []
      return
    }
    cooccorrenza.value = await res.json()
  } catch (e) {
    console.error('Errore fetch co-occorrenza:', e)
  }
}

async function aggiornaPozziSelezionati() {
  try {
    const params = new URLSearchParams()
    /*if (selectedFluidi.value.length === 1) {
      params.append('tipo_fluido', selectedFluidi.value[0])
    }*/
    selectedFluidi.value.forEach(fluido => {
      params.append('tipo_fluido', fluido)
    })
    if (profMin.value > 0) params.append('prof_min', profMin.value)
    if (profMax.value < 5000) params.append('prof_max', profMax.value)
    if (ruoloLito.value !== 'tutte') params.append('ruolo', ruoloLito.value)
    selectedLito.value.forEach(termine => {
      params.append('termine_lito', termine)
    })

    const res = await fetch(`${API_BASE}/pozzi/mappa/avanzata?${params}`)
    if (!res.ok) return
    const data = await res.json()
    pozziSelezionati.value = data.length
  } catch (e) {
    console.error('Errore aggiornamento pozzi:', e)
  }
}

// ============ APPLICA / RESET ============
function applicaFiltri() {
  emit('applica-filtri', {
    fluidi: selectedFluidi.value,
    lito: selectedLito.value,
    profMin: profMin.value,
    profMax: profMax.value,
    ruoloLito: ruoloLito.value // <-- NUOVO
  })
}

function resetFiltri() {
  selectedLito.value   = []
  selectedFluidi.value = []
  profMin.value = 0
  profMax.value = 5000
  ruoloLito.value = 'tutte' // <-- NUOVO
  pozziSelezionati.value = null
  aggiornaPozziSelezionati()
}

// ============ WATCHERS ============
// NUOVO: Reagisci automaticamente quando si cambia il radio button!
watch(ruoloLito, async () => {
  await fetchFluidi()
  await fetchTerminiLito()
  await fetchCooccorrenza()
  await aggiornaPozziSelezionati()
})
watch(profMin, (val) => {
  if (val >= profMax.value) profMin.value = profMax.value - 50
})

watch(profMax, (val) => {
  if (val <= profMin.value) profMax.value = profMin.value + 50
})

watch([profMin, profMax], async () => {
  await fetchTerminiLito()
  await fetchCooccorrenza()
  await aggiornaPozziSelezionati()
})

onMounted(async () => {
  await fetchFluidi()
  
  await fetchTerminiLito()
  await fetchCooccorrenza()
  await aggiornaPozziSelezionati()
})
</script>

<style scoped>
/* ====== LAYOUT GENERALE ====== */
.advanced-filter {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f0ebe2;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  overflow: hidden;
}

/* ====== HEADER ====== */
.af-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: #e8dcc8;
  border-bottom: 1px solid #c8b89a;
  flex-shrink: 0;
}

.af-title {
  font-size: 16px;
  font-weight: 700;
  color: #3d3020;
  margin-right: 10px;
}

.af-subtitle {
  font-size: 12px;
  color: #888;
  font-style: italic;
}

.af-badge {
  background: #2e7d32;
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 14px;
  border-radius: 20px;
}

/* ====== BARRA PROFONDITÀ GLOBALE RIDOTTA ====== */
/* ====== BARRA PROFONDITÀ GLOBALE RIDOTTA ====== */
.global-depth-bar {
  background: #ffffff;
  margin: 1% 50% 1% 1%;     /* Margine esterno ridotto (soprattutto sopra) */
  padding: 8px 14px;          /* Spaziatura interna ridotta */
  border-radius: 8px;
  border: 1px solid #e0d8cc;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 4px;                   /* Distanza ridotta tra gli elementi interni */
  flex-shrink: 0;
}

.depth-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.depth-title {
  font-size: 11px;
  font-weight: 700;
  color: #5d4e40;
  letter-spacing: 0.5px;
}

.depth-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.depth-input {
  width: 70px;
  padding: 4px 6px;
  border: 1.5px solid #d4c5b0;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
  color: #3d3020;
  background: #faf8f5;
}

.depth-input:focus {
  outline: none;
  border-color: #7d6b5a;
  background: #ffffff;
}

.depth-unit {
  font-weight: 600;
  color: #888;
}

.dual-slider-container {
  position: relative;
  height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.slider-track {
  position: absolute;
  height: 3px;
  background: #7d6b5a;
  border-radius: 3px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.slider-range {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  pointer-events: none;
  margin: 0;
}

.slider-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #5d4e40;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 5px rgba(0,0,0,0.3);
  cursor: grab;
  pointer-events: all;
  transition: transform 0.15s ease;
}

.slider-range::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  background: #3d3020;
}

/* ====== CORPO A 3 COLONNE IDENTICHE ====== */
.af-body-new {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  /*gap: 0px;*/
  padding: 12px;
  flex: 1;
  overflow: hidden;
  box-sizing: border-box;
}

.filter-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  /*border: 0px solid #e0d8cc;*/
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden;
}
.matrix-card{
  
  border: 12px solid #e0d8cc;
  
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  flex-shrink: 0;
}

.card-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #1c3b57;
}

/* ====== BARRA DI RICERCA ====== */
.search-bar {
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 30px;
  padding: 8px 14px;
  margin-bottom: 16px;
  flex-shrink: 0;
  transition: border-color 0.2s;
}

.search-bar:focus-within {
  border-color: #709bc8;
}

.search-bar input {
  border: none;
  background: transparent;
  outline: none;
  flex: 1;
  font-size: 12px;
  color: #333;
  margin-left: 10px;
}

/* ====== CHIPS ORIZZONTALI ====== */
.chips-container {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 10px;
  flex: 1;
  overflow-y: auto;
  align-content: flex-start;
  padding-right: 4px;
}

.selectable-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #f0f4f8;
  border: 2px solid transparent;
  border-radius: 30px;
  cursor: pointer;
  color: #4a6b8c;
  transition: all 0.2s ease;
  user-select: none;
}

.selectable-chip:hover:not(.is-active) {
  background-color: #e2e8f0;
}

.chip-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.chip-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.2;
}

.chip-title {
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.chip-count {
  font-weight: 600;
  opacity: 0.85;
}

/* ====== MATRICE ====== */
.matrix-desc {
  font-size: 11px;
  color: #666;
  line-height: 1.4;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.matrix-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  margin-bottom: 10px;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.matrix-table th {
  padding: 6px 6px;
  text-align: center;
  font-size: 9px;
  font-weight: 700;
  color: #888;
  text-transform: uppercase;
  border-bottom: 1px solid #eee;
  background: #fff;
  position: sticky;
  top: 0;
}

.lito-col { text-align: left !important; min-width: 80px; }
.fluido-col { min-width: 45px; }

.fluido-dot-small {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 3px;
  vertical-align: middle;
}

.matrix-table td {
  padding: 5px 6px;
  text-align: center;
  border-bottom: 1px solid #f5f5f5;
}

.lito-name {
  text-align: left !important;
  font-weight: 600;
  color: #444;
  font-size: 10px;
}

.matrix-cell {
  font-weight: 600;
  border-radius: 4px;
}

.cell-zero { color: #ddd; }
/*.cell-low  { background: #e8f5e9; color: #2e7d32; }
.cell-mid  { background: #fff3e0; color: #e65100; }
.cell-high { background: #ef5350; color: white; }
.cell-empty { color: #ddd; font-weight: 400; }*/
.cell-mid{background-color: rgb(236, 199, 117); font-weight: bolder;}
.cell-high { background: #ef5350; font-weight: bolder; }
.intensity-legend {
  flex-shrink: 0;
  border-top: 1px solid #f0e8dc;
  padding-top: 8px;
}

.legend-title {
  display: block;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  color: #aaa;
  margin-bottom: 4px;
}

.legend-chips {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.intensity-chip {
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 9px;
  font-weight: 700;
}

.i1  { background: #e8f5e9; color: #2e7d32; }
.i5  { background: #c8e6c9; color: #1b5e20; }
.i25 { background: #fff3e0; color: #e65100; }
.i48 { background: #ef5350; color: white; }

.legend-note {
  font-size: 9px;
  color: #aaa;
  margin-left: 4px;
}

.matrix-loading {
  text-align: center;
  color: #bbb;
  font-size: 12px;
  padding: 20px;
}

/* ====== FOOTER ====== */
.af-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  background: #e8dcc8;
  border-top: 1px solid #c8b89a;
  flex-shrink: 0;
}

.footer-left {
  font-size: 13px;
  color: #444;
  white-space: nowrap;
}

.footer-left strong { color: #3d3020; }

.footer-chips {
  display: flex;
  gap: 6px;
  flex: 1;
  flex-wrap: wrap;
  max-height: 35px;
  overflow: hidden;
}

.active-chip {
  padding: 3px 10px;
  border-radius: 20px;
  border: 1.5px solid;
  font-size: 11px;
  font-weight: 600;
  background: white;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.btn-reset {
  padding: 7px 18px;
  border: 1.5px solid #aaa;
  border-radius: 6px;
  background: white;
  color: #666;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reset:hover { background: #f5f5f5; }

.btn-apply {
  padding: 7px 20px;
  border: none;
  border-radius: 6px;
  background: #5d4e40;
  color: white;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-apply:hover { background: #3d3020; }

/* Scrollbar personalizzata per i pannelli interni */
.filter-card::-webkit-scrollbar,
.chips-container::-webkit-scrollbar,
.matrix-scroll::-webkit-scrollbar { 
  width: 4px; 
}
.filter-card::-webkit-scrollbar-thumb,
.chips-container::-webkit-scrollbar-thumb,
.matrix-scroll::-webkit-scrollbar-thumb { 
  background: #d4c5b0; 
  border-radius: 2px; 
}
</style>