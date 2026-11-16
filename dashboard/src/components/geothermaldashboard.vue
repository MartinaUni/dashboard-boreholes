<template>
  <div class="dashboard">
    <!-- HEADER -->
    <!-- HEADER -->
    <header class="header">
      <div class="header-content">
        <h1>GEOTHERMAL DASHBOARD</h1>
        <p class="subtitle">Italia: {{ pozzi.length }} active wells</p>
      </div>
      
      <!-- GESTIONE LOGIN REALE -->
      <!-- GESTIONE LOGIN REALE -->
      <div class="auth-section">
        <div v-if="userRole === 'base'">
          <button class="btn-login" @click="showLogin = !showLogin; authMode = 'login'"> Accedi / Registrati</button>
        </div>
        <div v-else class="user-logged-in">
          <span>Utente: <strong>{{ username }}</strong> ({{ userRole }})</span>
          <button class="btn-logout" @click="eseguiLogout">Esci</button>
        </div>

        <!-- MODALE DI LOGIN / REGISTRAZIONE -->
        <div v-if="showLogin && userRole === 'base'" class="login-popup">
          <h4>{{ authMode === 'login' ? 'Accesso Utenti' : 'Crea un account (Esperto)' }}</h4>
          
          <p v-if="authMessage" class="success-msg">{{ authMessage }}</p>

          <input type="text" v-model="loginForm.username" placeholder="Username">
          <input 
            type="password" 
            v-model="loginForm.password" 
            placeholder="Password" 
            @keyup.enter="authMode === 'login' ? eseguiLogin() : eseguiRegistrazione()"
          >
          
          <p v-if="loginError" class="error-msg">{{ loginError }}</p>

          <div class="auth-toggle">
            <a href="#" @click.prevent="authMode = authMode === 'login' ? 'register' : 'login'; loginError = ''; authMessage = '';">
              {{ authMode === 'login' ? 'Non hai un account? Registrati' : 'Hai già un account? Accedi' }}
            </a>
          </div>

          <div class="login-actions">
            <button @click="showLogin = false" class="btn-cancel">Annulla</button>
            <button v-if="authMode === 'login'" @click="eseguiLogin" class="btn-confirm">Accedi</button>
            <button v-else @click="eseguiRegistrazione" class="btn-confirm">Registrati</button>
          </div>
        </div>
      </div>
    </header>
    <!-- TABS NAVIGATION -->
    <!-- TABS NAVIGATION (sostituisci la div tabs-container) -->
    <div class="tabs-container">
      <button 
        v-for="tab in tabs" 
        :key="tab.name"
        :class="[
          'tab', 
          { active: activeTab === tab.name }, 
          { disabled: tab.requiresExpert && userRole !== 'esperto' }
        ]"
        @click="cambiaTab(tab)"
      >
        {{ tab.name }}
       
      </button>
    </div>

    <!-- MAIN CONTENT -->
    <div class="content-wrapper" v-if="activeTab === 'Map'">
      <!-- FILTRI SINISTRA -->
      <aside class="filters-panel">
        <div class="filter-section">
          <h3>FILTER</h3>
          
          <!-- Slider Profondità -->
          <div class="filter-item">
            <label>Profondità</label>
            <div class="slider-container">
              <input 
                v-model.number="filters.profMin" 
                type="range" 
                min="0" 
                max="5000" 
                step="100"
                class="slider slider-depth"
              >
              <span class="slider-value">{{ filters.profMin }}m</span>
            </div>
          </div>

          <!-- Slider Temperatura -->
          <div class="filter-item">
            <label>Temperatura</label>
            <div class="slider-container">
              <input 
                v-model.number="filters.tempMin" 
                type="range" 
                min="0" 
                max="300" 
                step="10"
                class="slider slider-temp"
              >
              <span class="slider-value">{{ filters.tempMin }}°C</span>
            </div>
          </div>

          <!-- Percentili -->
          <!-- Percentili -->
          <div class="filter-item">
            <label>Percentili</label>
            <div class="slider-container">
              <input 
                v-model.number="filters.percentile" 
                type="range" 
                min="0" 
                max="100" 
                step="5"
                class="slider slider-percentile"
              >
              <span class="slider-value">{{ filters.percentile }}%</span>
            </div>
            <!-- Modificato qui per mostrare la temperatura calcolata -->
            <p class="did" v-if="filters.percentile > 0" style="font-size: 10px; color: #666; margin-top: 4px;">
              T ≥ {{ temperaturaPercentile }}°C ({{ filters.percentile }}° percentile)
            </p>
          </div>

        </div>
      </aside>

      <!-- MAPPA CENTRO -->
      <main class="map-panel">
        <div id="map" class="map-container"></div>
        
        <!-- LEGENDA DESTRA DELLA MAPPA -->
        <div class="legend-box" ref="square" @mousedown="(e) => startDrag(e, square)">
          <!-- Color Gradient Legend -->
          <div class="gradient-legend">
            <h4>Temperature Gradient</h4>
            <div class="gradient-row">
              <span class="gradient-color" style="background: #1f77b4;"></span>
              <span class="gradient-label">&lt; 50°C</span>
            </div>
            <div class="gradient-row">
              <span class="gradient-color" style="background: #2ca02c;"></span>
              <span class="gradient-label">50 - 100°C</span>
            </div>
            <div class="gradient-row">
              <span class="gradient-color" style="background: #f0a000;"></span>
              <span class="gradient-label">100 - 150°C</span>
            </div>
            <div class="gradient-row">
              <span class="gradient-color" style="background: #ff7f0e;"></span>
              <span class="gradient-label">150 - 200°C</span>
            </div>
            <div class="gradient-row">
              <span class="gradient-color" style="background: purple;"></span>
              <span class="gradient-label">&gt; 200 °C</span>
            </div>
          </div>
          
        </div>
      </main>
  <aside class="details-panel" :class="{ 'panel-confronto': modalitaConfronto }">
    <button class="btn-reset-confronto" @click="dettaglioPozzo = null; modalitaConfronto = false; dettaglioSecondoPozzo = null">
       Chiudi
    </button>
    <div v-if="loadingDettaglio" class="empty-state">
      <p>Caricamento...</p>
    </div>

    <!-- MODALITÀ CONFRONTO: due pozzi affiancati -->
    <div v-else-if="modalitaConfronto && dettaglioPozzo && dettaglioSecondoPozzo">
      <div class="confronto-header">
        <span>Confronto pozzi</span>
        <button class="btn-reset-confronto" @click="modalitaConfronto = false; dettaglioSecondoPozzo = null">
            Chiudi confronto
        </button>
      </div>
      <WellProfilePanel
        :pozzi="[dettaglioPozzo, dettaglioSecondoPozzo]"
        :show-header="false"
      />
    </div>

    <!-- MODALITÀ SINGOLA: anagrafica + profilo -->
    <div v-else-if="dettaglioPozzo" class="pozzo-details">

      <h3>{{ dettaglioPozzo.anagrafica.nome }}</h3>

      <p style="font-size:10px; color:#aaa; margin-bottom:8px;">
         Clicca un secondo pozzo sulla mappa per confrontarli
      </p>

      <div class="details-section">
        <h4>Anagrafica</h4>
        <div class="details-grid">
          <p><strong>Profondità:</strong> {{ dettaglioPozzo.anagrafica.prof ?? 'N/D' }}m</p>
          <p><strong>Quota:</strong> {{ dettaglioPozzo.anagrafica.quota ?? 'N/D' }}m</p>
          <p><strong>Proprietario:</strong> {{ dettaglioPozzo.anagrafica.proprietar ?? 'N/D' }}</p>
          <p><strong>Data compl.:</strong> {{ dettaglioPozzo.anagrafica.datacomp ?? 'N/D' }}</p>
          <p><strong>Località:</strong> {{ dettaglioPozzo.anagrafica.locgeo ?? 'N/D' }}</p>
        </div>
      </div>

      <div class="details-section">
        <h4>Posizione</h4>
        <div class="details-grid">
          <p><strong>Regione:</strong> {{ dettaglioPozzo.posizione.regione ?? 'N/D' }}</p>
          <p><strong>Provincia:</strong> {{ dettaglioPozzo.posizione.provincia ?? 'N/D' }}</p>
          <p><strong>Comune:</strong> {{ dettaglioPozzo.posizione.comune ?? 'N/D' }}</p>
        </div>
      </div>

      <div class="details-section">
        <h4>Classificazione</h4>
        <div class="details-grid">
          <p><strong>Tipo:</strong> {{ dettaglioPozzo.classificazione.tipo ?? 'N/D' }}</p>
          <p><strong>Scopo:</strong> {{ dettaglioPozzo.classificazione.scopo ?? 'N/D' }}</p>
          <p><strong>Uso:</strong> {{ dettaglioPozzo.classificazione.uso ?? 'N/D' }}</p>
          <p><strong>Stato:</strong> {{ dettaglioPozzo.classificazione.stato ?? 'N/D' }}</p>
          <p><strong>Esito:</strong> {{ dettaglioPozzo.classificazione.esito ?? 'N/D' }}</p>
        </div>
      </div>

      <div class="details-section">
        <h4>Dati Termici</h4>
        <div class="details-grid">
          <p><strong>Temp. Max:</strong> {{ dettaglioPozzo.kpi.temp_max ?? 'N/D' }}°C</p>
          <p><strong>Gradiente medio:</strong> {{ dettaglioPozzo.kpi.grad_medio ?? 'N/D' }}°C/km</p>
        </div>
      </div>

      <!-- Profilo singolo -->
      <div class="details-section" v-if="dettaglioPozzo.temperatura_vs_profondita?.length">
        <h4>Profilo T vs Profondità</h4>
        <WellProfilePanel
          :pozzi="[dettaglioPozzo]"
          :show-header="false"
        />
      </div>

    </div>

    <div v-else class="empty-state">
      <p>Seleziona un pozzo sulla mappa</p>
      <p style="font-size:10px; color:#bbb; margin-top:8px;">
        Clicca un secondo pozzo per confrontarli
      </p>
    </div>

  </aside>

    </div>
    <!-- ADVANCED FILTER -->
    <AdvancedFilter 
      v-else-if="activeTab === 'Advanced Filter'"
      :token="token"
      @applica-filtri="onApplicaFiltri"
      style="flex: 1; overflow: hidden;"
    />
    <!--  AGGIUNGo QUI, dopo il </div> di content-wrapper -->
    <DataDistributions v-else-if="activeTab === 'Data Distributions'" />
  </div>
