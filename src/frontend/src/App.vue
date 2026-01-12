<template>
  <el-config-provider :button="{ autoInsertSpace: true }">
    <div class="detective-app">
      <!-- Global Situational Awareness Ticker (PPT Highlight 3) -->
      <div class="global-ticker">
        <div class="ticker-content">
          <span v-for="(item, i) in tickerItems" :key="i" :class="['ticker-item', item.type]">
            <el-icon><Warning v-if="item.type === 'alert'" /><InfoFilled v-else /></el-icon>
            {{ item.msg }}
          </span>
           <!-- Duplicate for seamless loop -->
           <span v-for="(item, i) in tickerItems" :key="`dup-${i}`" :class="['ticker-item', item.type]">
            <el-icon><Warning v-if="item.type === 'alert'" /><InfoFilled v-else /></el-icon>
            {{ item.msg }}
          </span>
        </div>
      </div>

      <el-container class="full-height">
        <!-- Sidebar -->
        <el-aside width="280px" class="sidebar">
          <div class="sidebar-header" @click="reloadPage">
            <span class="logo">🕵️‍♂️</span>
            <div class="title-group">
              <h1 class="main-title">{{ t('app.title') }}</h1>
              <span class="sub-title">{{ t('app.subtitle') }}</span>
            </div>
          </div>

          <div class="sidebar-stats" @click="showSystemMonitor = true" style="cursor: pointer">
            <div class="stat-item">
              <span class="label">{{ t('sidebar.engine') }}:</span>
              <el-tag size="small" :type="sqlbotStatus === 'reachable' ? 'success' : 'danger'">{{ engineType.toUpperCase() }}</el-tag>
            </div>
            <div class="stat-item">
              <span class="label">{{ t('sidebar.db') }}:</span>
              <el-tag size="small" :type="dbStatus ? 'success' : 'danger'" effect="dark">{{ dbStatus ? 'ONLINE' : 'OFFLINE' }}</el-tag>
            </div>
          </div>

          <div class="sidebar-actions">
            <el-button class="action-btn" type="danger" plain @click="openDeepScan">
              <el-icon><Aim /></el-icon> {{ t('sidebar.deep_scan') }}
            </el-button>
            <el-button class="action-btn" type="success" plain @click="showGlobe = true">
              <el-icon><MapLocation /></el-icon> {{ t('sidebar.global_intel') }}
            </el-button>
            <el-button class="action-btn" type="warning" plain @click="openSentiment">
              <el-icon><ChatDotRound /></el-icon> {{ t('sidebar.sentiment') }}
            </el-button>
            <el-button class="action-btn" type="primary" plain @click="exportCase" :disabled="chatHistory.length === 0">
              <el-icon><Download /></el-icon> {{ t('sidebar.export') }}
            </el-button>
            <el-button class="action-btn" type="primary" plain @click="shareSession" :disabled="!currentSessionId">
              <el-icon><Share /></el-icon> {{ t('sidebar.share') }}
            </el-button>
            <el-button class="action-btn" @click="createNewSession">
              <el-icon><Refresh /></el-icon> {{ t('sidebar.new') }}
            </el-button>
          </div>

          <div class="sidebar-sessions">
            <div class="session-label">{{ t('sidebar.history') }}</div>
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
            <div class="theme-switch" style="margin-bottom: 10px; text-align: center; display: flex; justify-content: center; gap: 10px;">
                <el-button circle size="small" @click="toggleDark()">
                  <el-icon v-if="isDark"><Moon /></el-icon>
                  <el-icon v-else><Sunny /></el-icon>
                </el-button>
                <el-button circle size="small" @click="toggleLanguage()">
                  <span style="font-size: 10px; font-weight: bold;">{{ locale.toUpperCase() }}</span>
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

                    <!-- Visualized Chain of Thought (PPT Highlight 1) -->
                    <div v-if="msg.role === 'assistant' && msg.evidence" class="thought-process" style="margin-bottom: 15px;">
                      <el-collapse>
                        <el-collapse-item name="1">
                          <template #title>
                            <span style="color: #00bcd4; font-weight: bold; display: flex; align-items: center; gap: 8px;">
                              <el-icon><Cpu /></el-icon> NEURAL LOGIC PATH
                            </span>
                          </template>
                          <div style="padding: 10px;">
                            <el-timeline>
                              <el-timeline-item timestamp="0.12s" type="success" placement="top">
                                <span style="color: #ccc">Semantic Parsing (Intent: <span style="color: #fff">Data Retrieval</span>)</span>
                              </el-timeline-item>
                              <el-timeline-item timestamp="0.45s" type="success" placement="top">
                                <span style="color: #ccc">Schema Linking (Mapped: <span style="color: #e6a23c">open_digger_metrics</span>)</span>
                              </el-timeline-item>
                              <el-timeline-item timestamp="1.10s" type="primary" placement="top">
                                <span style="color: #ccc">SQL Generation (Dialect: <span style="color: #409eff">MySQL 8.0</span>)</span>
                              </el-timeline-item>
                              <el-timeline-item timestamp="1.35s" type="warning" placement="top">
                                <span style="color: #ccc">Visual Rendering (Engine: <span style="color: #f56c6c">ECharts Gl</span>)</span>
                              </el-timeline-item>
                            </el-timeline>
                          </div>
                        </el-collapse-item>
                      </el-collapse>
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

      <!-- Globe Overlay -->
      <div v-if="showGlobe" class="battle-overlay" @click.self="showGlobe = false">
        <div class="battle-card" style="width: 800px; height: 700px;">
          <div class="battle-header">
            <h2>GLOBAL INTELLIGENCE</h2>
            <el-button circle size="small" @click="showGlobe = false"><el-icon><Delete /></el-icon></el-button>
          </div>
          <GlobeView />
        </div>
      </div>

      <!-- Sentiment Overlay -->
      <div v-if="showSentiment" class="battle-overlay" @click.self="showSentiment = false">
        <div class="battle-card" style="width: 800px; height: 400px;">
          <div class="battle-header">
            <h2>COMMUNITY SENTIMENT: {{ sentimentData?.repo }}</h2>
            <el-button circle size="small" @click="showSentiment = false"><el-icon><Delete /></el-icon></el-button>
          </div>
          <SentimentView v-if="sentimentData" :data="sentimentData" />
        </div>
      </div>

      <!-- System Monitor Overlay -->
      <div v-if="showSystemMonitor" class="battle-overlay" @click.self="showSystemMonitor = false">
        <div class="battle-card" style="width: 500px;">
          <div class="battle-header">
            <h2>SYSTEM DIAGNOSTICS</h2>
            <el-button circle size="small" @click="showSystemMonitor = false"><el-icon><Delete /></el-icon></el-button>
          </div>
          <div style="padding: 10px; color: #ccc;">
            <h3>MySQL Database</h3>
            <p>Status: <span :style="{color: dbStatus ? '#67c23a' : '#f56c6c'}">{{ dbStatus ? 'CONNECTED' : 'DISCONNECTED' }}</span></p>
            <p v-if="systemDetails.db?.details">Pool: {{ systemDetails.db.details.size }} (Free: {{ systemDetails.db.details.free }})</p>
            
            <el-divider />
            
            <h3>SQLBot Engine</h3>
            <p>Endpoint: {{ systemDetails.sqlbot?.status }}</p>
            <p v-if="systemDetails.sqlbot?.code">Response Code: {{ systemDetails.sqlbot.code }}</p>
          </div>
        </div>
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
import GlobeView from './components/GlobeView.vue';
import SentimentView from './components/SentimentView.vue';
import SuggestedQuestions from './components/SuggestedQuestions.vue';
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus';
import { useDark, useToggle } from '@vueuse/core';
import { 
  User, Monitor, Download, Refresh, Share, Moon, Sunny,
  DataLine, CopyDocument, Connection, Promotion, Delete, Aim, Microphone, MapLocation, ChatDotRound, Loading, Search, Cpu, Switch, Warning, InfoFilled
} from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n();
const isDark = useDark();
const toggleDark = useToggle(isDark);

