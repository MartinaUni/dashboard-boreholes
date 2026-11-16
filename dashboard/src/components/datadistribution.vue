<template>
  <div class="dashboard">
    <header class="header">
      <div class="header-content"></div>
    </header>

    <div class="tabs-container">
      <button
        v-for="tab in tabs"
        :key="tab"
        :class="['tab', { active: activeTab === tab }]"
        @click="activeTab = tab"
      >
        {{ tab }}
      </button>
    </div>
  </div>

  <div class="distributions-wrapper">
    <div class="page-heading">
      <div>
        <h2 class="page-title">Distribuzione dei dati</h2>
        <p class="page-subtitle">
          Panoramica delle principali caratteristiche dei pozzi
        </p>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>Caricamento dati...</p>
    </div>

    <div class="dashboard-grid">
      <!-- MAPPA -->
      <section class="chart-card map-card">
        <div class="card-heading">
          <div>
            <span class="card-kicker">Distribuzione spaziale</span>
            <h3 class="chart-title">Pozzi per Regione / Provincia</h3>
          </div>
        </div>
        <div class="chart-wrapper map-wrapper">
          <div ref="regioneMapDiv" class="map-container"></div>
        </div>
      </section>

      <!-- SCOPO -->
      <section class="chart-card">
        <div class="card-heading">
          <div>
            <span class="card-kicker">Composizione</span>
            <h3 class="chart-title">Pozzi per Scopo</h3>
          </div>
        </div>
        <div class="chart-wrapper">
          <canvas ref="scopoChart"></canvas>
        </div>
      </section>

      <!-- USO -->
      <section class="chart-card wide-card">
        <div class="card-heading">
          <div>
            <span class="card-kicker">Composizione</span>
            <h3 class="chart-title">Pozzi per Uso</h3>
          </div>
        </div>
        <div class="chart-wrapper lollipop-wrapper">
          <canvas ref="usoChart"></canvas>
        </div>
      </section>

      <!-- LITOLOGIA -->
      <section class="chart-card wide-card lito-card">
        <div class="card-heading">
          <div>
            <span class="card-kicker">Composizione geologica</span>
            <h3 class="chart-title">Tipi Litologici dei Pozzi</h3>
          </div>
          <div class="card-note">Tutte le categorie</div>
        </div>

        <div class="lito-layout">
          <div class="donut-container">
            <canvas ref="litoChart"></canvas>
            
          </div>

          <div class="lito-legend">
            <div
              v-for="item in litoLegend"
              :key="item.name"
              class="lito-row"
            >
              <span
                class="lito-dot"
                :style="{ backgroundColor: item.color }"
              ></span>
              <span class="lito-name" :title="item.name">{{ item.name }}</span>
              <span class="lito-percent">{{ item.percent }}%</span>
              <span class="lito-count">{{ item.count }}</span>
            </div>
            
          </div>
           <div >
              <strong>{{ litoTotal }}</strong>
              <span> pozzi</span>
            </div>
        </div>
       
      </section>

      <!-- PROFONDITA -->
      <section class="chart-card wide-card">
        <div class="card-heading">
          <div>
            <span class="card-kicker">Distribuzione numerica</span>
            <h3 class="chart-title">Distribuzione delle Profondità</h3>
          </div>
          <div class="card-note">Frequenza relativa</div>
        </div>
        <div class="chart-wrapper depth-wrapper">
          <canvas ref="profChart"></canvas>
        </div>
      </section>

      <!-- BOXPLOT -->
      <section class="chart-card wide-card">
        <div class="card-heading">
          <div>
            <span class="card-kicker">Relazione tra variabili</span>
            <h3 class="chart-title">Temperature per Profondità</h3>
          </div>
        </div>
        <div class="chart-wrapper boxplot-wrapper">
          <svg ref="boxplotSvg"></svg>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  DoughnutController,
  ArcElement,
  LineController,
  Tooltip,
  Legend,
  Title,
  PointElement,
  LineElement
} from 'chart.js'

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  DoughnutController,
  ArcElement,
  LineController,
  Tooltip,
  Legend,
  Title,
  PointElement,
  LineElement
)

const regioneChart = ref(null)
const regioneMapDiv = ref(null)
const scopoChart = ref(null)
const usoChart = ref(null)
const profChart = ref(null)
const boxplotSvg = ref(null)
const litoChart = ref(null)
const loading = ref(true)