</template>

<script setup>

import WellProfilePanel from './WellProfilePanel.vue'
import AdvancedFilter from './advancedfilter.vue'
import 'leaflet/dist/leaflet.css'
import DataDistributions from '/src/components/datadistribution.vue'
import L from 'leaflet'
import { ref, onMounted, computed, watch, nextTick } from 'vue'


import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.default.css'
import 'leaflet.markercluster'

//GESTIONE UTENTI:
//Per implementare l'autenticazione reale, dobbiamo sostituire la tendina fittizia con un modulo di login che invii le credenziali al backend (FastAPI) e riceva in cambio un token JWT e il ruolo dell'utente.

// ============ AUTENTICAZIONE ============
//const userRole = ref('base')
const username = ref('')
const token = ref(null)

const showLogin = ref(false)
const authMode = ref('login') // Può essere 'login' o 'register'
const authMessage = ref('')   // Per i messaggi di successo (es. registrazione completata)
const loginForm = ref({ username: '', password: '' })
const loginError = ref('')
// fine autenticazione

const disponibilitaPozzo = ref(null)

//const activeTab = ref('Map')
const userRole = ref('base') 

// drag

// drag & drop della legenda
const square = ref(null)

let startX = 0
let startY = 0
let initialLeft = 0
let initialTop = 0

