<template>
  <div class="theme-settings">
    <button class="settings-toggle" @click="isOpen = !isOpen" title="Theme Settings">
      🎨
    </button>
    <div v-if="isOpen" class="settings-panel">
      <h3>UI Customization</h3>
      <div class="setting-group">
        <label>Theme</label>
        <select v-model="currentTheme" @change="applyTheme">
          <option value="default">Cyberpunk (Dark)</option>
          <option value="minimalist">Minimalist (Light)</option>
          <option value="forest">Ocean (Deep Blue)</option>
        </select>
      </div>
      <div class="setting-group">
        <label>Accent Color</label>
        <input type="color" v-model="accentColor" @input="applyAccentColor" />
      </div>
      <button class="close-btn" @click="isOpen = false">Close</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isOpen = ref(false)
const currentTheme = ref(localStorage.getItem('theme') || 'default')
const accentColor = ref(localStorage.getItem('accentColor') || '#00bcd4')

const applyTheme = () => {
  document.documentElement.setAttribute('data-theme', currentTheme.value)
  localStorage.setItem('theme', currentTheme.value)
  window.dispatchEvent(new CustomEvent('theme-changed', { detail: currentTheme.value }))
}

const applyAccentColor = () => {
  document.documentElement.style.setProperty('--primary-color', accentColor.value)
  localStorage.setItem('accentColor', accentColor.value)
}

onMounted(() => {
  applyTheme()
  applyAccentColor()
})
</script>

<style scoped>
.theme-settings {
  position: relative;
}

.settings-toggle {
  background: transparent;
  border: 1px solid var(--border-color);
  font-size: 1.2rem;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.settings-toggle:hover {
  background: var(--surface-color);
  border-color: var(--primary-color);
}

.settings-panel {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 10px;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  width: 200px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

h3 {
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.setting-group {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

select, input[type="color"] {
  width: 100%;
  padding: 4px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 4px;
}

.close-btn {
  width: 100%;
  padding: 6px;
  background: var(--primary-color);
  color: #000;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.8rem;
}
</style>
