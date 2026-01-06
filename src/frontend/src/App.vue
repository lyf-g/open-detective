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
            <div class="copyright">v0.2.1 - CYBERNETIC DIV.</div>
          </div>
        </el-aside>

        <!-- Main Workspace -->
        <el-main class="main-workspace" v-loading="loading" element-loading-background="rgba(0, 0, 0, 0.7)" element-loading-text="Analyzing Data Streams...">
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

                <div v-for="(msg, index) in chatHistory" :key="index" :class="['message-row', msg.role]">
                  <div class="message-card">
                    <div class="role-badge">
                      <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                      <el-icon v-else><Monitor /></el-icon>
                      {{ msg.role === 'user' ? 'AGENT' : 'DETECTIVE AI' }}
                    </div>
                    
                    <div class="content" v-html="renderMarkdown(msg.content)"></div>

                    <!-- Evidence Section -->
                    <div v-if="msg.evidence" class="evidence-section">
                      <el-divider content-position="left">CASE EVIDENCE</el-divider>
                      
                      <div class="evidence-tabs">
                        <el-collapse v-model="activeEvidence">
                          <el-collapse-item name="visual" title="Visual Reconstruction">
                            <ResultChart :data="msg.evidence.data" :title="msg.evidence.brief" />
                          </el-collapse-item>
                          
                          <el-collapse-item name="sql" title="Query Logic (SQL)">
                            <div class="sql-code">
                              <pre><code>{{ msg.evidence.sql }}</code></pre>
                              <el-button size="small" link class="copy-btn" @click="copyToClipboard(msg.evidence.sql)">
                                <el-icon><CopyDocument /></el-icon> Copy
                              </el-button>
                            </div>
                          </el-collapse-item>

                          <el-collapse-item name="raw" title="Raw Data Records">
                            <el-table :data="msg.evidence.data.slice(0, 10)" size="small" border stripe class="evidence-table">
                              <el-table-column v-for="col in getTableColumns(msg.evidence.data)" 
                                :key="col" :prop="col" :label="col.toUpperCase()" />
                            </el-table>
                            <div v-if="msg.evidence.data.length > 10" class="table-footer">
                              Showing 10 of {{ msg.evidence.data.length }} records
                            </div>
                          </el-collapse-item>
                        </el-collapse>
                      </div>
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
                    :disabled="!userInput.trim()"
                  >
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
const loading = ref(false); // Fix: Initialized as boolean
const chatHistory = ref<any[]>([]);
const scrollRef = ref<any>(null);
const activeEvidence = ref(['visual']);
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
  ElMessage.success('Copied to clipboard');
};

const sendMessage = async () => {
  const query = userInput.value.trim();
  if (!query || loading.value) return;

  console.log("🚀 Starting Investigation:", query);
  chatHistory.value.push({ role: 'user', content: query });
  userInput.value = '';
  loading.value = true;

  try {
    const res = await axios.post(`${API_BASE}/chat`, { message: query });
    console.log("✅ Received Response:", res.data);
    const { answer, sql, data, brief } = res.data;

    chatHistory.value.push({
      role: 'assistant',
      content: answer || 'Analysis complete.',
      evidence: sql ? { sql, data: data || [], brief: brief || query } : null
    });
    
    nextTick(() => {
      if (scrollRef.value) {
        scrollRef.value.setScrollTop(100000);
      }
    });
  } catch (error: any) {
    console.error("❌ Investigation failed:", error);
    ElMessage.error(`Investigation failed: ${error.response?.data?.detail || 'Network error'}`);
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
  a.download = `case-report-${Date.now()}.md`;
  a.click();
};
</script>

<style>
/* Existing CSS remains same, ensuring high quality dark theme */
:root {
  --sidebar-bg: #0d1117;
  --main-bg: #0a0a0a;
  --accent-color: #00bcd4;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --border-color: #30363d;
}

body {
  margin: 0;
  background-color: var(--main-bg);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
}

.full-height { height: 100vh; }

/* Sidebar Styling */
.sidebar {
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
  cursor: pointer;
}

.logo { font-size: 2.5rem; }
.main-title { font-size: 1.2rem; font-weight: 800; margin: 0; color: #fff; letter-spacing: 1px; }
.sub-title { font-size: 0.7rem; color: var(--accent-color); font-weight: bold; }

.sidebar-stats { margin-bottom: 30px; }
.stat-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 0.8rem; }
.stat-item .label { color: var(--text-secondary); font-weight: bold; }

.sidebar-actions { display: flex; flex-direction: column; gap: 12px; flex-grow: 1; }
.action-btn { width: 100%; margin-left: 0 !important; }

.sidebar-footer { font-size: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 20px; }
.system-time { color: var(--accent-color); font-family: monospace; font-size: 1.1rem; margin-bottom: 5px; }
.copyright { color: #444; }

/* Workspace Styling */
.main-workspace {
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--main-bg);
}

.case-log-container {
  flex-grow: 1;
  overflow: hidden;
}

.case-log {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* Message Rows */
.message-row { display: flex; flex-direction: column; margin-bottom: 30px; }
.user { align-items: flex-end; }
.assistant { align-items: flex-start; }

.message-card {
  max-width: 85%;
  background: #161b22;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.user .message-card {
  background: #1f2937;
  border-color: #3b82f6;
}

.role-badge {
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--accent-color);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 5px;
  text-transform: uppercase;
}

.content { line-height: 1.6; font-size: 0.95rem; }
.content p { margin: 0 0 10px 0; }

/* Evidence Styling */
.evidence-section { margin-top: 20px; }
.el-divider__text { background-color: transparent !important; color: #555 !important; font-size: 0.7rem; font-weight: bold; }

.sql-code {
  position: relative;
  background: #000;
  padding: 15px;
  border-radius: 6px;
  font-family: 'Fira Code', monospace;
  font-size: 0.85rem;
}
.sql-code pre { margin: 0; white-space: pre-wrap; color: #7ee787; }
.copy-btn { position: absolute; top: 10px; right: 10px; }

.evidence-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: #1a1a1a;
  font-size: 0.8rem;
}

.table-footer { font-size: 0.75rem; color: #555; margin-top: 8px; text-align: center; }

/* Input Area */
.input-area {
  padding: 20px 40px 40px;
  background: linear-gradient(to top, var(--main-bg) 80%, transparent);
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.el-input__wrapper {
  background-color: #161b22 !important;
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

.el-input__inner { color: #fff !important; }

/* Empty state */
.neon-circle {
  font-size: 4rem;
  text-shadow: 0 0 20px var(--accent-color);
  margin-bottom: 20px;
  text-align: center;
}
.hint { color: var(--text-secondary); text-align: center; font-size: 0.9rem; }
</style>