const litoTotal = ref(0)
const litoLegend = ref([])

const API_BASE = 'http://127.0.0.1:8000'

const COLORS = [
  '#4fc3f7', '#81c784', '#ffb74d', '#e57373',
  '#ba68c8', '#4db6ac', '#fff176', '#f06292',
  '#a1887f', '#90a4ae', '#7986cb', '#4dd0e1',
  '#aed581', '#ff8a65', '#ce93d8', '#80cbc4',
  '#dce775', '#ffb300', '#90caf9', '#ef9a9a'
]

async function fetchDistribuzione(campo) {
  const res = await fetch(`${API_BASE}/pozzi/distribuzione?campo=${campo}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchBoxplot(campo) {
  const res = await fetch(`${API_BASE}/pozzi/distribuzione?campo=${campo}&modalita=boxplot`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

function percentValues(data) {
  const total = data.reduce((sum, d) => sum + Number(d.conteggio || 0), 0)
  return {
    total,
    values: data.map(d => total ? (Number(d.conteggio || 0) / total) * 100 : 0)
  }
}

function baseChartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 500 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#101b25',
        titleColor: '#fff',
        bodyColor: '#d9e2e8',
        borderColor: 'rgba(255,255,255,0.12)',
        borderWidth: 1,
        padding: 10
      }
    },
    scales: {
      x: {
        ticks: { color: '#aeb9c2', font: { size: 10 } },
        grid: { color: 'rgba(255,255,255,0.05)' }
      },
      y: {
        ticks: { color: '#aeb9c2', font: { size: 10 } },
        grid: { color: 'rgba(255,255,255,0.07)' }
      }
    }
  }
}

// ------ REGIONE ------
async function initRegione() {
  const dati = await fetchDistribuzione('regione')

  const codiceToNome = {
    1: 'PIEMONTE', 2: "VALLE D'AOSTA", 3: 'LOMBARDIA',
    4: 'TRENTINO-ALTO ADIGE', 5: 'VENETO', 6: 'FRIULI-VENEZIA GIULIA',
    7: 'LIGURIA', 8: 'EMILIA-ROMAGNA', 9: 'TOSCANA',
    10: 'UMBRIA', 11: 'MARCHE', 12: 'LAZIO',
    13: 'ABRUZZO', 14: 'MOLISE', 15: 'CAMPANIA',
    16: 'PUGLIA', 17: 'BASILICATA', 18: 'CALABRIA',
    19: 'SICILIA', 20: 'SARDEGNA'
  }

  const conteggioMap = {}
  dati.forEach(d => {
    const codice = Number(d.gruppo)
    const nome = codiceToNome[codice]
    if (nome) conteggioMap[nome] = Number(d.conteggio || 0)
  })

  const geoRes = await fetch(
    'https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson'
  )
  const geoJson = await geoRes.json()

  function getColor(count) {
    if (!count) return '#b2ebf2'
    const max = Math.max(...Object.values(conteggioMap), 1)
    const ratio = count / max

    if (ratio < 0.2) return '#80eef5' // Chiaro per frequenza bassa
    if (ratio < 0.4) return '#4dd8e8'
    if (ratio < 0.6) return '#20bcd4'
    if (ratio < 0.8) return '#1a9ab0'
    return '#1a6a8a'                  // Scuro per frequenza alta
  }

  function style(feature) {
    const nome = feature.properties.reg_name?.trim().toUpperCase() || ''
    return {
      fillColor: getColor(conteggioMap[nome] || 0),
      weight: 1,
      opacity: 0.8,
      color: '#0a2030',
      fillOpacity: 0.85
    }
  }

  function onEachFeature(feature, layer) {
    const nome = feature.properties.reg_name || 'N/D'
    const count = conteggioMap[nome.trim().toUpperCase()] || 0
    layer.bindTooltip(
      `<strong>${nome}</strong><br>${count} pozzi`,
      { sticky: true }
    )
  }

  await nextTick()

  const mapInstance = L.map(regioneMapDiv.value, {
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false
  }).setView([42.5, 12.5], 5)

  L.geoJSON(geoJson, { style, onEachFeature }).addTo(mapInstance)

  await nextTick()
  mapInstance.invalidateSize()

  const observer = new ResizeObserver(() => mapInstance.invalidateSize())
  observer.observe(regioneMapDiv.value)

  setTimeout(() => mapInstance.invalidateSize(), 300)

  const legend = L.control({ position: 'bottomleft' })

  legend.onAdd = () => {
    const div = L.DomUtil.create('div')

    div.style.cssText = `
      background: rgba(10, 25, 35, 0.94);
      padding: 10px 12px;
      border-radius: 8px;
      color: #fff;
      font-size: 10px;
      line-height: 18px;
      box-shadow: 0 3px 12px rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.15);
    `

    div.innerHTML = `
      <div style="
        font-weight:700;
        font-size:11px;
        margin-bottom:6px;
        color:#fff;
      ">
        frequenza pozzi
      </div>

      <div style="display:flex;align-items:center;gap:7px;">
        <span style="width:13px;height:13px;background:#b2ebf2;border-radius:3px;"></span>
        <span>0</span>
      </div>

      <div style="display:flex;align-items:center;gap:7px;">
        <span style="width:13px;height:13px;background:#80eef5;border-radius:3px;"></span>
        <span>Bassa</span>
      </div>

      <div style="display:flex;align-items:center;gap:7px;">
        <span style="width:13px;height:13px;background:#4dd8e8;border-radius:3px;"></span>
        <span>Medio-bassa</span>
      </div>

      <div style="display:flex;align-items:center;gap:7px;">
        <span style="width:13px;height:13px;background:#20bcd4;border-radius:3px;"></span>
        <span>Media</span>
      </div>

      <div style="display:flex;align-items:center;gap:7px;">
        <span style="width:13px;height:13px;background:#1a9ab0;border-radius:3px;"></span>
        <span>Medio-alta</span>
      </div>

      <div style="display:flex;align-items:center;gap:7px;">
        <span style="width:13px;height:13px;background:#1a6a8a;border-radius:3px;"></span>
        <span>Alta</span>
      </div>
    `

    return div
  }

  legend.addTo(mapInstance)

}
// ------ SCOPO ------
async function initScopo() {
  const data = await fetchDistribuzione('scopo')
  const clean = data.filter(d => d.gruppo !== null && d.gruppo !== undefined)

  const { total, values } = percentValues(clean)

  new Chart(scopoChart.value, {
    type: 'bar',
    data: {
      labels: clean.map(d => d.gruppo ?? 'N/D'),
      datasets: [{
        data: values,
        backgroundColor: COLORS.slice(0, clean.length),
        borderRadius: 5,
        borderSkipped: false
      }]
    },
    options: {
      ...baseChartOptions(),
      indexAxis: 'y',
      plugins: {
        ...baseChartOptions().plugins,
        tooltip: {
          ...baseChartOptions().plugins.tooltip,
          callbacks: {
            label: ctx => {
              const d = clean[ctx.dataIndex]
              return ` ${Number(d.conteggio).toLocaleString('it-IT')} pozzi · ${ctx.parsed.x.toFixed(1)}%`
            }
          }
        }
      },
      scales: {
        x: {
          min: 0,
          max: 100,
          ticks: {
            color: '#aeb9c2',
            callback: value => `${value}%`,
            font: { size: 10 }
          },
          grid: { color: 'rgba(255,255,255,0.06)' }
        },
        y: {
          ticks: { color: '#d2dbe1', font: { size: 10 } },
          grid: { display: false }
        }
      }
    }
  })
}

// ------ USO: LOLLIPOP ------
async function initUso() {
  const data = await fetchDistribuzione('uso')
  const clean = data
    .filter(d => 
      d.gruppo !== null && 
      d.gruppo !== undefined && 
      d.gruppo.toUpperCase() !== 'NON INDICATO' // Esclude i non indicati
    )
    .sort((a, b) => Number(b.conteggio || 0) - Number(a.conteggio || 0))
  const { values } = percentValues(clean)
  
  new Chart(usoChart.value, {
    type: 'bar', // Imposta il tipo base su bar per far funzionare correttamente l'asse
    data: {
      labels: clean.map(d => d.gruppo ?? 'N/D'),
      datasets: [
        {
          // 1. IL PUNTO IN CIMA (Pallino)
          type: 'line',
          data: values,
          showLine: false, // CRUCIALE: nasconde la linea orizzontale che unisce i punti
          pointRadius: 6,
          pointHoverRadius: 8,
          pointBackgroundColor: COLORS[0],
          pointBorderColor: '#10202d',
          pointBorderWidth: 2,
          order: 1 // Assicura che i punti vengano disegnati sopra le linee verticali
        },
        {
          // 2. LA LINEA VERTICALE (Barra sottile)
          type: 'bar',
          data: values,
          backgroundColor: 'rgba(79,195,247,0.5)', // Colore della linea verticale
          barThickness: 2, // Rende la barra sottile come una linea
          order: 2
        }
      ]
    },
    options: {
      ...baseChartOptions(),
      plugins: {
        ...baseChartOptions().plugins,
        tooltip: {
          ...baseChartOptions().plugins.tooltip,
          // Configura il tooltip per mostrare i dati di un solo dataset altrimenti si duplica
          filter: function(tooltipItem) {
            return tooltipItem.datasetIndex === 0; 
          },
          callbacks: {
            label: ctx => {
              const d = clean[ctx.dataIndex];
              return ` ${Number(d.conteggio).toLocaleString('it-IT')} pozzi · ${ctx.parsed.y.toFixed(1)}%`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: '#aeb9c2',
            font: { size: 9 },
            maxRotation: 45,
            minRotation: 25,
            autoSkip: false
          },
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: '#aeb9c2',
            callback: value => `${value}%`
          },
          grid: { color: 'rgba(255,255,255,0.06)' }
        }
      }
    }
  })
}

async function initProfondita() {
  const res = await fetch(`${API_BASE}/pozzi/mappa`)

  if (!res.ok) {
    throw new Error(`Errore HTTP ${res.status}`)
  }

  const pozzi = await res.json()

  // Recupera le profondità valide
  const depths = pozzi
    .map(p => Number(p.profondita))
    .filter(d => Number.isFinite(d) && d >= 0)

  if (!depths.length) return

  // Ordina le profondità per calcolare il percentile
  const sortedDepths = [...depths].sort((a, b) => a - b)

  /*
   * Usiamo il 98° percentile per individuare la profondità
   * oltre la quale iniziano i valori più rari.
   */
  const p98 = percentile(sortedDepths, 0.98)

  // Ampiezza delle classi
  const binWidth = 250

  /*
   * Le classi normali arrivano fino al 98° percentile,
   * arrotondato ai 250 metri successivi.
   */
  const normalMax = Math.max(
    binWidth,
    Math.ceil(p98 / binWidth) * binWidth
  )

  const labels = []
  const counts = []

  // ---------------------------------------------------------
  // CLASSI PRINCIPALI
  // ---------------------------------------------------------

  for (let start = 0; start < normalMax; start += binWidth) {
    const end = start + binWidth

    const count = depths.filter(
      d => d >= start && d < end
    ).length

    labels.push(`${start}-${end} m`)
    counts.push(count)
  }

  // ---------------------------------------------------------
  // CODA DEI VALORI MOLTO PROFONDI
  // ---------------------------------------------------------

  const tailCount = depths.filter(
    d => d >= normalMax
  ).length

  if (tailCount > 0) {
    labels.push(`>${normalMax} m`)
    counts.push(tailCount)
  }

  // ---------------------------------------------------------
  // PERCENTUALI
  // ---------------------------------------------------------

  const total = depths.length

  const percentages = counts.map(
    count => (count / total) * 100
  )

  // ---------------------------------------------------------
  // GRAFICO
  // ---------------------------------------------------------

  new Chart(profChart.value, {
    type: 'bar',

    data: {
      labels,

      datasets: [
        {
          data: percentages,

          backgroundColor: '#81c784',

          borderRadius: 3,

          borderSkipped: false
        }
      ]
    },

    options: {
      ...baseChartOptions(),

      plugins: {
        ...baseChartOptions().plugins,

        tooltip: {
          ...baseChartOptions().plugins.tooltip,

          callbacks: {
            label: ctx => {
              const count = counts[ctx.dataIndex]

              const percentage = ctx.parsed.y

              return ` ${count.toLocaleString('it-IT')} pozzi · ${percentage.toFixed(1)}%`
            }
          }
        }
      },

      scales: {
        x: {
           title: {
            display: true,
            text: 'Profondità (m)',
            color: '#9faab2',
            font: {
              size: 10
            }
          },

          ticks: {
            color: '#aeb9c2',

            font: {
              size: 8
            },

            autoSkip: false,

            maxRotation: 60,

            minRotation: 45,

            padding: 4
          },

          grid: {
            display: false
          }
        },

        y: {
          beginAtZero: true,

          title: {
            display: true,

            text: '% pozzi',

            color: '#9faab2',

            font: {
              size: 10
            }
          },

          ticks: {
            color: '#aeb9c2',

            callback: value => `${value}%`
          },

          grid: {
            color: 'rgba(255,255,255,0.06)'
          }
        }
      }
    }
  })
}// ------ BOXPLOT ------
async function initBoxplot() {
  const res = await fetch(`${API_BASE}/pozzi/mappa`)
  const pozzi = await res.json()

  const gruppi = [
    { label: '0–500 m', min: 0, max: 500 },
    { label: '500–1000 m', min: 500, max: 1000 },
    { label: '1000–1500 m', min: 1000, max: 1500 },
    { label: '>1500 m', min: 1500, max: Infinity }
  ]

  const datiGruppi = gruppi.map(g => {
    const temps = pozzi
      .filter(p =>
        Number.isFinite(Number(p.profondita)) &&
        Number(p.profondita) >= g.min &&
        Number(p.profondita) < g.max &&
        p.temp_max !== null &&
        Number.isFinite(Number(p.temp_max))
      )
      .map(p => Number(p.temp_max))
      .sort((a, b) => a - b)

    return { label: g.label, temps }
  })

  drawBoxplotSVG(datiGruppi)
}

function percentile(sorted, p) {
  if (!sorted.length) return null
  const index = (sorted.length - 1) * p
  const lower = Math.floor(index)
  const upper = Math.ceil(index)
  if (lower === upper) return sorted[lower]
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower)
}

function calcolaBoxStats(values) {
  if (!values.length) return null

  const sorted = [...values].sort((a, b) => a - b)
  const q1 = percentile(sorted, 0.25)
  const median = percentile(sorted, 0.5)
  const q3 = percentile(sorted, 0.75)
  const iqr = q3 - q1

  const lowerFence = q1 - 1.5 * iqr
  const upperFence = q3 + 1.5 * iqr

  let min = sorted[0]
  let max = sorted[sorted.length - 1]

  for (const v of sorted) {
    if (v >= lowerFence) {
      min = v
      break
    }
  }

  for (let i = sorted.length - 1; i >= 0; i--) {
    if (sorted[i] <= upperFence) {
      max = sorted[i]
      break
    }
  }

  const outliers = sorted.filter(v => v < min || v > max)

  return { min, q1, median, q3, max, outliers, n: sorted.length }
}

function drawBoxplotSVG(gruppi) {
  const svg = boxplotSvg.value
  if (!svg) return

  const W = svg.clientWidth || 600
  const H = svg.clientHeight || 260
  const marginLeft = 50
  const marginRight = 20
  const marginTop = 20
  const marginBottom = 45

  const plotW = W - marginLeft - marginRight
  const plotH = H - marginTop - marginBottom

  const stats = gruppi.map(g => ({
    label: g.label,
    stats: calcolaBoxStats(g.temps)
  }))

  const allValues = gruppi.flatMap(g => g.temps)
  if (!allValues.length) {
    svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#777">Dati non disponibili</text>'
    return
  }

  const sortedAll = [...allValues].sort((a, b) => a - b)
  const p99 = percentile(sortedAll, 0.99)
  const maxTemp = Math.max(10, Math.ceil((p99 || Math.max(...allValues)) / 10) * 10)

  const scaleY = v =>
    marginTop + plotH - (Math.max(0, Math.min(v, maxTemp)) / maxTemp) * plotH

  const nGruppi = gruppi.length
  const boxWidth = Math.min(70, (plotW / nGruppi) * 0.5)
  const scaleX = i => marginLeft + (i + 0.5) * (plotW / nGruppi)

  let svgContent = ''

  for (let t = 0; t <= maxTemp; t += Math.max(10, maxTemp / 5)) {
    const y = scaleY(t)
    svgContent += `
      <line x1="${marginLeft}" y1="${y}" x2="${W - marginRight}" y2="${y}"
        stroke="rgba(255,255,255,0.07)" stroke-width="1"/>
      <text x="${marginLeft - 7}" y="${y + 4}" text-anchor="end"
        font-size="9" fill="#9da8b0">${Math.round(t)}</text>
    `
  }

  svgContent += `
    <text transform="rotate(-90)" x="${-(H / 2)}" y="14"
      text-anchor="middle" font-size="9" fill="#9da8b0">Temperatura (°C)</text>
  `

  stats.forEach((item, i) => {
    const s = item.stats
    const cx = scaleX(i)
    const color = COLORS[i % COLORS.length]

    if (!s) {
      svgContent += `
        <text x="${cx}" y="${H - 7}" text-anchor="middle"
          font-size="9" fill="#888">${item.label}</text>
        <text x="${cx}" y="${plotH / 2 + marginTop}" text-anchor="middle"
          font-size="9" fill="#555">N/D</text>
      `
      return
    }

    const yMin = scaleY(s.min)
    const yQ1 = scaleY(s.q1)
    const yMedian = scaleY(s.median)
    const yQ3 = scaleY(s.q3)
    const yMax = scaleY(s.max)

    const x1 = cx - boxWidth / 2
    const x2 = cx + boxWidth / 2

    svgContent += `
      <line x1="${cx}" y1="${yMin}" x2="${cx}" y2="${yQ1}"
        stroke="${color}" stroke-width="1.5" stroke-dasharray="3,2"/>
      <line x1="${cx}" y1="${yQ3}" x2="${cx}" y2="${yMax}"
        stroke="${color}" stroke-width="1.5" stroke-dasharray="3,2"/>

      <line x1="${x1 + boxWidth * 0.2}" y1="${yMin}"
        x2="${x2 - boxWidth * 0.2}" y2="${yMin}"
        stroke="${color}" stroke-width="1.5"/>
      <line x1="${x1 + boxWidth * 0.2}" y1="${yMax}"
        x2="${x2 - boxWidth * 0.2}" y2="${yMax}"
        stroke="${color}" stroke-width="1.5"/>

      <rect x="${x1}" y="${yQ3}" width="${boxWidth}"
        height="${Math.max(1, yQ1 - yQ3)}"
        fill="${color}" fill-opacity="0.28"
        stroke="${color}" stroke-width="1.5" rx="3"/>

      <line x1="${x1}" y1="${yMedian}" x2="${x2}" y2="${yMedian}"
        stroke="${color}" stroke-width="2.5"/>

      <text x="${cx}" y="${H - 7}" text-anchor="middle"
        font-size="9" fill="#d0d8dd">${item.label}</text>

      <text x="${cx}" y="${Math.max(12, yQ3 - 7)}"
        text-anchor="middle" font-size="8" fill="#8f9aa2">n=${s.n}</text>
    `

    // Mostra gli outlier solo se sono pochi, per non sovraccaricare il grafico.
    if (s.outliers.length <= 20) {
      s.outliers.forEach(v => {
        const y = scaleY(v)
        svgContent += `
          <circle cx="${cx}" cy="${y}" r="2.5"
            fill="${color}" opacity="0.75"/>
        `
      })
    }
  })

  svg.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg"
      width="${W}" height="${H}"
      viewBox="0 0 ${W} ${H}">
      ${svgContent}
    </svg>
  `
}

