<script setup>
import { ref } from 'vue'

const password = ref('')
const error = ref('')
const loading = ref(false)

const emit = defineEmits(['login'])

const login = async () => {
  if (!password.value) return
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: password.value })
    })
    
    const data = await res.json()
    if (res.ok) {
      localStorage.setItem('token', data.token)
      emit('login', data.token)
    } else {
      error.value = data.error || 'Login failed'
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
    <h2>🔐 Login</h2>
    <form @submit.prevent="login">
      <input type="password" v-model="password" placeholder="Enter Password" autofocus>
      <div v-if="error" class="error">{{ error }}</div>
      <button class="primary full-width" :disabled="loading">
        {{ loading ? 'Checking...' : 'Login' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-card { max-width: 350px; margin: 50px auto; text-align: center; }
.error { color: #dc3545; margin: 10px 0; font-size: 0.9rem; }
</style>
