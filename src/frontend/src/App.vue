<template>
  <div class="app-layout">
    <!-- Sidebar / Header Area -->
    <header class="top-bar">
      <div class="brand">
        <span class="logo-icon">🕵️‍♂️</span>
        <div class="brand-text">
          <h1>Open-Detective</h1>
          <span class="status-badge" :class="{ online: backendConnected }">
            {{ backendConnected ? 'SYSTEM ONLINE' : 'OFFLINE' }}
          </span>
        </div>
      </div>
      <div class="actions">
        <ThemeSettings />
        <button class="action-btn" @click="exportToMarkdown" title="Export Case File">
          📁 EXPORT CASE
        </button>
      </div>
    </header>

    <main class="main-terminal">
      <div class="chat-interface">
        <!-- Messages Area -->
        <div class="messages-scroll" ref="messagesRef">
          <div v-for="(msg, index) in history" :key="index" :class="['message-row', msg.role]">
            
            <!-- Avatar -->
            <div class="avatar">
              {{ msg.role === 'assistant' ? '🤖' : '👤' }}
            </div>

            <!-- Bubble -->
            <div class="message-content">
              <div class="bubble" v-html="md.render(msg.text)"></div>

              <!-- Evidence: SQL -->
              <div v-if="msg.sql" class="evidence-block">
                <div class="evidence-header">
                  <span>🔍 EXECUTED QUERY <small v-if="msg.engineSource">({{ msg.engineSource.toUpperCase() }} ENGINE)</small></span>
                  <button 
                    class="copy-btn" 
                    :class="{ copied: copiedIndex === index }"
                    @click="copyToClipboard(msg.sql, index)"
                  >
                    {{ copiedIndex === index ? 'COPIED!' : 'COPY' }}
                  </button>
                </div>
                <pre class="code-block">{{ msg.sql }}</pre>
              </div>

              <!-- Evidence: Chart -->
              <div v-if="msg.data && msg.data.length > 0" class="evidence-block">
                <div class="evidence-header">📊 VISUAL ANALYSIS</div>
                <ResultChart :data="msg.data" :theme="currentTheme === 'minimalist' ? 'light' : 'dark'" />
              </div>

              <!-- Evidence: Table -->
              <div v-if="msg.data && msg.data.length > 0" class="evidence-block">
                <div class="evidence-header">💾 RAW DATA</div>
                <div class="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th v-for="key in Object.keys(msg.data[0])" :key="key">{{ key }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, i) in msg.data" :key="i">
                        <td v-for="val in row" :key="val">{{ val }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- Typing Indicator -->
          <div v-if="loading" class="message-row assistant">
            <div class="avatar">🤖</div>
            <div class="message-content">
              <div class="bubble typing">
                <span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-deck">
          <div class="input-wrapper">
            <input 
              v-model="inputMessage" 
              @keyup.enter="sendMessage"
              placeholder="Ask me anything about open source projects..." 
              :disabled="loading"
              autofocus
            />
            <button @click="sendMessage" :disabled="loading || !inputMessage.trim()">
              ➤
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import axios from 'axios'
import ResultChart from './components/ResultChart.vue'
import ThemeSettings from './components/ThemeSettings.vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  sql?: string
  data?: any[]
  engineSource?: string
}

const inputMessage = ref('')
const loading = ref(false)
const backendConnected = ref(false)
const history = ref<ChatMessage[]>([
  { role: 'assistant', text: 'Identity verified. Detective system initialized. Awaiting orders.' }
])
const messagesRef = ref<HTMLElement | null>(null)
const copiedIndex = ref<number | null>(null)
const currentTheme = ref(localStorage.getItem('theme') || 'default')