// ------ LITOLOGIA ------

/*
async function initLitologia() {
  try {
    const res = await fetch(`${API_BASE}/pozzi/litologie/termini`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    
    // Ora l'API restituisce { totale_pozzi_univoci: 1234, dati: [...] }
    const responseData = await res.json()

    // 1. IL TOTALE REALE VIENE DIRETTAMENTE DALL'API (niente più .reduce per il totale!)
    const total = responseData.totale_pozzi_univoci
    litoTotal.value = total

    // 2. QUI USI responseData.dati (al posto di data) per filtrare, mappare e ordinare
    const sorted = responseData.dati
      .filter(d => d.termine && Number(d.n_pozzi || 0) > 0)
      .map(d => [d.termine, Number(d.n_pozzi)])
      .sort((a, b) => b[1] - a[1])

    // 3. LOGICA TOP 15 + "ALTRO" (rimane identica)
    let groupedData = []
    if (sorted.length > 15) {
      groupedData = sorted.slice(0, 15)
      const othersCount = sorted.slice(15).reduce((sum, [, count]) => sum + count, 0)
      groupedData.push(['Altro', othersCount])
    } else {
      groupedData = [...sorted]
    }

    // 4. LEGENDA (ora calcola le % rispetto al VERO numero di pozzi univoci)
    litoLegend.value = groupedData.map(([name, count], i) => ({
      name,
      count,
      percent: total ? ((count / total) * 100).toFixed(1) : '0.0',
      color: COLORS[i % COLORS.length]
    }))

    // 5. CONFIGURAZIONE CHART.JS
    new Chart(litoChart.value, {
      type: 'bar',
      data: {
        labels: groupedData.map(([name]) => name),
        datasets: [{
          data: groupedData.map(([, count]) => count),
          backgroundColor: groupedData.map((_, i) => COLORS[i % COLORS.length]),
          borderColor: '#1a2a3a',
          borderWidth: 2
        }]
      },
      options: {
        indexAxis: 'y', // Grafico orizzontale
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#101b25',
            titleColor: '#fff',
            bodyColor: '#d9e2e8',
            borderColor: 'rgba(255,255,255,0.12)',
            borderWidth: 1,
            padding: 10,
            callbacks: {
              label: ctx => {
                const count = Number(ctx.raw || 0)
                // Anche qui usa 'total' (il totale univoco dall'API)
                const percent = total ? (count / total) * 100 : 0
                return ` ${count.toLocaleString('it-IT')} pozzi · ${percent.toFixed(1)}%`
              }
            }
          }
        }
      }
    })
  } catch (e) {
    console.warn('Litologia non disponibile:', e.message)
    litoLegend.value = []
    litoTotal.value = 0
  }
}*/

