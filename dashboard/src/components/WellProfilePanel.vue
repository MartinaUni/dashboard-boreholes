<template>
  <div class="well-profile-panel">

    <!-- HEADER -->
    <div class="wpp-header"  v-if="showHeader">
      <div class="header-left">
        <button class="btn-close" @click="$emit('close')">✕</button>
        <span class="header-title">
          {{ pozzi.length === 1 ? 'Profilo Pozzo' : 'Confronto Pozzi' }}
        </span>
      </div>
      <label class="toggle-strati">
        <input type="checkbox" v-model="mostraLitologia">
        <span class="toggle-slider"></span>
        Stratigrafia
      </label>
    </div>

    <!-- KPI CARDS -->
    <div class="kpi-row">
      <div
        v-for="(p, i) in pozzi"
        :key="p.anagrafica.key"
        class="kpi-card"
        
      >
        <div class="kpi-nome">
          
          {{ p.anagrafica.nome }}
        </div>
        <div class="kpi-grid">
          <div class="kpi-item">
            <span class="kpi-label">Profondità</span>
            <span class="kpi-value">{{ p.anagrafica.prof ?? 'N/D' }} m</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">T max</span>
            <span class="kpi-value">{{ p.kpi.temp_max ?? 'N/D' }} °C</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">Grad. medio</span>
            <span class="kpi-value">{{ p.kpi.grad_medio ?? 'N/D' }} °C/km</span>
          </div>
        </div>
      </div>
    </div>

    <!-- PROFILI AFFIANCATI -->
    <div class="profiles-row">
      <div
        v-for="(p, i) in pozzi"
        :key="p.anagrafica.key"
        class="profile-col"
      >
        <!-- Nome pozzo -->
        <div class="profile-label" >
          
          {{ p.anagrafica.nome }} — {{ p.anagrafica.key }}
        </div>

        <!-- SVG PROFILO -->
        <div class="profile-svg-wrapper">
          <svg
            :width="svgW"
            :height="svgH"
            :viewBox="`0 0 ${svgW} ${svgH}`"
            
          >
            <!-- Asse X (temperatura) -->
            <line :x1="marginL" :y1="marginT" :x2="marginL" :y2="svgH - marginB" stroke="black" stroke-width="1"/>
            <line :x1="marginL" :y1="svgH - marginB" :x2="svgW - marginR" :y2="svgH - marginB" stroke="black" stroke-width="1"/>

            <!-- Griglie X -->
            <g v-for="t in [0, 50, 100, 150, 200, 250]" :key="'xt' + t">
              <line
                :x1="scaleX(t, i)" :y1="marginT"
                :x2="scaleX(t, i)" :y2="svgH - marginB"
                stroke="#eee" stroke-width="1" stroke-dasharray="3,3"
              />
              <text
                :x="scaleX(t, i)" :y="svgH - marginB + 14"
                text-anchor="middle" font-size="9" fill="#black"
              >{{ t }}</text>
            </g>

            <!-- Griglie Y (profondità) -->
            <g v-for="d in depthTicks" :key="'yd' + d">
              <line
                :x1="marginL" :y1="scaleY(d)"
                :x2="svgW - marginR" :y2="scaleY(d)"
                stroke="#eee" stroke-width="1" stroke-dasharray="3,3"
              />
              <text
                :x="marginL - 5" :y="scaleY(d) + 4"
                text-anchor="end" font-size="9" fill="black"
              >{{ d }}</text>
            </g>

            <!-- COLONNA LITOLOGIA -->
            <!-- COLONNA LITOLOGIA -->
            <g v-if="mostraLitologia">
              <rect
                v-for="(gruppo, li) in getGroupedLitologie(p)"
                :key="li"
                :x="2"
                :y="scaleY(gruppo.da)"
                :width="litoW - 2"
                :height="Math.max(scaleY(gruppo.a) - scaleY(gruppo.da), 2)"
                :fill="getLitoColor(gruppo.primaria)"
                :opacity="0.85"
              >
                <!-- Tooltip multiriga -->
                <title>{{ buildTooltip(gruppo) }}</title>
              </rect>
            </g>

            <!-- Linea Fine Pozzo -->
            <g v-if="p.anagrafica.prof">
              <line
                :x1="marginL" :y1="scaleY(p.anagrafica.prof)"
                :x2="svgW - marginR" :y2="scaleY(p.anagrafica.prof)"
                stroke="#999" stroke-width="1.5" stroke-dasharray="6,3"
              />
              <rect
                :x="svgW - marginR - 80" :y="scaleY(p.anagrafica.prof) - 16"
                width="80" height="16" rx="3"
                :fill="COLORI_POZZO[i]"
              />
              <text
                :x="svgW - marginR - 40" :y="scaleY(p.anagrafica.prof) - 5"
                text-anchor="middle" font-size="9" fill="white" font-weight="600"
              >Fine pozzo: {{ p.anagrafica.prof }} m</text>
            </g>

            <!-- CURVA TEMPERATURA -->
            <polyline
              v-if="p.temperatura_vs_profondita.length > 1"
              :points="buildPolyline(p.temperatura_vs_profondita, i)"
              :stroke="COLORI_POZZO[i]"
              stroke-width="2.5"
              fill="none"
              stroke-linejoin="round"
              stroke-linecap="round"
            />

            <!-- Punti temperatura -->
            <circle
              v-for="(t, ti) in p.temperatura_vs_profondita"
              :key="ti"
              :cx="scaleX(t.temp, i)"
              :cy="scaleY(t.prof)"
              r="4"
              :fill="COLORI_POZZO[i]"
              stroke="white"
              stroke-width="1.5"
            >
              <title>{{ t.temp }}°C @ {{ t.prof }}m</title>
            </circle>

            <!-- Label asse X -->
            <text
              :x="marginL + (svgW - marginL - marginR) / 2"
              :y="svgH - 2"
              text-anchor="middle" font-size="10" fill="#999" 
            >T (°C)</text>

          </svg>
        </div>
      </div>
    </div>

    <!-- LEGENDA -->
    <div class="legend-row">
      <div class="legend-curves">
        <span v-for="(p, i) in pozzi" :key="i" class="legend-item">
          <svg width="24" height="10">
            <line x1="0" y1="5" x2="24" y2="5" :stroke="COLORI_POZZO[i]" stroke-width="2.5"/>
          </svg>
          {{ p.anagrafica.nome }} ({{ p.anagrafica.key }})
        </span>
        <!--<span class="legend-item" v-if="mostraLitologia">
          <svg width="14" height="10">
            <rect x="0" y="0" width="14" height="10" fill="#c4a572"/>
          </svg>
          Litologia
        </span>-->
        <span class="legend-note">Stessa scala T e profondità per entrambi i profili</span>
      </div>

      <!-- Legenda litologia colori -->
      <!--<div class="lito-legend" v-if="mostraLitologia">
        <span v-for="(color, nome) in LITO_COLORS" :key="nome" class="lito-legend-item">
          
          {{ nome }}
        </span>
      </div>-->
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'