function cambiaTab(tab) {
  // Se la tab richiede l'utente esperto e l'utente NON lo è, non fare nulla
  //if (tab.requiresExpert && userRole.value !== 'esperto') {
  //  return;
  //}
  // Altrimenti cambia tab
  activeTab.value = tab.name;
}

const startDrag = (e) => {
  // Ignora il click se proviene da slider o input interni (se presenti)
  if (['INPUT', 'BUTTON', 'LABEL'].includes(e.target.tagName)) return

  const element = square.value
  if (!element) return

  // Disabilita la selezione testo durante il drag
  e.preventDefault()

  // Salva la posizione iniziale del mouse
  startX = e.clientX
  startY = e.clientY

  // Recupera le coordinate correnti rispetto al contenitore (.map-panel)
  const rect = element.getBoundingClientRect()
  const parentRect = element.parentElement.getBoundingClientRect()

  initialLeft = rect.left - parentRect.left
  initialTop = rect.top - parentRect.top

  // Imposta la posizione assoluta basata su left/top invece che right/top
  element.style.right = 'auto'
  element.style.left = `${initialLeft}px`
  element.style.top = `${initialTop}px`

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  const element = square.value
  if (!element) return

  // Calcola il delta del movimento
  const deltaX = e.clientX - startX
  const deltaY = e.clientY - startY

  element.style.left = `${initialLeft + deltaX}px`
  element.style.top = `${initialTop + deltaY}px`
}