const tickerItems = ref([
  { type: 'alert', msg: '[ALERT] React: Issue backlog critical (+15% DoD)' },
  { type: 'info', msg: 'Vue.js: 3.4.0 release adoption rate > 80%' },
  { type: 'warn', msg: '[WARN] TensorFlow: Bus Factor dropping (Risk Level 3)' },
  { type: 'alert', msg: '[ALERT] Kubernetes: Unusual commit velocity detected' },
  { type: 'info', msg: 'OpenAI: Star history anomaly normalized' },
  { type: 'warn', msg: '[WARN] Deno: Maintainer activity low' }
]);

const toggleLanguage = () => {
  locale.value = locale.value === 'en' ? 'zh' : 'en';
};

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang, ignoreIllegals: true }).value;
      } catch (__error) {}
    }
    return '';
  }
});

const userInput = ref('');
const loading = ref(false);
const chatHistory = ref<any[]>([]);
const showRadar = ref(false);
const radarData = ref<any[]>([]);
const radarTitle = ref('');
const showDossier = ref(false);
const dossierData = ref<any>(null);
const showGlobe = ref(false);
const showSentiment = ref(false);
const sentimentData = ref<any>(null);
const isListening = ref(false);
const scrollRef = ref<any>(null);
const engineType = ref('sqlbot');
const currentTime = ref('');
const dbStatus = ref(false);
const sqlbotStatus = ref('checking');
const systemDetails = ref<any>({});
const showSystemMonitor = ref(false);

