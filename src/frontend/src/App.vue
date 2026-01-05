<template>
  <div class="container">
    <header>
      <h1>Open-Detective</h1>
      <p>Don't just query. Investigate.</p>
    </header>
    <main>
      <div class="chat-container">
        <p>Backend status: {{ status }}</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const status = ref('Checking...')

onMounted(async () => {
  try {
    const response = await axios.get('/api/health')
    status.value = response.data.status === 'ok' ? 'Connected' : 'Error'
  } catch (error) {
    status.value = 'Disconnected'
  }
})
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  font-family: Arial, sans-serif;
  text-align: center;
}
header {
  margin-bottom: 2rem;
}
.chat-container {
  border: 1px solid #ccc;
  padding: 1rem;
  border-radius: 8px;
}
</style>