async function initLitologia() {
  try {
    const res = await fetch(`${API_BASE}/pozzi/litologie/termini`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const responseData = await res.json()

    // Base corretta per le percentuali: totale strati (partizione esatta, no overlap)
    const totalStrati = responseData.totale_strati
    litoTotal.value = responseData.totale_pozzi_univoci // mostralo come "N pozzi coinvolti", non come base %

    const sorted = responseData.dati
      .filter(d => d.termine && Number(d.n_strati || 0) > 0)
      .map(d => [d.termine, Number(d.n_strati), Number(d.n_pozzi)])
      .sort((a, b) => b[1] - a[1])

    let groupedData = []
    if (sorted.length > 15) {
      groupedData = sorted.slice(0, 15)
      const othersStrati = sorted.slice(15).reduce((sum, [, nStrati]) => sum + nStrati, 0)
      const othersPozzi = sorted.slice(15).reduce((sum, [, , nPozzi]) => sum + nPozzi, 0)
      groupedData.push(['Altro', othersStrati, othersPozzi])
    } else {
      groupedData = [...sorted]
    }

    litoLegend.value = groupedData.map(([name, nStrati, nPozzi], i) => ({
      name,
      count: nStrati,
      percent: totalStrati ? ((nStrati / totalStrati) * 100).toFixed(1) : '0.0',
      pozzi: nPozzi, // se vuoi mostrarlo separatamente in legenda
      color: COLORS[i % COLORS.length]
    }))

    new Chart(litoChart.value, {
      type: 'bar',
      data: {
        labels: groupedData.map(([name]) => name),
        datasets: [{
          data: groupedData.map(([, nStrati]) => nStrati),
          backgroundColor: groupedData.map((_, i) => COLORS[i % COLORS.length]),
          borderColor: '#1a2a3a',
          borderWidth: 2
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#101b25',
            titleColor: '#fff',
            bodyColor: '#d9e2e8',
            borderColor: 'rgba(255,255,255,0.12)',
            borderWidth: 1,
            padding: 10,
            callbacks: {
              label: ctx => {
                const [, nStrati, nPozzi] = groupedData[ctx.dataIndex]
                const percent = totalStrati ? (nStrati / totalStrati) * 100 : 0
                return ` ${nStrati.toLocaleString('it-IT')} strati (${nPozzi} pozzi) · ${percent.toFixed(1)}%`
              }
            }
          }
        }
      }
    })
  } catch (e) {
    console.warn('Litologia non disponibile:', e.message)
    litoLegend.value = []
    litoTotal.value = 0
  }
}

// ------ MOUNT ------
onMounted(async () => {
  await nextTick()

  try {
    await Promise.all([
      initRegione(),
      initScopo(),
      initUso(),
      initProfondita(),
      initBoxplot(),
      initLitologia()
    ])
  } catch (e) {
    console.error('Errore inizializzazione grafici:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.distributions-wrapper {
  background: #7d6b5a;
  min-height: 100%;
  padding: 24px;
  color: white;
  overflow-y: auto;
  box-sizing: border-box;
}

.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin: 0 auto 22px;
  max-width: 1500px;
}

.page-title {
  margin: 0;
  font-size: 23px;
  font-weight: 650;
  color: white;
  letter-spacing: 0.3px;
}

.page-subtitle {
  margin: 5px 0 0;
  color: rgba(255,255,255,0.58);
  font-size: 12px;
}

.loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 160px;
  color: #b9c4cb;
  font-size: 13px;
}

.loading-spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255,255,255,0.18);
  border-top-color: #4fc3f7;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.dashboard-grid {
  max-width: 1500px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 17px;
}

