<script setup>
import { ref, reactive } from 'vue'

const wifiNetworks = ref([])
const scanning = ref(false)
const wifiForm = reactive({ ssid: '', password: '' })

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
</script>

<template>
  <div class="card">
    <h2>WiFi Settings</h2>
    <button class="full-width" @click="scanWifi" :disabled="scanning">{{ scanning ? 'Scanning...' : 'Scan Networks' }}</button>
    
    <ul class="wifi-list" v-if="wifiNetworks.length">
      <li v-for="net in wifiNetworks" @click="wifiForm.ssid = net.ssid">
        <span class="ssid">{{ net.ssid }}</span>
        <span class="rssi">{{ net.rssi }}dBm</span>
      </li>
    </ul>

    <div class="form">
      <input v-model="wifiForm.ssid" placeholder="SSID">
      <input v-model="wifiForm.password" type="password" placeholder="Password">
      <button class="primary full-width" @click="saveWifi">Save & Connect</button>
    </div>
  </div>
</template>

<style scoped>
.wifi-list { list-style: none; padding: 0; margin: 15px 0; border: 1px solid #e1e4e8; border-radius: 8px; max-height: 250px; overflow-y: auto; }
.wifi-list li { padding: 12px; border-bottom: 1px solid #e1e4e8; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
.wifi-list li:hover { background: #f8f9fa; }
.wifi-list li:last-child { border-bottom: none; }
.ssid { font-weight: 500; }
.rssi { font-size: 0.8rem; color: #888; background: #eee; padding: 2px 6px; border-radius: 4px; }
.form input { margin-bottom: 10px; }
</style>
