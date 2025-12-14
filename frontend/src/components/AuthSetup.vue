<script setup>
import { ref } from 'vue'

const password = ref('')
const confirm = ref('')
const error = ref('')
const loading = ref(false)

const emit = defineEmits(['setup-complete'])

const setup = async () => {
  if (password.value !== confirm.value) {
    error.value = "Passwords don't match"
    return
  }
  
  loading.value = true
  try {
    const res = await fetch('/api/auth/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: password.value })
    })
    
    if (res.ok) {
      alert("Password set! Please login.")
      emit('setup-complete')
    } else {
      error.value = 'Setup failed'
    }
  } catch (e) {
    error.value = 'Connection error'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card login-card">
    <h2>🆕 First Time Setup</h2>
    <p>Set a password for your device.</p>
    <form @submit.prevent="setup">
      <input type="password" v-model="password" placeholder="New Password" required>
      <input type="password" v-model="confirm" placeholder="Confirm Password" required>
      <div v-if="error" class="error">{{ error }}</div>
      <button class="primary full-width" :disabled="loading">
        {{ loading ? 'Saving...' : 'Set Password' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-card { max-width: 350px; margin: 50px auto; text-align: center; }
.error { color: #dc3545; margin: 10px 0; font-size: 0.9rem; }
</style>