const stopDrag = () => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}


// ============ STATE ============
const activeTab = ref('Map')
//const tabs = ['Map', 'Advanced Filter', 'Data Distributions']


// Trasformiamo le tab in oggetti per gestire i permessi
const tabs = [
  { name: 'Map', requiresExpert: false },
  { name: 'Advanced Filter', requiresExpert: false },
  { name: 'Data Distributions', requiresExpert: false }
]

const filters = ref({
  profMin: 0,
  tempMin: 0,
  percentile: 0
})

/*
async function eseguiRegistrazione() {
  loginError.value = ''
  authMessage.value = ''
  try {
    // In auth.py, la funzione 'registra' prende i parametri dalla stringa di query
    const queryParams = new URLSearchParams({
      username: loginForm.value.username,
      password: loginForm.value.password
    })

    const res = await fetch(`${API_BASE}/auth/registra?${queryParams}`, {
      method: 'POST'
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Errore durante la registrazione')
    }

    const data = await res.json()
    authMessage.value = data.messaggio // "Utente 'X' creato con ruolo 'base'"
    authMode.value = 'login'           // Riporta automaticamente alla schermata di login
    loginForm.value.password = ''      // Svuota la password per sicurezza

  } catch (e) {
    loginError.value = e.message
  }
}*/

async function eseguiRegistrazione() {
  loginError.value = ''
  authMessage.value = ''
  try {
    const res = await fetch(`${API_BASE}/auth/registra`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: loginForm.value.username,
        password: loginForm.value.password
      })
    })

    if (!res.ok) {
      const err = await res.json()
      // 422: detail è una lista di errori di validazione
      const msg = Array.isArray(err.detail)
        ? err.detail.map(d => d.msg).join(', ')
        : err.detail
      throw new Error(msg || 'Errore durante la registrazione')
    }

    const data = await res.json()
    authMessage.value = data.messaggio
    authMode.value = 'login'
    loginForm.value.password = ''

  } catch (e) {
    loginError.value = e.message
  }
}


async function eseguiLogin() {
  loginError.value = ''
  authMessage.value = ''
  try {
    const params = new URLSearchParams()
    params.append('username', loginForm.value.username)
    params.append('password', loginForm.value.password)

    // L'endpoint in auth.py è /auth/login
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Username o password errati')
    }

    const data = await res.json()
    
    // Salva i dati
    token.value = data.access_token
    userRole.value = data.ruolo
    username.value = loginForm.value.username

    localStorage.setItem('geo_token', token.value)
    localStorage.setItem('geo_role', userRole.value)
    localStorage.setItem('geo_username', username.value)

    showLogin.value = false
    loginForm.value.password = ''

  } catch (e) {
    loginError.value = e.message
  }
}


function eseguiLogout() {
  token.value = null
  userRole.value = 'base'
  username.value = ''
  
  localStorage.removeItem('geo_token')
  localStorage.removeItem('geo_role')
  localStorage.removeItem('geo_username')
  
  if (activeTab.value === 'Advanced Filter') {
    activeTab.value = 'Map'
  }
}

async function onApplicaFiltri(params) {
  console.log('Filtri applicati:', params)
  activeTab.value = 'Map'
  
  try {
    const queryParams = new URLSearchParams()
    
    // Aggiungi TUTTI i parametri dai filtri avanzati
    if (params.fluidi.length > 0) {
      params.fluidi.forEach(f => queryParams.append('tipo_fluido', f))
    }
    if (params.lito.length > 0) {
      params.lito.forEach(l => queryParams.append('termine_lito', l))
    }
    if (params.profMin > 0) {
      queryParams.append('prof_min', params.profMin)
    }
    if (params.profMax < 5000) {
      queryParams.append('prof_max', params.profMax)
    }
    
    // SEMPRE passa il ruolo, anche se è 'tutte'
    queryParams.append('ruolo', params.ruoloLito || 'tutte')  // ← CAMBIA QUI
    
    const url = `${API_BASE}/pozzi/mappa/avanzata?${queryParams}`
    console.log('Fetching:', url)
    
    const response = await fetch(url)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const data = await response.json()
    console.log('Pozzi dal filtro avanzato:', data.length)
    
    pozzi.value = data
    await nextTick()
    renderMarkers()
    
  } catch (error) {
    console.error('Errore:', error.message)
  }
}

