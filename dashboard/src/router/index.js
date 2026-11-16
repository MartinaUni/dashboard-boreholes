/*import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [],
})

export default router*/
import { createRouter, createWebHistory } from 'vue-router'
import GeoThermalDashboard from '/src/components/geothermaldashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: GeoThermalDashboard
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
