<script setup>
import { ref, onMounted, reactive } from 'vue'
import ControlPanel from './components/ControlPanel.vue'
import WiFiSetup from './components/WiFiSetup.vue'
import Login from './components/Login.vue'
import AuthSetup from './components/AuthSetup.vue'

// View State: 'loading', 'auth-setup', 'login', 'app'
const view = ref('loading')
const uiMode = ref('control') // app tabs

// Global State
const appState = reactive({
  message: '',
  led: true,
  brightness: 0.1,
  mode: 0,
  colors: [[0,0,0], [0,0,0], [0,0,0], [0,0,0]],
  storage: { free: 0, total: 0 }
})

// Helper for Authenticated Requests
const apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem('token')
  const headers = { ...options.headers }
  if (token) headers['X-Token'] = token
  
  const res = await fetch(url, { ...options, headers })
  if (res.status === 401) {
    view.value = 'login'
    throw new Error('Unauthorized')
  }
  return res
}

const checkAuth = async () => {
  try {
    // 1. Check if setup is needed
    const statusRes = await fetch('/api/auth/status')
    const statusData = await statusRes.json()
    
    if (!statusData.setup) {
      view.value = 'auth-setup'
      return
    }
    
    // 2. Try to fetch data with token
    await fetchData()
    view.value = 'app'
    
  } catch (e) {
    // fetchData handles 401 redirect
    console.log("Auth check failed", e)
  }
}

const fetchData = async () => {
  const [msgRes, ledRes] = await Promise.all([
    apiFetch('/api/message'),
    apiFetch('/api/settings')
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
}

const handleLogin = (token) => {
  view.value = 'loading'
  fetchData().then(() => view.value = 'app')
}

const handleSetupComplete = () => {
  view.value = 'login'
}

onMounted(() => {
  if (window.location.hostname === '192.168.4.1') {
    // AP Mode: Show WiFi Setup directly? Or still require auth?
    // Let's require auth for security even in AP mode.
  }
  checkAuth()
  
  // Poll only if logged in
  setInterval(() => {
    if (view.value === 'app') fetchData()
  }, 5000)
})
</script>

<template>
  <div class="container">
    <div v-if="view === 'loading'" class="loading">Loading...</div>
    
    <AuthSetup v-else-if="view === 'auth-setup'" @setup-complete="handleSetupComplete" />
    
    <Login v-else-if="view === 'login'" @login="handleLogin" />
    
    <div v-else-if="view === 'app'">
      <header>
        <h1>📡 ESP32 Hub</h1>
        <div class="main-tabs">
          <button :class="{active: uiMode==='control'}" @click="uiMode='control'">Control</button>
          <button :class="{active: uiMode==='setup'}" @click="uiMode='setup'">WiFi Setup</button>
        </div>
      </header>

      <main>
        <ControlPanel v-if="uiMode === 'control'" :state="appState" @refresh="fetchData" />
        <WiFiSetup v-if="uiMode === 'setup'" />
      </main>
    </div>
  </div>
</template>

<style>
/* ... (Keep existing styles) ... */
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