const legend = ref({
  densita: true,
  confini: false,
  geologia: false
})

const selectedPozzo = ref(null)
//let map = null
//let markersLayer = L.featureGroup()

let map = null
let markersLayer = L.markerClusterGroup({
  maxClusterRadius: 80,          // Raggio del cluster in px
  disableClusteringAtZoom: 15    // Disabilita clustering a zoom > 15
})  // ← Cambia da L.featureGroup() a L.markerClusterGroup()

const pozzi = ref([])
const API_BASE = 'http://127.0.0.1:8000'

// ============ FETCH DAL BACKEND ============
async function fetchPozzi() {
  try {
    const params = new URLSearchParams()
    
    if (filters.value.profMin > 0) {
      params.append('prof_min', filters.value.profMin)
    }
    if (filters.value.tempMin > 0) {
      params.append('temp_min', filters.value.tempMin)
    }
    
    const url = `${API_BASE}/pozzi/mappa?${params}`
    console.log('Fetching:', url)
    
    const response = await fetch(url)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const data = await response.json()
    console.log('Pozzi ricevuti dal backend:', data.length)
    
    pozzi.value = data
    renderMarkers()
    
  } catch (error) {
    console.error(' Errore fetch:', error.message)
  }
}

// dettaglio pozzo / confronto
const secondoPozzo = ref(null)
const dettaglioSecondoPozzo = ref(null)
const modalitaConfronto = ref(false)

// pannello destro anagrafica
const dettaglioPozzo = ref(null)
const loadingDettaglio = ref(false)

/*
async function fetchDettaglioPozzo(key) {
  // Se c'è già un pozzo selezionato e ne clicco un altro → confronto
  if (dettaglioPozzo.value && dettaglioPozzo.value.anagrafica.key !== key) {
    if (userRole.value !== 'esperto') {
      alert("Il confronto tra pozzi multipli è riservato agli utenti Esperti. Fai l'upgrade per sbloccarlo!");
      return; // BLOCCO
    }
    modalitaConfronto.value = true
    loadingDettaglio.value = true
    try {
      const res = await fetch(`${API_BASE}/pozzi/confronto?key=${dettaglioPozzo.value.anagrafica.key}&key=${key}`)
      const data = await res.json()
      dettaglioPozzo.value = data[0]
      await fetchDisponibilita(key)  // ← aggiungi questa riga
      dettaglioSecondoPozzo.value = data[1]
    } finally {
      loadingDettaglio.value = false
    }
    return
  }

  // Altrimenti carica il dettaglio singolo come prima
  modalitaConfronto.value = false
  dettaglioSecondoPozzo.value = null
  loadingDettaglio.value = true
  try {
    const res = await fetch(`${API_BASE}/pozzi/confronto?key=${key}`)
    const data = await res.json()
    dettaglioPozzo.value = data[0]
  } finally {
    loadingDettaglio.value = false
  }
  async function fetchDisponibilita(key) {
    try {
      const res = await fetch(`${API_BASE}/pozzi/${key}/disponibilita`)
      disponibilitaPozzo.value = await res.json()
    } catch (e) {
      disponibilitaPozzo.value = null
    }
  }
}*/

async function fetchDettaglioPozzo(key) {
  if (dettaglioPozzo.value && dettaglioPozzo.value.anagrafica.key !== key) {
    if (userRole.value !== 'esperto') {
      alert("Il confronto tra pozzi multipli è riservato agli utenti Esperti. Fai l'upgrade per sbloccarlo!");
      return;
    }
    modalitaConfronto.value = true
    loadingDettaglio.value = true
    try {
      const res = await fetch(
        `${API_BASE}/pozzi/confronto?key=${dettaglioPozzo.value.anagrafica.key}&key=${key}`,
        { headers: token.value ? { Authorization: `Bearer ${token.value}` } : {} }
      )
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        console.error('Errore confronto:', res.status, err.detail)
        alert(err.detail || 'Errore nel caricamento del confronto')
        modalitaConfronto.value = false
        return
      }
      const data = await res.json()
      dettaglioPozzo.value = data[0]
      dettaglioSecondoPozzo.value = data[1]
    } finally {
      loadingDettaglio.value = false
    }
    return
  }

  // dettaglio singolo — resta libero, nessun token necessario
  modalitaConfronto.value = false
  dettaglioSecondoPozzo.value = null
  loadingDettaglio.value = true
  try {
    const res = await fetch(`${API_BASE}/pozzi/confronto?key=${key}`)
    if (!res.ok) {
      console.error('Errore dettaglio:', res.status)
      dettaglioPozzo.value = null
      return
    }
    const data = await res.json()
    dettaglioPozzo.value = data[0]
  } finally {
    loadingDettaglio.value = false
  }
}