.chart-card {
  background: #1a2a3a;
  border-radius: 12px;
  padding: 16px;
  min-height: 320px;
  border: 1px solid rgba(255,255,255,0.065);
  box-shadow: 0 7px 22px rgba(0,0,0,0.22);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.map-card {
  min-height: 390px;
}

.wide-card {
  min-height: 350px;
}

.card-heading {
  min-height: 40px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.card-kicker {
  display: block;
  color: #6dcae8;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-size: 8px;
  font-weight: 700;
  margin-bottom: 3px;
}

.chart-title {
  margin: 0;
  color: #e5ebef;
  font-size: 13px;
  font-weight: 600;
}

.card-note {
  color: #7f8e99;
  font-size: 9px;
  padding-top: 3px;
  white-space: nowrap;
}

.chart-wrapper {
  flex: 1;
  min-height: 0;
  position: relative;
}

.map-wrapper {
  min-height: 320px;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 320px;
  border-radius: 8px;
  overflow: hidden;
}

.lollipop-wrapper {
  min-height: 300px;
}

.depth-wrapper {
  min-height: 300px;
}

.boxplot-wrapper {
  min-height: 290px;
}

.boxplot-wrapper svg {
  width: 100%;
  height: 100%;
  display: block;
}

.lito-card {
  min-height: 390px;
}

.lito-layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(240px, 42%) minmax(0, 1fr);
  gap: 16px;
}

.donut-container {
  min-height: 320px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}

.donut-center strong {
  display: block;
  color: #f1f5f7;
  font-size: 21px;
  font-weight: 650;
  line-height: 1;
}

.donut-center span {
  display: block;
  margin-top: 5px;
  color: #8998a2;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
}

.lito-legend {
  overflow-y: auto;
  min-height: 0;
  max-height: 325px;
  padding-right: 4px;
}

.lito-row {
  display: grid;
  grid-template-columns: 9px minmax(0, 1fr) 50px 42px;
  gap: 8px;
  align-items: center;
  min-height: 27px;
  border-bottom: 1px solid rgba(255,255,255,0.045);
}

.lito-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.lito-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #cbd5db;
  font-size: 10px;
}

.lito-percent {
  text-align: right;
  color: #dfe7eb;
  font-size: 10px;
  font-weight: 600;
}

.lito-count {
  text-align: right;
  color: #778791;
  font-size: 9px;
}

.lito-legend::-webkit-scrollbar {
  width: 5px;
}

.lito-legend::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.13);
  border-radius: 10px;
}

.legend-box {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 5px;
  vertical-align: -2px;
  border-radius: 2px;
}

@media (max-width: 1050px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .lito-layout {
    grid-template-columns: minmax(220px, 40%) minmax(0, 1fr);
  }
}

@media (max-width: 700px) {
  .distributions-wrapper {
    padding: 14px;
  }

  .dashboard-grid {
    gap: 12px;
  }

  .chart-card,
  .wide-card,
  .map-card,
  .lito-card {
    min-height: 300px;
  }

  .lito-layout {
    grid-template-columns: 1fr;
  }

  .donut-container {
    min-height: 220px;
  }

  .lito-legend {
    max-height: 220px;
  }

  .page-title {
    font-size: 19px;
  }
}
</style>
