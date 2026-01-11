<template>
  <el-config-provider :button="{ autoInsertSpace: true }">
    <div class="detective-app">
      <el-container class="full-height">
        <!-- Sidebar -->
        <el-aside width="280px" class="sidebar">
          <div class="sidebar-header" @click="reloadPage">
            <span class="logo">🕵️‍♂️</span>
            <div class="title-group">
              <h1 class="main-title">OPEN DETECTIVE</h1>
              <span class="sub-title">Neural Evidence Tracker</span>
            </div>
          </div>

          <div class="sidebar-stats">
            <div class="stat-item">
              <span class="label">ENGINE:</span>
              <el-tag size="small" :type="engineType === 'sqlbot' ? 'danger' : 'success'">{{ engineType.toUpperCase() }}</el-tag>
            </div>
            <div class="stat-item">
              <span class="label">STATUS:</span>
              <el-tag size="small" type="primary" effect="dark">CONNECTED</el-tag>
            </div>
          </div>

          <div class="sidebar-actions">
            <el-button class="action-btn" type="danger" plain @click="openDeepScan">
              <el-icon><Aim /></el-icon> Deep Scan (Battle Mode)
            </el-button>
            <el-button class="action-btn" type="primary" plain @click="exportCase" :disabled="chatHistory.length === 0">
              <el-icon><Download /></el-icon> Export Case File
            </el-button>
            <el-button class="action-btn" type="primary" plain @click="shareSession" :disabled="!currentSessionId">
              <el-icon><Share /></el-icon> Share Link
            </el-button>
            <el-button class="action-btn" @click="createNewSession">
              <el-icon><Refresh /></el-icon> New Investigation
            </el-button>
          </div>

          <div class="sidebar-sessions">
            <div class="session-label">HISTORY LOGS</div>
            <el-scrollbar>
              <div v-for="sess in sessions" :key="sess.id" 
                   :class="['session-item', { active: currentSessionId === sess.id }]"
                   @click="loadSession(sess.id)">
                <div class="session-info">
                   <div class="session-title">{{ sess.title }}</div>
                   <div class="session-date">{{ new Date(sess.created_at).toLocaleDateString() }}</div>
                </div>
                <el-button class="session-delete" type="danger" link size="small" @click="(e) => deleteSession(sess.id, e)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </el-scrollbar>
          </div>

          <div class="sidebar-footer">
            <div class="theme-switch" style="margin-bottom: 10px; text-align: center;">
                <el-button circle size="small" @click="toggleDark()">
                  <el-icon v-if="isDark"><Moon /></el-icon>
                  <el-icon v-else><Sunny /></el-icon>
                </el-button>
            </div>
            <div class="system-time">{{ currentTime }}</div>
            <div class="copyright">v0.3.0 - CYBERNETIC DIV.</div>
          </div>
        </el-aside>

        <!-- Main Workspace -->
        <el-main class="main-workspace">
          <div class="case-log-container">
            <el-scrollbar ref="scrollRef">
              <div class="case-log">
                <div v-if="chatHistory.length === 0" class="empty-state">
                  <el-empty description="NO ACTIVE INVESTIGATION">
                    <template #image>
                      <div class="neon-circle">🔍</div>
                    </template>
                    <p class="hint">Select a session or start a new investigation.</p>
                    <SuggestedQuestions @select="handleSuggestion" />
                  </el-empty>
                </div>

                <div v-for="(msg, index) in chatHistory" :key="msg.id || index" :class="['message-row', msg.role]">
                  <div class="message-card">
                    <div class="role-badge">
                      <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                      <el-icon v-else><Monitor /></el-icon>
                      {{ msg.role === 'user' ? 'AGENT' : 'OPEN-DETECTIVE' }}
                      <el-tag v-if="msg.evidence" size="small" type="success" effect="dark" class="evidence-badge">
                        EVIDENCE SECURED
                      </el-tag>
                    </div>
                    
                    <div class="content">
                      <div v-if="isRefusal(msg.content)" class="refusal-box">
                        <el-alert
                          :title="msg.content"
                          type="warning"
                          :closable="false"
                          show-icon
                        />
                      </div>
                      <div v-else v-html="renderMarkdown(msg.content)"></div>
                    </div>

                    <!-- Evidence Section -->
                    <div v-if="msg.evidence" class="evidence-section">
                      <el-divider content-position="left">INVESTIGATION LOGS</el-divider>
                      
                      <div class="evidence-content">
                        <div class="evidence-box">
                          <div class="evidence-header">
                            <el-icon><DataLine /></el-icon> Visual Reconstruction
                          </div>
                          <ResultChart :key="`chart-${index}-${msg.evidence.data.length}`" :data="msg.evidence.data" :title="msg.evidence.brief" />
                        </div>

                        <el-collapse class="secondary-evidence" v-model="msg.activeDetails">
                          <el-collapse-item title="Data Forensics (SQL & Raw)" name="details">
                            <div class="sql-block">
                              <span class="label">QUERY LOGIC:</span>
                              <pre><code class="hljs language-sql" v-html="highlightSql(msg.evidence.sql)"></code></pre>
                              <el-button size="small" circle @click="copyToClipboard(msg.evidence.sql)" class="copy-float">
                                <el-icon><CopyDocument /></el-icon>
                              </el-button>
                            </div>
                            
                            <el-table :data="msg.evidence.data" size="small" border stripe class="mini-table" max-height="250">
                              <el-table-column v-for="col in getTableColumns(msg.evidence.data)" 
                                :key="col" :prop="col" :label="col.toUpperCase()" sortable />
                            </el-table>
                          </el-collapse-item>
                        </el-collapse>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Local Loading Indicator with Thought Chain -->
                <div v-if="loading" class="message-row assistant loading-state">
                  <div class="message-card loading-card">
                    <div class="role-badge">
                      <el-icon class="is-loading"><Loading /></el-icon>
                      OPEN-DETECTIVE
                    </div>
                    <div class="thought-chain">
                      <div class="thought-step active">
                        <el-icon><Search /></el-icon> Parsing investigation request...
                      </div>
                      <div class="thought-step">
                        <el-icon><Connection /></el-icon> Accessing metric database...
                      </div>
                      <div class="thought-step">
                        <el-icon><Cpu /></el-icon> Generating relational logic...
                      </div>
                    </div>
                    <div class="loading-content">
                      <div class="scanner-line"></div>
                    </div>
                  </div>
                </div>
              </div>
            </el-scrollbar>
          </div>

          <!-- Input Area -->
          <div class="input-area">
            <div class="input-wrapper">
              <el-input
                v-model="userInput"
                placeholder="Enter project names or metric queries..."
                @keyup.enter="sendMessage"
                :disabled="loading"
                size="large"
                clearable
              >
                <template #prefix>
                  <el-icon><Connection /></el-icon>
                </template>
                <template #suffix>
                  <el-button 
                    :loading="loading" 
                    @click="sendMessage" 
                    type="primary" 
                    circle 
                    :disabled="!userInput.trim()">
                    <el-icon v-if="!loading"><Promotion /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </div>
          </div>
        </el-main>
      </el-container>

      <!-- Battle Mode Overlay -->
      <div v-if="showRadar" class="battle-overlay" @click.self="showRadar = false">
        <div class="battle-card">
          <div class="battle-header">
            <h2>{{ radarTitle }}</h2>
            <el-button circle size="small" @click="showRadar = false"><el-icon><Delete /></el-icon></el-button>
          </div>
          <RadarView :data="radarData" :title="radarTitle" />
        </div>
      </div>
      <!-- Dossier Overlay -->
      <div v-if="showDossier" class="dossier-overlay" @click.self="showDossier = false">
        <DossierCard :profile="dossierData" />
      </div>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css';
