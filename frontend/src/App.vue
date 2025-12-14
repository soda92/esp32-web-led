<script setup>
import { ref, onMounted, reactive } from 'vue'
import ControlPanel from './components/ControlPanel.vue'
import WiFiSetup from './components/WiFiSetup.vue'

const uiMode = ref('control')
const loading = ref(true)

// Global State
const appState = reactive({
  message: '',
  led: true,
  brightness: 0.1,
  mode: 0,
  colors: [[0,0,0], [0,0,0], [0,0,0], [0,0,0]],
  storage: { free: 0, total: 0 }
})

const fetchData = async () => {
  try {
    const [msgRes, ledRes] = await Promise.all([
      fetch('/api/message'),
      fetch('/api/settings')
    ])
    
    const msgData = await msgRes.json()
    const ledData = await ledRes.json()
    
    appState.message = msgData.message
    appState.led = ledData.led
    appState.brightness = ledData.brightness
    appState.mode = ledData.mode
    appState.colors = ledData.colors || [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
    appState.storage = { 
        free: ledData.storage_free || 0, 
        total: ledData.storage_total || 0 
    }
    
    loading.value = false
  } catch (e) {
    console.error("Fetch error", e)
  }
}

onMounted(() => {
  if (window.location.hostname === '192.168.4.1') {
    uiMode.value = 'setup'
  }
  fetchData()
  setInterval(fetchData, 5000)
})
</script>

<template>
  <div class="container">
    <header>
      <h1>📡 ESP32 Hub</h1>
      <div class="main-tabs">
        <button :class="{active: uiMode==='control'}" @click="uiMode='control'">Control</button>
        <button :class="{active: uiMode==='setup'}" @click="uiMode='setup'">WiFi Setup</button>
      </div>
    </header>

    <main v-if="loading" class="loading">Loading...</main>
    
    <main v-else>
      <ControlPanel v-if="uiMode === 'control'" :state="appState" @refresh="fetchData" />
      <WiFiSetup v-if="uiMode === 'setup'" />
    </main>
  </div>
</template>

<style>
:root { --primary: #007bff; --bg: #f4f6f8; --card-bg: #ffffff; --text: #2c3e50; --border: #e1e4e8; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); margin: 0; padding: 20px; color: var(--text); }
.container { max-width: 480px; margin: 0 auto; }
.card { background: var(--card-bg); padding: 20px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
h1 { font-size: 1.5rem; margin: 0; color: #1a1a1a; }
h2 { font-size: 1.1rem; margin: 0 0 15px 0; font-weight: 600; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }

/* Global Button Styles */
button { padding: 10px 16px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; font-size: 14px; transition: all 0.2s; background: #e2e6ea; color: var(--text); }
button.active { background: var(--primary); color: white; }
button.primary { background: var(--primary); color: white; }
button.secondary { background: #f1f3f5; color: #495057; }
button.full-width { width: 100%; margin-top: 10px; }
button:disabled { opacity: 0.6; cursor: not-allowed; }

/* Tabs */
.main-tabs { display: flex; gap: 8px; background: white; padding: 4px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
.sub-tabs { display: flex; margin-bottom: 15px; border-bottom: 1px solid var(--border); }
.sub-tabs span { padding: 10px 20px; cursor: pointer; font-weight: 500; color: #888; position: relative; }
.sub-tabs span.active { color: var(--primary); }
.sub-tabs span.active::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 100%; height: 2px; background: var(--primary); }

.loading { text-align: center; color: #888; margin-top: 50px; }
</style>