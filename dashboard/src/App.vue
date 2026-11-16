<script setup>
import GeoThermalDashboard from './components/GeoThermalDashboard.vue'
import DataDistribution from './components/datadistribution.vue'
</script>

<template>
  <div id="app">
    <GeoThermalDashboard />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
}
</style>