import ResultChart from './components/ResultChart.vue';
import RadarView from './components/RadarView.vue';
import DossierCard from './components/DossierCard.vue';
import SuggestedQuestions from './components/SuggestedQuestions.vue';
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus';
import { useDark, useToggle } from '@vueuse/core';
import {
  User, Monitor, Download, Refresh, Share, Moon, Sunny,
  DataLine, CopyDocument, Connection, Promotion, Delete, Aim
} from '@element-plus/icons-vue';

const isDark = useDark();
const toggleDark = useToggle(isDark);

// ...

const userInput = ref('');
const loading = ref(false);
const showRadar = ref(false);
const radarData = ref<any[]>([]);
const radarTitle = ref('');
const showDossier = ref(false);
const dossierData = ref<any>(null);
const isListening = ref(false);
const scrollRef = ref<any>(null);
const engineType = ref('sqlbot');
const currentTime = ref('');

// Session State
const sessions = ref<any[]>([]);
const currentSessionId = ref<string | null>(null);

const API_BASE = '/api/v1';

const deleteSession = async (id: string, event: Event) => {
  event.stopPropagation();
  try {
    await axios.delete(`${API_BASE}/sessions/${id}`);
    sessions.value = sessions.value.filter(s => s.id !== id);
    if (currentSessionId.value === id) {
      if (sessions.value.length > 0) loadSession(sessions.value[0].id);
      else {
        currentSessionId.value = null;
        chatHistory.value = [];
        window.history.replaceState({}, '', window.location.pathname);
      }
    }
    ElMessage.success("Session deleted");
  } catch (e) {
    ElMessage.error("Failed to delete session");
  }
};