const props = defineProps({
  pozzi: { type: Array, required: true },
  showHeader: { type: Boolean, default: true }
})

defineEmits(['close'])

// ============ STATE ============
const mostraLitologia = ref(true)

// ============ COLORI POZZI ============
const COLORI_POZZO = ['#2196f3', '#ff8c00', '#4caf50', '#9c27b0']

// ============ COLORI LITOLOGIA ============
const LITO_COLORS = {
  'ARGILLA':    '#9e9e9e',
  'SABBIA':     '#fdd835',
  'ARENARIA':   '#ffb74d',
  'SILT':       '#a5d6a7',
  'CALCARE':    '#81d4fa',
  'DOLOMIA':    '#4fc3f7',
  'MARNA':      '#80cbc4',
  'MUDSTONE':   '#607d8b',
  'WACKESTONE': '#4db6ac',
  'PACKSTONE':  '#26a69a',
  'GRAINSTONE': '#00897b',
  'ANIDRITE':   '#f48fb1',
  'GESSO':      '#f8bbd9',
  'SALGEMMA':   '#e1bee7',
  'ALLUVIONE':  '#a1887f',
  'BASALTO':    '#424242',
  'TUFO':       '#795548',
  'DEFAULT':    '#bdbdbd',
}

// Mostra tutti i colori come swatches
Object.entries(LITO_COLORS).forEach(([nome, colore]) => {
  console.log(`%c ${nome} `, `background: ${colore}; color: white; padding: 2px 6px;`)
})

function getLitoColor(litologia) {
  if (!litologia) return LITO_COLORS['DEFAULT']
  const upper = litologia.toUpperCase()
  for (const [nome, color] of Object.entries(LITO_COLORS)) {
    if (upper.includes(nome)) return color
  }
  return LITO_COLORS['DEFAULT']
}