// ============ FUNZIONI MAPPA ============

// temperature
function getTemperatureColor(temp) {
  if (temp === null || temp === undefined) return '#999999'
  if (temp <= 50) return '#1f77b4'
  if (temp <= 100) return '#2ca02c'
  if (temp <= 150) return '#f0a000'
  if (temp <= 200) return '#ff7f0e'
  if (temp > 200) return 'purple'
  return '#d62728'
}

// percentili
function calcolaPercentile(valori, p) {
  if (valori.length === 0) return null
  const sorted = [...valori].sort((a, b) => a - b)
  const idx = (sorted.length - 1) * p / 100
  const lower = Math.floor(idx)
  const upper = lower + 1
  if (upper >= sorted.length) return sorted[sorted.length - 1]
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (idx - lower)
}

// Calcola la temperatura esatta corrispondente al percentile selezionato
const temperaturaPercentile = computed(() => {
  if (filters.value.percentile === 0) return 0
  
  const temperatureValide = pozzi.value
    .filter(p => p.temp_max !== null && p.temp_max !== undefined)
    .map(p => p.temp_max)

  if (temperatureValide.length === 0) return 0
  
  const soglia = calcolaPercentile(temperatureValide, filters.value.percentile)
  return soglia !== null ? Math.round(soglia) : 0
})

function initMap() {
  if (map) map.remove()
  
  map = L.map('map').setView([41.87, 12.56], 6)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map)

  markersLayer.addTo(map)
}

function renderMarkers() {
  markersLayer.clearLayers()

  // Calcola la soglia percentile sulle temperature disponibili
  const temperatureValide = pozzi.value
    .filter(p => p.temp_max !== null && p.temp_max !== undefined)
    .map(p => p.temp_max)

  const sogliaPercentile = filters.value.percentile > 0
    ? calcolaPercentile(temperatureValide, filters.value.percentile)
    : null

  console.log('Soglia percentile', filters.value.percentile + '%:', sogliaPercentile)

  // Filtra i pozzi in base al percentile (se attivo)
  const pozziFiltrati = pozzi.value.filter(pozzo => {
    if (sogliaPercentile === null) return true // percentile disattivato
    if (pozzo.temp_max === null || pozzo.temp_max === undefined) return false
    return pozzo.temp_max >= sogliaPercentile
  })

  console.log(' Rendering', pozziFiltrati.length, 'pozzi sulla mappa (su', pozzi.value.length, 'totali)')

  pozziFiltrati.forEach(pozzo => {
    if (!pozzo.lat || !pozzo.lon) return

    const color = getTemperatureColor(pozzo.temp_max)

    const marker = L.circleMarker([pozzo.lat, pozzo.lon], {
      radius: 8,
      fillColor: color,
      color: '#333',
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.8
    })

    marker.bindPopup(`
      <div style="min-width:180px;">
        <div style="font-size:13px;font-weight:700;">${pozzo.nome}</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">Caricamento...</div>
      </div>
    `)

    marker.on('click', () => {
      selectedPozzo.value = pozzo
      fetchDettaglioPozzo(pozzo.key)
    })

    markersLayer.addLayer(marker)
    marker.on('popupopen', async () => {
      try {
        const res = await fetch(`${API_BASE}/pozzi/${pozzo.key}/disponibilita`)
        const disp = await res.json()


        const righe = Object.entries(disp)
        .map(([campo, disponibile]) => {
          const colore = disponibile ? '#2e7d32' : '#ccc'
          const etichetta = campo
            .replace(/_/g, ' ')
            .split(' ')
            .map(w => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ')
          
          return `<div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
            <span style="font-size:12px;color:${colore};">${etichetta}</span>
            <span style="margin-left:auto;font-size:11px;color:${colore};">${disponibile ? '✓' : '—'}</span>
          </div>`
        }).join('')

        marker.getPopup().setContent(`
          <div style="min-width:180px;">
            <div style="font-size:13px;font-weight:700;margin-bottom:6px;border-bottom:1px solid #eee;padding-bottom:4px;">
              ${pozzo.nome}
            </div>
            <div style="font-size:11px;color:#666;margin-bottom:8px;">
              Prof: ${pozzo.profondita || 'N/D'}m &nbsp;|&nbsp; 
              T max: ${pozzo.temp_max || 'N/D'}°C
            </div>
            <div style="font-size:10px;font-weight:700;color:#999;margin-bottom:4px;text-transform:uppercase;">
              Dati disponibili
            </div>
            ${righe}
          </div>
        `)
      } catch (e) {
        console.error('Errore disponibilità:', e)
      }
    })

  })

  console.log('Marcatori sulla mappa:', markersLayer.getLayers().length)
}

// ============ LIFECYCLE ============

// Controlla se c'è già un token salvato all'avvio
onMounted(() => {
  const savedToken = localStorage.getItem('geo_token')
  const savedRole = localStorage.getItem('geo_role')
  const savedUser = localStorage.getItem('geo_username')
  
  if (savedToken && savedRole) {
    token.value = savedToken
    userRole.value = savedRole
    username.value = savedUser
  }
  
  initMap()
  fetchPozzi()
})

// ============ WATCHERS ============

watch(() => [filters.value.profMin, filters.value.tempMin], () => {
  fetchPozzi()  // Solo questi due ricaricano dal backend
})

watch(() => filters.value.percentile, () => {
  renderMarkers()  // Il percentile filtra client-side, non serve richiamare il backend
})

watch(activeTab, async (nuovaTab) => {
  if (nuovaTab === 'Map') {
    await nextTick()
    initMap()
    renderMarkers()
  }
})

// Se l'utente torna "base" mentre è in una tab da esperto, riportalo alla mappa
/*watch(userRole, (newRole) => {
  if (newRole === 'base' && activeTab.value === 'Advanced Filter') {
    activeTab.value = 'Map'
  }
})*/
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #e8dcc8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  color: #333;
}