const reloadPage = () => window.location.reload();

const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString('en-US', { hour12: false });
};

const fetchSessions = async () => {
  try {
    const res = await axios.get(`${API_BASE}/sessions`);
    sessions.value = res.data;
  } catch (e) { console.error(e); }
};

const createNewSession = async () => {
  try {
    const res = await axios.post(`${API_BASE}/sessions`);
    sessions.value.unshift(res.data);
    loadSession(res.data.id);
  } catch (e) { ElMessage.error("Failed to create session"); }
};

const loadSession = async (id: string) => {
  if (loading.value) return;
  currentSessionId.value = id;
  loading.value = true;
  chatHistory.value = []; // Clear current view
  
  try {
    const res = await axios.get(`${API_BASE}/sessions/${id}/messages`);
    // Map backend messages to frontend format
    chatHistory.value = res.data.map((m: any, idx: number) => ({
      id: idx,
      role: m.role,
      content: m.content,
      activeDetails: [],
      evidence: m.evidence_sql ? { 
        sql: m.evidence_sql, 
        data: m.evidence_data || [], 
        brief: 'Historical Data' 
      } : null
    }));
    
    nextTick(() => {
      if (scrollRef.value) scrollRef.value.setScrollTop(100000);
    });
  } catch (e) {
    ElMessage.error("Failed to load history");
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  setInterval(updateTime, 1000);
  updateTime();
  await fetchSessions();
  
  const urlParams = new URLSearchParams(window.location.search);
  const sharedSessionId = urlParams.get('session_id');
  
  if (sharedSessionId) {
    loadSession(sharedSessionId);
  } else if (sessions.value.length > 0) {
    loadSession(sessions.value[0].id);
  } else {
    createNewSession();
  }
});

const renderMarkdown = (content: string) => {
  if (!content) return '';
  // Brute force: Remove anything between { and } that looks like JSON
  let sanitized = content.replace(/\{.*?\}/gs, '');
  return md.render(sanitized.trim());
};

const isRefusal = (content: string) => {
  if (!content) return false;
  const keywords = ['无法', '抱歉', 'sorry', 'refuse', 'error', '未能识别', '没有发现'];
  // Also check if it's very short and contains no spaces (typical of raw error objects)
  return keywords.some(k => content.includes(k)) || (content.startsWith('{') && content.endsWith('}'));
};

const getTableColumns = (data: any[]) => {
  return data && data.length > 0 ? Object.keys(data[0]) : [];
};