// litologia standard
// Usa litologia_standard se disponibile, altrimenti fallback alla grezza
const getLitologie = (p) => {
  return p.litologia_standard?.length 
    ? p.litologia_standard 
    : p.litologia
}

// Raggruppa primaria e subordinate per intervallo di profondità
/*function getGroupedLitologie(p) {
  const rawLito = p.litologia_standard?.length ? p.litologia_standard : p.litologia;
  if (!rawLito || !rawLito.length) return [];

  const map = new Map();
  rawLito.forEach(l => {
    const da = l.da ?? l.daprof;
    const a = l.a ?? l.aprof;
    const litoName = l.litologia || l.litologia_standard || l.litologiastandard;
    const key = `${da}-${a}`; // Chiave univoca per profondità

    if (!map.has(key)) {
      map.set(key, { da, a, primaria: null, subordinate: [] });
    }
    
    const group = map.get(key);
    // Normalizza il ruolo in minuscolo per evitare errori di case-sensitivity
    const ruolo = (l.ruolo || '').toLowerCase();

    // Se è esplicitamente subordinata, o se ha una relazione sintattica compilata
    if (ruolo === 'subordinata' || l.relazione) {
      group.subordinate.push({ nome: litoName, relazione: l.relazione });
    } else {
      // Evitiamo di sovrascrivere se ci sono più primarie (anomalia dato)
      if (group.primaria) {
        group.primaria += ` + ${litoName}`;
      } else {
        group.primaria = litoName;
      }
    }
  });

  return Array.from(map.values());
}
  */

// Raggruppa primaria e subordinate per intervallo di profondità
function getGroupedLitologie(p) {
  const rawLito = p.litologia_standard?.length ? p.litologia_standard : p.litologia;
  if (!rawLito || !rawLito.length) return [];

  const map = new Map();
  rawLito.forEach(l => {
    const da = l.da ?? l.daprof;
    const a = l.a ?? l.aprof;
    const litoName = l.litologia_standard || l.litologiastandard || l.litologia;
    const key = `${da}-${a}`; 

    if (!map.has(key)) {
      // 1. Cerchiamo la vera descrizione originale nell'array p.litologia 
      //    basandoci sull'intervallo di profondità
      let testoOriginale = "N/D";
      if (p.litologia && p.litologia.length) {
        const originaliMatch = p.litologia.filter(
          orig => (orig.da ?? orig.daprof) === da && (orig.a ?? orig.aprof) === a
        );
        if (originaliMatch.length > 0) {
          // Uniamo i testi in caso ci siano più record per la stessa profondità
          testoOriginale = originaliMatch.map(o => o.litologia).join('; ');
        }
      }

      map.set(key, { 
        da, 
        a, 
        primaria: null, 
        subordinate: [],
        descrizioneOriginale: testoOriginale // Salviamo il testo grezzo qui
      });
    }
    
    const group = map.get(key);
    const ruolo = (l.ruolo || '').toLowerCase();

    if (ruolo === 'subordinata' || l.relazione) {
      group.subordinate.push({ nome: litoName, relazione: l.relazione });
    } else {
      if (group.primaria) {
        group.primaria += ` + ${litoName}`;
      } else {
        group.primaria = litoName;
      }
    }
  });

  return Array.from(map.values());
}
// Costruisce il testo mostrato al mouse hover
/*function buildTooltip(gruppo) {
  // Usa \r\n per forzare il ritorno a capo nei tooltip nativi dei browser
  let text = `Prof: ${gruppo.da}–${gruppo.a} m\r\n`;
  text += `Primaria: ${gruppo.primaria || 'N/D'}`;
  
  if (gruppo.subordinate && gruppo.subordinate.length > 0) {
    const subs = gruppo.subordinate.map(s => 
      s.relazione ? `${s.relazione} di ${s.nome}` : s.nome
    );
    text += `\r\nSubordinate: ${subs.join(', ')}`;
  }
  return text;
}
*/
// Costruisce il testo mostrato al mouse hover
// Costruisce il testo mostrato al mouse hover
function buildTooltip(gruppo) {
  let text = `Prof: ${gruppo.da}–${gruppo.a} m\r\n`;
  text += `Standard: ${gruppo.primaria || 'N/D'}`;
  
  if (gruppo.subordinate && gruppo.subordinate.length > 0) {
    const subs = gruppo.subordinate.map(s => 
      s.relazione ? `${s.relazione} di ${s.nome}` : s.nome
    );
    text += `\r\nSubordinate: ${subs.join(', ')}`;
  }
  
  // Aggiungiamo in fondo l'esatta descrizione originale grezza
  if (gruppo.descrizioneOriginale && gruppo.descrizioneOriginale !== "N/D") {
    text += `\r\n\r\nOriginale:\r\n${gruppo.descrizioneOriginale}`;
  }
  
  return text;
}
// ============ SCALA SVG ============
const svgW   = 260
const svgH   = 480
const marginT = 15
const marginB = 30
const marginR = 20
const litoW  = 28

