<script setup>
import { ref, onMounted, reactive } from 'vue'

const currentMessage = ref('')
const newMessage = ref('')
const ledEnabled = ref(true)
const brightness = ref(0.1)
const ledMode = ref(0)
const ledColors = ref([[0,0,0], [0,0,0], [0,0,0], [0,0,0]])
const storage = reactive({ free: 0, total: 0 })
const loading = ref(true)
const sending = ref(false)
const wifiNetworks = ref([])
const scanning = ref(false)
const wifiForm = reactive({ ssid: '', password: '' })

// Mode: 'control' or 'setup'
const uiMode = ref('control')

const fetchData = async () => {
  try {
    const [msgRes, ledRes] = await Promise.all([
      fetch('/api/message'),
      fetch('/api/settings')
    ])
    
    const msgData = await msgRes.json()
    const ledData = await ledRes.json()
    
    currentMessage.value = msgData.message
    ledEnabled.value = ledData.led
    brightness.value = ledData.brightness
    ledMode.value = ledData.mode
    ledColors.value = ledData.colors || [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
    storage.free = ledData.storage_free || 0
    storage.total = ledData.storage_total || 0
    
    loading.value = false
  } catch (e) {
    console.error("Fetch error", e)
  }
}

const updateMessage = async () => {
  sending.value = true
  try {
    await fetch('/api/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: newMessage.value })
    })
    currentMessage.value = newMessage.value
    newMessage.value = ''
  } catch (e) {
    alert("Failed")
  } finally {
    sending.value = false
  }
}

const clearMessage = async () => {
  newMessage.value = ''
  await updateMessage()
}

const toggleLed = async () => {
  await fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ led: ledEnabled.value })
  })
}

const updateSettings = async (body) => {
  await fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
}

const rgbToHex = (rgb) => "#" + ((1 << 24) + (rgb[0] << 16) + (rgb[1] << 8) + rgb[2]).toString(16).slice(1)
const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)] : null;
}

const updatePixel = (idx, hex) => {
  const rgb = hexToRgb(hex)
  if (!rgb) return
  ledColors.value[idx] = rgb
  updateSettings({ pixel: { index: idx, r: rgb[0], g: rgb[1], b: rgb[2] } })
}

const scanWifi = async () => {
  scanning.value = true
  try {
    const res = await fetch('/api/scan')
    wifiNetworks.value = await res.json()
  } catch(e) {
    alert("Scan failed")
  } finally {
    scanning.value = false
  }
}

const saveWifi = async () => {
  if(!wifiForm.ssid) return
  try {
    await fetch('/api/wifi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(wifiForm)
    })
    alert("Saved! Rebooting...")
  } catch(e) {
    alert("Error saving")
  }
}

onMounted(() => {
  fetchData()
  setInterval(fetchData, 5000)
})
</script>

<template>
  <div class="container">
    <header>
      <h1>📡 ESP32 Controller</h1>
      <div class="tabs">
        <button :class="{active: uiMode==='control'}" @click="uiMode='control'">Control</button>
        <button :class="{active: uiMode==='setup'}" @click="uiMode='setup'">WiFi Setup</button>
      </div>
    </header>

    <main v-if="uiMode === 'control'">
      <div class="card">
        <h2>E-Ink Message</h2>
        <div class="message-box">{{ currentMessage || '(Empty)' }}</div>
        <div class="input-group">
          <input v-model="newMessage" placeholder="Type message..." @keyup.enter="updateMessage">
          <button @click="updateMessage" :disabled="sending">Send</button>
        </div>
        <button class="secondary" @click="clearMessage">Clear</button>
      </div>

      <div class="card">
        <div class="row">
          <h2>LED Control</h2>
          <label class="switch">
            <input type="checkbox" v-model="ledEnabled" @change="toggleLed">
            <span class="slider"></span>
          </label>
        </div>

        <div v-if="ledEnabled" class="led-settings">
          <label>Brightness</label>
          <input type="range" v-model.number="brightness" min="0" max="1" step="0.05" @change="updateSettings({brightness})">
          
          <label>Mode</label>
          <select v-model.number="ledMode" @change="updateSettings({mode: ledMode})">
            <option :value="0">Auto (Status)</option>
            <option :value="1">Manual</option>
          </select>

          <div v-if="ledMode === 1" class="pixels">
            <div v-for="(color, idx) in ledColors" :key="idx">
              <input type="color" :value="rgbToHex(color)" @input="updatePixel(idx, $event.target.value)">
            </div>
          </div>
        </div>
      </div>

      <div class="footer">
        Storage: {{ (storage.free / 1024).toFixed(1) }} KB Free / {{ (storage.total / 1024).toFixed(1) }} KB Total
      </div>
    </main>

    <main v-else>
      <div class="card">
        <h2>WiFi Settings</h2>
        <button @click="scanWifi" :disabled="scanning">{{ scanning ? 'Scanning...' : 'Scan Networks' }}</button>
        
        <ul class="wifi-list" v-if="wifiNetworks.length">
          <li v-for="net in wifiNetworks" @click="wifiForm.ssid = net.ssid">
            <span>{{ net.ssid }}</span>
            <small>{{ net.rssi }}dBm</small>
          </li>
        </ul>

        <div class="form">
          <input v-model="wifiForm.ssid" placeholder="SSID">
          <input v-model="wifiForm.password" type="password" placeholder="Password">
          <button class="primary" @click="saveWifi">Save & Connect</button>
        </div>
      </div>
    </main>
  </div>
</template>

<style>
:root { --primary: #007bff; --bg: #f0f2f5; }
body { font-family: system-ui, sans-serif; background: var(--bg); margin: 0; padding: 20px; color: #333; }
.container { max-width: 480px; margin: 0 auto; }
.card { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
h1, h2 { margin-top: 0; }
input, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;}
button { padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer; font-weight: 600; background: var(--primary); color: white; }
button:disabled { opacity: 0.7; }
button.secondary { background: #6c757d; }
button.active { background: #0056b3; }
.tabs { display: flex; gap: 10px; margin-bottom: 20px; }
.message-box { font-size: 1.5em; font-weight: bold; margin: 15px 0; min-height: 1.2em; word-break: break-word; }
.input-group { display: flex; gap: 10px; }
.row { display: flex; justify-content: space-between; align-items: center; }
.pixels { display: flex; justify-content: space-around; margin-top: 15px; }
.wifi-list { list-style: none; padding: 0; border: 1px solid #eee; border-radius: 8px; max-height: 200px; overflow-y: auto; }
.wifi-list li { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; justify-content: space-between; }
.wifi-list li:hover { background: #f9f9f9; }
.switch { position: relative; display: inline-block; width: 50px; height: 28px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 34px; }
.slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
input:checked + .slider { background-color: var(--primary); }
input:checked + .slider:before { transform: translateX(22px); }
.footer { text-align: center; color: #888; font-size: 0.8rem; }
</style>