const highlightSql = (sql: string) => {
  try {
    return hljs.highlight(sql, { language: 'sql' }).value;
  } catch (e) {
    return sql;
  }
};

const copyToClipboard = (text: string) => {
  if (!text) return;
  navigator.clipboard.writeText(text);
  ElMessage.success({ message: 'Logic copied to clipboard', grouping: true });
};

const handleSuggestion = (q: string) => {
  userInput.value = q;
  sendMessage();
};

const shareSession = () => {
  const url = `${window.location.origin}/?session_id=${currentSessionId.value}`;
  copyToClipboard(url);
  ElMessage.success("Session link copied!");
};

const sendMessage = async () => {
  const query = userInput.value.trim();
  if (!query || loading.value) return;

  // Dossier Protocol (Hijack)
  if (query.toLowerCase().startsWith('profile ')) {
      const username = query.substring(8).trim();
      if (username) {
          loading.value = true;
          try {
              const res = await axios.post(`${API_BASE}/analytics/dossier`, { username });
              dossierData.value = res.data;
              showDossier.value = true;
          } catch (e) {
              ElMessage.error("Subject not found in database.");
          } finally {
              loading.value = false;
              userInput.value = '';
          }
          return;
      }
  }

  if (!currentSessionId.value) {
    await createNewSession();
  }

  chatHistory.value.push({
    id: Date.now(),
    role: 'user', 
    content: query 
  });
  userInput.value = '';
  loading.value = true;

  // Auto-scroll to bottom
  nextTick(() => {
    if (scrollRef.value) scrollRef.value.setScrollTop(100000);
  });

  let assistantMsg: any = null;

  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query, session_id: currentSessionId.value })
    });

    if (!response.body) throw new Error("No response body");
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const json = JSON.parse(line);
          
          if (json.type === 'meta') {
             loading.value = false;
             assistantMsg = {
                id: Date.now() + 1,
                role: 'assistant',
                content: '',
                activeDetails: [],
                evidence: json.sql_query ? {
                   sql: json.sql_query,
                   data: json.data || [],
                   brief: query
                } : null
             };
             chatHistory.value.push(assistantMsg);
             if (json.error) assistantMsg.content = `**Error:** ${json.error}\n`;
          } 
          else if (json.type === 'token') {
             if (!assistantMsg) {
                 loading.value = false;
                 assistantMsg = { id: Date.now()+1, role: 'assistant', content: '', activeDetails: [], evidence: null };
                 chatHistory.value.push(assistantMsg);
             }
             assistantMsg.content += json.content;
             nextTick(() => { if (scrollRef.value) scrollRef.value.setScrollTop(100000); });
          }
        } catch (e) { console.error("Stream parse error", e); }
      }
    }
    
    if (chatHistory.value.length <= 2) fetchSessions();

  } catch (error: any) {
    loading.value = false;
    ElMessage.error(`System error: ${error.message}`);
  }
};

const openDeepScan = async () => {
  try {
    const { value } = await ElMessageBox.prompt('Enter Repository Name (e.g. vuejs/core)', 'Deep Scan Protocol', {
      confirmButtonText: 'Scan',
      cancelButtonText: 'Cancel',
      inputPattern: /.+/,
      inputErrorMessage: 'Repo name required'
    });
    
    if (value) {
      const loadingInstance = ElLoading.service({ fullscreen: true, text: 'Scanning Repositories... Analyzing Metadata...' });
      try {
        const res = await axios.post(`${API_BASE}/analytics/profile`, { repo: value });
        radarData.value = res.data.radar;
        radarTitle.value = `BATTLE MODE: ${res.data.repo}`;
        showRadar.value = true;
      } catch (e) {
        ElMessage.error("Scan Failed");
      } finally {
        loadingInstance.close();
      }
    }
  } catch {
    // Cancelled
  }
};

