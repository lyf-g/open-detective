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
            <el-button class="action-btn" type="primary" plain @click="exportCase" :disabled="chatHistory.length === 0">
              <el-icon><Download /></el-icon> Export Case File
            </el-button>
            <el-button class="action-btn" @click="reloadPage">
              <el-icon><Refresh /></el-icon> New Investigation
            </el-button>
          </div>

          <div class="sidebar-footer">
            <div class="system-time">{{ currentTime }}</div>
            <div class="copyright">v0.2.2 - CYBERNETIC DIV.</div>
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
                    <p class="hint">Ask about repository trends, comparisons, or metric rankings.</p>
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
                    
                    <div class="content" v-html="renderMarkdown(msg.content)"></div>

                    <!-- Evidence Section -->
                    <div v-if="msg.evidence" class="evidence-section">
                      <el-divider content-position="left">INVESTIGATION LOGS</el-divider>
                      
                      <div class="evidence-content">
                        <div class="evidence-box">
                          <div class="evidence-header">
                            <el-icon><DataLine /></el-icon> Visual Reconstruction
                          </div>
                          <!-- Use a unique key based on message index and data length to force re-render -->
                          <ResultChart :key="`chart-${index}-${msg.evidence.data.length}`" :data="msg.evidence.data" :title="msg.evidence.brief" />
                        </div>

                        <el-collapse class="secondary-evidence" v-model="msg.activeDetails">
                          <el-collapse-item title="Data Forensics (SQL & Raw)" name="details">
                            <div class="sql-block">
                              <span class="label">QUERY LOGIC:</span>
                              <pre><code>{{ msg.evidence.sql }}</code></pre>
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
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import MarkdownIt from 'markdown-it';
import ResultChart from './components/ResultChart.vue';
import { ElMessage } from 'element-plus';
import { 
  User, Monitor, Download, Refresh, 
  DataLine, CopyDocument, Connection, Promotion 
} from '@element-plus/icons-vue';

const md = new MarkdownIt();
const userInput = ref('');
const loading = ref(false);
const chatHistory = ref<any[]>([]);
const scrollRef = ref<any>(null);
const engineType = ref('sqlbot');
const currentTime = ref('');

const API_BASE = '/api/v1';

const reloadPage = () => window.location.reload();

const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString('en-US', { hour12: false });
};

onMounted(() => {
  setInterval(updateTime, 1000);
  updateTime();
});

const renderMarkdown = (content: string) => md.render(content || '');

const getTableColumns = (data: any[]) => {
  return data && data.length > 0 ? Object.keys(data[0]) : [];
};

const copyToClipboard = (text: string) => {
  if (!text) return;
  navigator.clipboard.writeText(text);
  ElMessage.success({ message: 'Logic copied to clipboard', grouping: true });
};

const sendMessage = async () => {
  const query = userInput.value.trim();
  if (!query || loading.value) return;

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

  try {
    const res = await axios.post(`${API_BASE}/chat`, { message: query });
    const { answer, sql, data, brief } = res.data;

    chatHistory.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: answer || 'Investigation concluded.',
      activeDetails: [], // Individual state for collapse
      evidence: sql ? { sql, data: data || [], brief: brief || query } : null
    });
    
    nextTick(() => {
      if (scrollRef.value) scrollRef.value.setScrollTop(100000);
    });
  } catch (error: any) {
    ElMessage.error(`System error during analysis: ${error.response?.data?.detail || 'Offline'}`);
  } finally {
    loading.value = false;
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
  a.download = `investigation-file-${Date.now()}.md`;
  a.click();
};
</script>

<style>
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
</style>