/* ========== HEADER ========== */
.header {
  background: linear-gradient(135deg, #7d6b5a 0%, #5d4e40 100%);
  color: white;
  padding: 15px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 1px;
}

.header-content .subtitle {
  margin: 5px 0 0 0;
  font-size: 15px;
  opacity: 0.85;
  font-weight: 400;
}

/* ========== TABS ========== */
.tabs-container {
  display: flex;
  background: #d4c5b0;
  border-bottom: 1px solid #b8a791;
  padding-left: 20px;
  gap: 0;
}

.tab {
  background: none;
  border: none;
  padding: 12px 20px;
  cursor: pointer;
  font-size: 20px;
  color: #666;
  border-bottom: 3px solid transparent;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.2s ease;
  font-weight: 500;
}

.tab:hover {
  background: rgba(255, 255, 255, 0.3);
  color: #333;
}

.tab.active {
  color: #333;
  border-bottom-color: #7d6b5a;
  background: rgba(255, 255, 255, 0.5);
}

.tab-icon {
  font-size: 14px;
}

/* ========== CONTENT WRAPPER ========== */
.content-wrapper {
  display: flex;
  flex: 1;
  gap: 0;
  overflow: hidden;
}

/* ========== FILTERS PANEL (SINISTRA) ========== */
.filters-panel {
  width: 220px;
  background: #d4c5b0;
  border-right: 1px solid #b8a791;
  padding: 15px;
  overflow-y: auto;
}

.filter-section h3 {
  font-size: 15px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 15px 0;
  color: #555;
}

.filter-item {
  margin-bottom: 20px;
}

.filter-item label {
  display: block;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #555;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(to right, #999, #666);
  cursor: pointer;
}

.slider-depth {
  background: linear-gradient(to right, #999, #666);
}

.slider-temp {
  background: linear-gradient(to right, #999, #666);
}

.slider-percentile {
  background: linear-gradient(to right, #999, #666);
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  border: 2px solid #666;
}

.slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  border: 2px solid #666;
}

.slider-value {
  font-size: 11px;
  color: #666;
  min-width: 45px;
  text-align: right;
  font-weight: 500;
}

/* ========== MAP PANEL (CENTRO) ========== */
.map-panel {
  flex: 1;
  position: relative;
  display: flex;
  background: white;
}

.map-container {
  width: 100%;
  height: 100%;
}

/* LEAFLET OVERRIDE */
.map-container :deep(.leaflet-control-zoom) {
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.map-container :deep(.leaflet-control-zoom-in,
.leaflet-control-zoom-out) {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.map-container :deep(.leaflet-popup-content-wrapper) {
  border-radius: 4px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* ========== LEGEND BOX ========== */
.legend-box {
  position: absolute;
  top: 60px;
  right: 15px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  z-index: 400;
  max-width: 180px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.legend-checkbox {
  width: 14px;
  height: 14px;
  cursor: pointer;
  accent-color: #7d6b5a;
}

.legend-item label {
  cursor: pointer;
  font-size: 11px;
  margin: 0;
}

.gradient-legend {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.gradient-legend h4 {
  margin: 0 0 8px 0;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: #555;
}

.gradient-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.gradient-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  border: 1px solid #999;
}

.gradient-label {
  font-size: 10px;
  color: #666;
}

/* ========== DETAILS PANEL (DESTRA) ========== */
.details-panel {
  width: 340px;
  background: #f5f5f5;
  border-left: 1px solid #ddd;
  padding: 15px;
  overflow-y: auto;
}

.pozzo-details h3 {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 10px 0;
  color: #333;
}

.details-grid {
  font-size: 12px;
  line-height: 1.8;
}

.details-grid p {
  margin: 5px 0;
  color: #555;
}

.details-grid strong {
  color: black;
  font-weight: 600;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 12px;
  text-align: center;
  padding: 20px;
}

/* ========== SCROLLBARS ========== */
.filters-panel::-webkit-scrollbar,
.details-panel::-webkit-scrollbar {
  width: 6px;
}

.filters-panel::-webkit-scrollbar-track,
.details-panel::-webkit-scrollbar-track {
  background: #e0d5ca;
}

.filters-panel::-webkit-scrollbar-thumb,
.details-panel::-webkit-scrollbar-thumb {
  background: #b8a791;
  border-radius: 3px;
}

.details-section {
  font-size: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.details-section:last-child {
  border-bottom: none;
}

.details-section h4 {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: #7d6b5a;
  margin: 0 0 8px 0;
}

/* ========== RESPONSIVE ========== */
@media (max-width: 1200px) {
  .filters-panel {
    width: 140px;
    padding: 10px;
  }

  .details-panel {
    width: 280px;
    padding: 10px;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    flex-direction: column;
  }

  .filters-panel,
  .details-panel {
    width: 100%;
    max-height: 25vh;
    border: none;
  }

  .legend-box {
    font-size: 10px;
  }
}

.panel-confronto {
  width: 620px;  /* Si allarga per il confronto affiancato */
  transition: width 0.3s ease;
}

.confronto-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: #f0ebe2;
  border-bottom: 1px solid #ddd;
  font-size: 13px;
  font-weight: 600;
  color: black;
}

.btn-reset-confronto {
  background: none;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 3px 10px;
  cursor: pointer;
  font-size: 11px;
  color: #666;
}

.btn-reset-confronto:hover { background: #f5f5f5; }

.did{
  font-size: 12px;
}

/* Stile per il selettore di ruolo in alto a destra */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-role-selector {
  background: rgba(255, 255, 255, 0.15);
  padding: 8px 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.user-role-selector select {
  background: white;
  border: none;
  padding: 5px 8px;
  border-radius: 4px;
  font-weight: 600;
  color: #3d3020;
  cursor: pointer;
}

/* Stili per le tab bloccate */
.tab.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: transparent !important;
}

.tab.disabled:hover {
  background: transparent !important;
  color: #666 !important;
}

.lock-icon {
  font-size: 14px;
  margin-left: 6px;
  opacity: 0.8;
}

.auth-section { position: relative; }
.btn-login, .btn-logout { 
  background: white; color: #5d4e40; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; cursor: pointer; 
}
.user-logged-in { display: flex; align-items: center; gap: 12px; font-size: 13px; }

.login-popup {
  position: absolute; top: 40px; right: 0; background: white; padding: 15px; border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2); width: 220px; z-index: 1000; color: #333;
}
.login-popup h4 { margin: 0 0 10px 0; font-size: 14px; color: #5d4e40; }
.login-popup input { 
  width: 100%; margin-bottom: 8px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; 
}
.login-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 5px; }
.btn-cancel { background: #eee; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
.btn-confirm { background: #5d4e40; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
.error-msg { color: #d62728; font-size: 11px; margin: 0 0 8px 0; }
</style>