const checkSystemHealth = async () => {
  try {
    const health = await axios.get(`${API_BASE}/health`);
    dbStatus.value = health.data.db_connected;
    systemDetails.value.db = health.data;
    
    const sb = await axios.get(`${API_BASE}/sqlbot-health`);
    sqlbotStatus.value = sb.data.status;
    systemDetails.value.sqlbot = sb.data;
  } catch (e) {
    dbStatus.value = false;
    sqlbotStatus.value = 'error';
  }
};

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
  chatHistory.value = [];
  
  try {
    const res = await axios.get(`${API_BASE}/sessions/${id}/messages`);
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
  checkSystemHealth();
  setInterval(checkSystemHealth, 30000);
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
  let sanitized = content.replace(/\{.*?\}/gs, '');
  return md.render(sanitized.trim());
};

const isRefusal = (content: string) => {
  if (!content) return false;
  const keywords = ['无法', '抱歉', 'sorry', 'refuse', 'error', '未能识别', '没有发现'];
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

const openSentiment = async () => {
  try {
    const { value } = await ElMessageBox.prompt('Enter Repository Name', 'Sentiment Analysis', {
      confirmButtonText: 'Analyze',
      cancelButtonText: 'Cancel'
    });
    if (value) {
      const loadingInstance = ElLoading.service({ fullscreen: true, text: 'Mining Community Data...' });
      try {
        const res = await axios.post(`${API_BASE}/analytics/sentiment`, { repo: value });
        sentimentData.value = res.data;
        showSentiment.value = true;
      } catch (e) {
        ElMessage.error("Analysis Failed");
      } finally {
        loadingInstance.close();
      }
    }
  } catch {}
};

const openDeepScan = async () => {
  try {
    const { value } = await ElMessageBox.prompt('Enter Repository Name', 'Deep Scan Protocol', {
      confirmButtonText: 'Scan',
      cancelButtonText: 'Cancel'
    });
    if (value) {
      const loadingInstance = ElLoading.service({ fullscreen: true, text: 'Scanning Repositories...' });
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
  } catch {}
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
.sidebar-sessions { flex-grow: 1; overflow: hidden; display: flex; flex-direction: column; margin-top: 20px; border-top: 1px solid #222; padding-top: 15px; }
.session-label { font-size: 0.65rem; color: #555; margin-bottom: 10px; font-weight: bold; letter-spacing: 1px; }
.session-item { padding: 10px; margin-bottom: 8px; border-radius: 6px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; display: flex; justify-content: space-between; align-items: center; }
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

.full-height { height: calc(100vh - 30px); }
.sidebar { background-color: var(--sidebar-bg); border-right: 1px solid var(--border-color); padding: 20px; display: flex; flex-direction: column; }

/* Ticker Styles */
.global-ticker {
  height: 30px;
  background: #111;
  border-bottom: 1px solid #00bcd4;
  overflow: hidden;
  display: flex;
  align-items: center;
  position: relative;
  z-index: 100;
}
.ticker-content {
  display: flex;
  white-space: nowrap;
  animation: ticker-scroll 30s linear infinite;
}
.ticker-item {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-right: 50px;
  font-size: 0.8rem;
  font-family: 'Share Tech Mono', monospace;
}
.ticker-item.alert { color: #f56c6c; font-weight: bold; text-shadow: 0 0 5px red; }
.ticker-item.warn { color: #e6a23c; }
.ticker-item.info { color: #00bcd4; }

@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.sidebar-header { display: flex; align-items: center; gap: 12px; margin-bottom: 40px; cursor: pointer; }
.logo { font-size: 2.2rem; }
.main-title { font-size: 1.1rem; font-weight: 800; margin: 0; color: #fff; letter-spacing: 1px; }
.sub-title { font-size: 0.65rem; color: var(--accent-color); font-weight: bold; opacity: 0.8; }
.stat-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 0.75rem; }
.sidebar-actions { display: flex; flex-direction: column; gap: 10px; flex-grow: 1; }
.action-btn { width: 100%; margin-left: 0 !important; font-size: 0.8rem; }
.sidebar-footer { font-size: 0.7rem; border-top: 1px solid var(--border-color); padding-top: 20px; }
.system-time { color: var(--accent-color); font-family: monospace; font-size: 1rem; margin-bottom: 4px; }

.main-workspace { padding: 0 !important; display: flex; flex-direction: column; background: radial-gradient(circle at center, #0a0a0a 0%, #050505 100%); }
.case-log-container { flex-grow: 1; overflow: hidden; }
.case-log { max-width: 850px; margin: 0 auto; padding: 40px 20px; }

.message-row { display: flex; flex-direction: column; margin-bottom: 32px; animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.user { align-items: flex-end; }
.message-card { max-width: 90%; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 18px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); position: relative; }
.user .message-card { background: #1c2533; border-color: #3b82f6; border-left: 4px solid #3b82f6; }
.assistant .message-card { border-left: 4px solid var(--accent-color); }
.role-badge { font-size: 0.65rem; font-weight: 900; color: var(--accent-color); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; letter-spacing: 1px; }
.content { font-size: 0.95rem; color: #d1d5db; line-height: 1.6; }
.content blockquote { border-left: 3px solid #00bcd4; margin: 10px 0; padding: 10px 15px; background: rgba(0, 188, 212, 0.05); font-family: 'Fira Code', monospace; font-size: 0.85rem; color: #a5d6ff; }
.content strong { color: #00bcd4; font-weight: 800; text-shadow: 0 0 5px rgba(0, 188, 212, 0.4); }

.evidence-section { margin-top: 24px; padding-top: 10px; }
.evidence-box { background: rgba(0,0,0,0.3); border-radius: 6px; padding: 12px; border: 1px solid #222; margin-bottom: 12px; }
.evidence-header { font-size: 0.75rem; font-weight: 800; color: #666; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; text-transform: uppercase; }
.sql-block { position: relative; background: #000; padding: 12px; border-radius: 4px; margin-bottom: 10px; border: 1px solid #333; }
.sql-block pre { margin: 15px 0 0 0; font-family: 'Fira Code', monospace; color: #a5d6ff; font-size: 0.8rem; overflow-x: auto; }
.mini-table { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: #111; font-size: 0.75rem; }

.thought-chain { margin-bottom: 15px; display: flex; flex-direction: column; gap: 8px; }
.thought-step { font-size: 0.75rem; color: #444; display: flex; align-items: center; gap: 8px; }
.thought-step.active { color: var(--accent-color); font-weight: bold; }
.scanner-line { height: 2px; background: var(--accent-color); width: 100%; border-radius: 2px; position: relative; overflow: hidden; }
.scanner-line::after { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, #fff, transparent); animation: scan 1.5s infinite; }
@keyframes scan { from { left: -100%; } to { left: 100%; } }

.input-area { padding: 30px 40px 50px; background: linear-gradient(to top, var(--main-bg) 70%, transparent); }
.input-wrapper { max-width: 850px; margin: 0 auto; }
.el-input__wrapper { background-color: #161b22 !important; box-shadow: 0 0 0 0 1px #30363d inset !important; border-radius: 12px !important; }
.el-input__inner { color: #fff !important; }

.battle-overlay, .dossier-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(5px); z-index: 9999; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.3s; }
.battle-card { width: 600px; background: #111; border: 2px solid #00bcd4; border-radius: 12px; padding: 20px; box-shadow: 0 0 50px rgba(0, 188, 212, 0.3); position: relative; }
.battle-header h2 { color: #00bcd4; margin: 0; font-size: 1.2rem; letter-spacing: 2px; text-transform: uppercase; text-shadow: 0 0 10px rgba(0, 188, 212, 0.5); }
</style>