const marginL = computed(() => mostraLitologia.value ? litoW + 35 : 35)

// Profondità massima (stessa scala per tutti i pozzi)
const maxProf = computed(() => {
  const max = Math.max(...props.pozzi.map(p => p.anagrafica.prof || 0))
  return Math.ceil(max / 500) * 500 || 5000
})

// Temperatura massima (stessa scala)
const maxTemp = computed(() => {
  const allTemps = props.pozzi.flatMap(p => p.temperatura_vs_profondita.map(t => t.temp))
  const max = Math.max(...allTemps, 50)
  return Math.ceil(max / 50) * 50
})

const depthTicks = computed(() => {
  const step = maxProf.value <= 2000 ? 500 : 1000
  const ticks = []
  for (let d = 0; d <= maxProf.value; d += step) ticks.push(d)
  return ticks
})

function scaleY(prof) {
  return marginT + (prof / maxProf.value) * (svgH - marginT - marginB)
}

function scaleX(temp, idx) {
  const ml = marginL.value
  return ml + (temp / maxTemp.value) * (svgW - ml - marginR)
}

function buildPolyline(punti, idx) {
  return punti
    .filter(p => p.temp !== null && p.prof !== null)
    .map(p => `${scaleX(p.temp, idx)},${scaleY(p.prof)}`)
    .join(' ')
}
</script>

<style scoped>
.well-profile-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  overflow-y: auto;
  font-size: 12px;
}

/* ====== HEADER ====== */
.wpp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #eee;
  background: #fafafa;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-close {
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 2px 7px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
}

.btn-close:hover { background: #f5f5f5; }

.header-title {
  font-size: 13px;
  font-weight: 700;
  color: #333;
}

/* Toggle stratigrafia */
.toggle-strati {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #666;
  cursor: pointer;
}

.toggle-strati input { display: none; }

.toggle-slider {
  width: 32px;
  height: 16px;
  background: #ccc;
  border-radius: 8px;
  position: relative;
  transition: background 0.2s;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  left: 2px;
  top: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  transition: left 0.2s;
}

.toggle-strati input:checked + .toggle-slider { background: #4caf50; }
.toggle-strati input:checked + .toggle-slider::after { left: 18px; }

/* ====== KPI ====== */
.kpi-row {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.kpi-card {
  flex: 1;
  border: 1px solid #eee;
  border-top: 3px solid;
  border-radius: 6px;
  padding: 8px 10px;
  background: #fafafa;
}

.kpi-nome {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #333;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.kpi-grid {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.kpi-item {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}

.kpi-label {
  font-size: 10px;
  color: #999;
}

.kpi-value {
  font-size: 10px;
  font-weight: 600;
  color: #444;
}

/* ====== PROFILI ====== */
.profiles-row {
  display: flex;
  gap: 0;
  flex: 1;
  min-height: 0;
  overflow-x: auto;
  padding: 10px 8px;
}

.profile-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 260px;
}

.profile-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
  border: 1.5px solid;
  margin-bottom: 8px;
  white-space: nowrap;
}

.profile-svg-wrapper {
  width: 100%;
  overflow: visible;
}

/* ====== LEGENDA ====== */
.legend-row {
  padding: 8px 14px;
  border-top: 1px solid #eee;
  flex-shrink: 0;
  background: #fafafa;
}

.legend-curves {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: #555;
}

.legend-note {
  font-size: 9px;
  color: #aaa;
  font-style: italic;
  margin-left: 4px;
}

.lito-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.lito-legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 9px;
  color: #666;
}

.lito-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  border: 1px solid rgba(0,0,0,0.1);
}

/* ====== SCROLLBAR ====== */
.well-profile-panel::-webkit-scrollbar { width: 4px; }
.well-profile-panel::-webkit-scrollbar-track { background: #f5f5f5; }
.well-profile-panel::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
</style>