<template>
  <div class="container">
    <header>
      <h1>🕵️‍♂️ Open-Detective</h1>
      <p class="subtitle">Don't just query. Investigate.</p>
    </header>

    <main>
      <div class="chat-window">
        <!-- Messages Area -->
        <div class="messages" ref="messagesRef">
          <div v-for="(msg, index) in history" :key="index" :class="['message', msg.role]">
            <div class="content">
              <p>{{ msg.text }}</p>
              
              <!-- Display SQL if available (for assistant) -->
              <div v-if="msg.sql" class="sql-box">
                <strong>🔍 Executed SQL:</strong>
                <pre>{{ msg.sql }}</pre>
              </div>

              <!-- Display Chart if data is suitable -->
              <div v-if="msg.data && msg.data.length > 0" class="chart-wrapper">
                <ResultChart :data="msg.data" />
              </div>

              <!-- Display Data Table if available -->
              <div v-if="msg.data && msg.data.length > 0" class="data-table-wrapper">
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
          
          <div v-if="loading" class="message assistant">
            <div class="content">Thinking...</div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <input 
            v-model="inputMessage" 
            @keyup.enter="sendMessage"
            placeholder="Ask e.g.: 'Show me stars for fastapi'..." 
            :disabled="loading"
          />
          <button @click="sendMessage" :disabled="loading || !inputMessage.trim()">Send</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import axios from 'axios'
import ResultChart from './components/ResultChart.vue'

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  sql?: string
  data?: any[]
}
// ... (rest of the script setup)

const inputMessage = ref('')
const loading = ref(false)
const history = ref<ChatMessage[]>([
  { role: 'assistant', text: 'Hello! I am Open-Detective. Ask me about repository metrics (e.g., "fastapi stars", "vue activity").' }
])
const messagesRef = ref<HTMLElement | null>(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text) return

  // Add user message
  history.value.push({ role: 'user', text })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const res = await axios.post('/api/chat', { message: text })
    
    // Add assistant response
    history.value.push({
      role: 'assistant',
      text: res.data.answer,
      sql: res.data.sql_query,
      data: res.data.data
    })
  } catch (err) {
    history.value.push({
      role: 'assistant',
      text: 'Error: Failed to reach the detective backend.'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
/* Basic Reset & Layout */
.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  height: 90vh;
  display: flex;
  flex-direction: column;
}

header {
  text-align: center;
  margin-bottom: 1rem;
}

h1 { margin: 0; color: #2c3e50; }
.subtitle { color: #666; margin-top: 0.5rem; }

/* Chat Window */
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  background: #f9f9f9;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  align-items: flex-end;
}

.message.assistant {
  align-self: flex-start;
  align-items: flex-start;
}

.message .content {
  padding: 0.8rem 1.2rem;
  border-radius: 12px;
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.message.user .content {
  background: #007bff;
  color: white;
  border-bottom-right-radius: 2px;
}

.message.assistant .content {
  background: #ffffff;
  color: #333;
  border-bottom-left-radius: 2px;
}

/* SQL & Data Styles */
.sql-box {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  background: #2d2d2d;
  color: #aaccff;
  padding: 0.5rem;
  border-radius: 6px;
  overflow-x: auto;
}

.data-table-wrapper {
  margin-top: 0.5rem;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

th, td {
  border: 1px solid #eee;
  padding: 4px 8px;
  text-align: left;
}

th { background: #f1f1f1; font-weight: 600; }

/* Input Area */
.input-area {
  padding: 1rem;
  background: white;
  border-top: 1px solid #eee;
  display: flex;
  gap: 0.5rem;
}

input {
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  outline: none;
}

input:focus { border-color: #007bff; }

button {
  padding: 0 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

button:hover:not(:disabled) { background: #0056b3; }
button:disabled { background: #ccc; cursor: not-allowed; }
</style>