const exportCase = () => {
  let content = "# Open-Detective Investigation Report\n\n";
  chatHistory.value.forEach(m => {
    content += `### ${m.role.toUpperCase()}\n${m.content}\n\n`;
    if (m.evidence) {
      content += "#### Evidence Logic (SQL)\n```sql\n" + m.evidence.sql + "\n```\n\n";
    }
  });
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `investigation-session-${currentSessionId.value}.md`;
  a.click();
};
</script>

<style>
/* ... keep existing styles ... */
/* New Session List Styles */
.sidebar-sessions { flex-grow: 1; overflow: hidden; display: flex; flex-direction: column; margin-top: 20px; border-top: 1px solid #222; padding-top: 15px; }
.session-label { font-size: 0.65rem; color: #555; margin-bottom: 10px; font-weight: bold; letter-spacing: 1px; }
.session-item { 
  padding: 10px; 
  margin-bottom: 8px; 
  border-radius: 6px; 
  cursor: pointer; 
  transition: all 0.2s; 
  border: 1px solid transparent; 
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.session-info { flex-grow: 1; overflow: hidden; }
.session-item:hover { background: rgba(255,255,255,0.05); }
.session-item:hover .session-delete { opacity: 1; }
.session-item.active { background: rgba(0, 188, 212, 0.1); border-color: rgba(0, 188, 212, 0.3); }
.session-title { font-size: 0.8rem; color: #ccc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500; }
.session-date { font-size: 0.6rem; color: #666; margin-top: 4px; }
.session-delete { opacity: 0; transition: opacity 0.2s; padding: 0 !important; margin-left: 5px; }

:root {
  --sidebar-bg: #0d1117;
  --main-bg: #050505;
  --card-bg: #161b22;
  --accent-color: #00bcd4;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --border-color: #30363d;
}

body {
  margin: 0;
  background-color: var(--main-bg);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
}

.full-height { height: 100vh; }

/* Sidebar */
.sidebar { background-color: var(--sidebar-bg); border-right: 1px solid var(--border-color); padding: 20px; display: flex; flex-direction: column; }
.sidebar-header { display: flex; align-items: center; gap: 12px; margin-bottom: 40px; cursor: pointer; }
.logo { font-size: 2.2rem; }
.main-title { font-size: 1.1rem; font-weight: 800; margin: 0; color: #fff; letter-spacing: 1px; }
.sub-title { font-size: 0.65rem; color: var(--accent-color); font-weight: bold; opacity: 0.8; }
.stat-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 0.75rem; }
.sidebar-actions { display: flex; flex-direction: column; gap: 10px; flex-grow: 1; }
.action-btn { width: 100%; margin-left: 0 !important; font-size: 0.8rem; }
.sidebar-footer { font-size: 0.7rem; border-top: 1px solid var(--border-color); padding-top: 20px; }
.system-time { color: var(--accent-color); font-family: monospace; font-size: 1rem; margin-bottom: 4px; }

/* Main Area */
.main-workspace { padding: 0 !important; display: flex; flex-direction: column; background: radial-gradient(circle at center, #0a0a0a 0%, #050505 100%); }
.case-log-container { flex-grow: 1; overflow: hidden; }
.case-log { max-width: 850px; margin: 0 auto; padding: 40px 20px; }

/* Messages */
.message-row { display: flex; flex-direction: column; margin-bottom: 32px; animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.user { align-items: flex-end; }
.message-card { max-width: 90%; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 18px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); position: relative; }
.user .message-card { background: #1c2533; border-color: #3b82f6; border-left: 4px solid #3b82f6; }
.assistant .message-card { border-left: 4px solid var(--accent-color); }
.role-badge { font-size: 0.65rem; font-weight: 900; color: var(--accent-color); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; letter-spacing: 1px; }
.content { font-size: 0.95rem; color: #d1d5db; line-height: 1.6; }
.content blockquote {
  border-left: 3px solid #00bcd4;
  margin: 10px 0;
  padding: 10px 15px;
  background: rgba(0, 188, 212, 0.05);
  font-family: 'Fira Code', monospace;
  font-size: 0.85rem;
  color: #a5d6ff;
}
.content strong {
  color: #00bcd4;
  font-weight: 800;
  text-shadow: 0 0 5px rgba(0, 188, 212, 0.4);
}

/* Evidence */
.evidence-section { margin-top: 24px; padding-top: 10px; }
.evidence-box { background: rgba(0,0,0,0.3); border-radius: 6px; padding: 12px; border: 1px solid #222; margin-bottom: 12px; }
.evidence-header { font-size: 0.75rem; font-weight: 800; color: #666; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; text-transform: uppercase; }
.secondary-evidence { background: transparent !important; border: none !important; }
.el-collapse-item__header { background-color: transparent !important; color: var(--text-secondary) !important; font-size: 0.75rem !important; border-bottom: 1px solid #222 !important; }
.el-collapse-item__wrap { background-color: transparent !important; border: none !important; }

.sql-block { position: relative; background: #000; padding: 12px; border-radius: 4px; margin-bottom: 10px; border: 1px solid #333; }
.sql-block .label { font-size: 0.6rem; color: #444; font-weight: bold; position: absolute; top: 5px; left: 10px; }
.sql-block pre { margin: 15px 0 0 0; font-family: 'Fira Code', monospace; color: #a5d6ff; font-size: 0.8rem; overflow-x: auto; }
.copy-float { position: absolute; top: 8px; right: 8px; background: #111 !important; border-color: #333 !important; }

.mini-table { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: #111; font-size: 0.75rem; }
.table-info { font-size: 0.65rem; color: #555; margin-top: 6px; text-align: right; font-style: italic; }

/* Thought Chain */
.thought-chain {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.thought-step {
  font-size: 0.75rem;
  color: #444;
  display: flex;
  align-items: center;
  gap: 8px;
}
.thought-step.active {
  color: var(--accent-color);
  font-weight: bold;
}
.is-loading {
  margin-right: 5px;
}

/* Loading State */
.loading-content { display: flex; flex-direction: column; gap: 8px; padding: 10px 0; }
.loading-text { font-size: 0.75rem; color: var(--text-secondary); font-family: monospace; }
.scanner-line { height: 2px; background: var(--accent-color); width: 100%; border-radius: 2px; position: relative; overflow: hidden; }
.scanner-line::after { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, #fff, transparent); animation: scan 1.5s infinite; }
@keyframes scan { from { left: -100%; } to { left: 100%; } }

/* Input */
.input-area { padding: 30px 40px 50px; background: linear-gradient(to top, var(--main-bg) 70%, transparent); }
.input-wrapper { max-width: 850px; margin: 0 auto; }
.el-input__wrapper { background-color: #161b22 !important; box-shadow: 0 0 0 0 1px #30363d inset !important; border-radius: 12px !important; }
.el-input__inner { color: #fff !important; }

/* Empty state */
.neon-circle { font-size: 3.5rem; filter: drop-shadow(0 0 15px var(--accent-color)); margin-bottom: 20px; text-align: center; }

/* Global Scrollbar Styling */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--main-bg); }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-color); }

/* Interactive Elements */
.message-card { 
  max-width: 90%; 
  background: var(--card-bg); 
  border: 1px solid var(--border-color); 
  border-radius: 8px; 
  padding: 18px; 
  box-shadow: 0 8px 24px rgba(0,0,0,0.5); 
  position: relative;
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.message-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(0, 188, 212, 0.15);
  border-color: rgba(0, 188, 212, 0.5);
}

/* Battle Mode */
.battle-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(5px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s;
}
.battle-card {
  width: 600px;
  background: #111;
  border: 2px solid #00bcd4;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 0 50px rgba(0, 188, 212, 0.3);
  position: relative;
}
.battle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #333;
  padding-bottom: 10px;
}
.battle-header h2 {
  color: #00bcd4;
  margin: 0;
  font-size: 1.2rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  text-shadow: 0 0 10px rgba(0, 188, 212, 0.5);
}

.dossier-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(8px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.5s;
}
</style>