// Monitor theme changes from the settings component (simple poll or event would be better, but let's check localStorage for simplicity if it was reactive, which it isn't. Better: use a simple interval or a shared state if we had one. For now, let's just make it react to the settings change if we can.)
// Actually, let's just use a simple computed based on a body class or similar.
const isDark = () => {
  return currentTheme.value !== 'minimalist'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

onMounted(async () => {
  window.addEventListener('theme-changed', (e: any) => {
    currentTheme.value = e.detail
  })
  try {
    const res = await axios.get('/api/v1/health')
    if(res.data.status === 'ok') backendConnected.value = true
  } catch (e) {
    backendConnected.value = false
  }
})

const sendMessage = async () => {
  if (loading.value) return
  const text = inputMessage.value.trim()
  if (!text) return

  history.value.push({ role: 'user', text })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const res = await axios.post('/api/v1/chat', { message: text })
    
    history.value.push({
      role: 'assistant',
      text: res.data.answer,
      sql: res.data.sql_query,
      data: res.data.data,
      engineSource: res.data.engine_source
    })
  } catch (err) {
    history.value.push({
      role: 'assistant',
      text: '⚠️ SYSTEM ERROR: Connection lost or query failed.'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const exportToMarkdown = () => {
  let mdContent = `# 🕵️‍♂️ Open-Detective: Case File\n`
  mdContent += `**Date:** ${new Date().toLocaleString()}\n`
  mdContent += `**Status:** ${backendConnected.value ? 'ONLINE' : 'OFFLINE'}\n\n`
  mdContent += `---\n\n`

  history.value.forEach((msg, index) => {
    const role = msg.role === 'user' ? '👤 DETECTIVE' : '🤖 SYSTEM'
    mdContent += `### ${role}:\n${msg.text}\n\n`
    
    if (msg.sql) {
      mdContent += `**🔍 Query:** 
${msg.sql}

`
    }

    if (msg.data && msg.data.length > 0) {
      mdContent += `**📊 Evidence Data (Top 10 rows):**\n\n`
      // Create Markdown Table
      const headers = Object.keys(msg.data[0])
      mdContent += `| ${headers.join(' | ')} |\n`
      mdContent += `| ${headers.map(() => '---').join(' | ')} |\n`
      
      msg.data.slice(0, 10).forEach((row: any) => {
        mdContent += `| ${Object.values(row).join(' | ')} |\n`
      })
      if (msg.data.length > 10) {
        mdContent += `\n*(...and ${msg.data.length - 10} more records)*\n`
      }
      mdContent += `\n`
    }
    mdContent += `---\n\n`
  })

  // Trigger Download
  const blob = new Blob([mdContent], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `case-report-${new Date().toISOString().slice(0,10)}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const copyToClipboard = async (text: string, index: number) => {
  try {
    await navigator.clipboard.writeText(text)
    copiedIndex.value = index
    setTimeout(() => {
      if (copiedIndex.value === index) {
        copiedIndex.value = null
      }
    }, 2000)
  } catch (err) {
    console.error('Failed to copy: ', err)
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-primary);
}

/* Header */
.top-bar {
  padding: 1rem 2rem;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon {
  font-size: 2rem;
}

.brand-text h1 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text-primary);
}

.actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.action-btn {
  background: transparent;
  border: 1px solid var(--primary-color);
  color: var(--primary-color);
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.8rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.action-btn:hover {
  background: var(--surface-color);
  border-color: var(--primary-color);
  box-shadow: 0 0 8px var(--primary-color);
}

.status-badge {
  font-size: 0.7rem;
  padding: 2px 6px;
  background: var(--border-color);
  color: var(--text-secondary);
  border-radius: 4px;
  font-weight: bold;
}

.status-badge.online {
  background: rgba(0, 255, 0, 0.1);
  color: #00ff00;
  border: 1px solid #00ff00;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-family: monospace;
}

/* Main Terminal */
.main-terminal {
  flex: 1;
  overflow: hidden;
  display: flex;
  justify-content: center;
}

.chat-interface {
  width: 100%;
  max-width: 1000px;
  display: flex;
  flex-direction: column;
  background: var(--bg-color);
}

.messages-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Message Rows */
.message-row {
  display: flex;
  gap: 1rem;
  max-width: 85%;
}

.message-row.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-color);
  border-radius: 50%;
  font-size: 1.2rem;
  border: 1px solid var(--border-color);
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bubble {
  padding: 1rem 1.5rem;
  border-radius: 12px;
  background: var(--surface-color);
  line-height: 1.5;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.message-row.user .bubble {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: var(--bg-color);
}

/* Evidence Blocks (SQL, Charts, Data) */
.evidence-block {
  background: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.evidence-header {
  background: var(--header-bg);
  padding: 4px 10px;
  font-size: 0.7rem;
  color: var(--text-secondary);
  font-weight: bold;
  letter-spacing: 1px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.copy-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 0.6rem;
  padding: 2px 6px;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 50px;
}

.copy-btn:hover {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.copy-btn.copied {
  color: var(--accent-color);
  border-color: var(--accent-color);
  background: rgba(0, 255, 0, 0.1);
}

.code-block {
  margin: 0;
  padding: 1rem;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  color: var(--primary-color);
  white-space: pre-wrap;
}

.table-container {
  overflow-x: auto;
  max-height: 300px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

th, td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

th {
  background: var(--header-bg);
  color: var(--text-primary);
  position: sticky;
  top: 0;
}

td {
  color: var(--text-secondary);
}

/* Input Deck */
.input-deck {
  padding: 1.5rem;
  background: var(--bg-color);
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 1rem;
  background: var(--input-bg);
  padding: 0.5rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  padding: 0.8rem;
  font-family: inherit;
  font-size: 1rem;
  outline: none;
}

button {
  background: var(--primary-color);
  color: var(--bg-color);
  border: none;
  padding: 0 1.5rem;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  transition: opacity 0.2s;
}

button:hover:not(:disabled) {
  opacity: 0.9;
}
button:disabled {
  background: #444;
  color: #777;
  cursor: not-allowed;
}

/* Typing Animation */
.typing span {
  animation: blink 1.4s infinite both;
  font-size: 1.5rem;
  margin: 0 2px;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
}
</style>