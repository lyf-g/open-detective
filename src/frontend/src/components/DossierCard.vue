<template>
  <div class="dossier-overlay">
    <div class="dossier-card">
      <!-- Header -->
      <div class="card-header">
        <div class="header-left">
          <div class="avatar">
            <el-icon :size="40"><User /></el-icon>
          </div>
          <div class="identity">
            <h1 class="name">{{ profile.username }}</h1>
            <div class="alias">ALIAS: {{ profile.codename }}</div>
          </div>
        </div>
        <div class="header-right">
          <div class="risk-badge" :class="getRiskClass(profile.risk_score)">
            <span class="risk-label">RISK SCORE</span>
            <span class="risk-val">{{ profile.risk_score }}</span>
          </div>
        </div>
      </div>

      <!-- Body -->
      <div class="card-body">
        <!-- Col 1: Radar Visualization -->
        <div class="col-visual">
          <div class="chart-title">RISK TOPOLOGY</div>
          <div class="radar-wrapper">
            <v-chart class="radar-chart" :option="radarOption" autoresize />
          </div>
        </div>

        <!-- Col 2: Metrics & Intel -->
        <div class="col-intel">
          <div class="section-title">
            <el-icon><DataLine /></el-icon> KEY METRICS
          </div>
          <div class="metrics-grid">
            <div class="metric-item" v-for="m in profile.metrics" :key="m.name">
              <div class="m-label">{{ m.name }}</div>
              <el-progress 
                :percentage="m.value" 
                :color="customColors" 
                :stroke-width="8" 
                :show-text="true"
              />
            </div>
          </div>

          <div class="section-title" style="margin-top: 20px;">
            <el-icon><Warning /></el-icon> RECENT INCIDENTS
          </div>
          <ul class="incident-list">
            <li v-for="(inc, i) in profile.incidents" :key="i">
              <span class="inc-time">[{{ inc.date }}]</span> {{ inc.desc }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Footer: AI Verdict -->
      <div class="card-footer">
        <div class="ai-verdict">
          <span class="verdict-label">AI VERDICT:</span>
          <span class="verdict-text">{{ profile.recommendation }}</span>
        </div>
        <div class="stamp-verified">VERIFIED</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { User, DataLine, Warning } from '@element-plus/icons-vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { RadarChart } from 'echarts/charts';
import { TitleComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, RadarChart, TitleComponent, LegendComponent]);

const props = defineProps<{
  profile: any; // { username, codename, risk_score, risk_dimensions[], metrics[], incidents[], recommendation }
}>();

const customColors = [
  { color: '#67c23a', percentage: 40 },
  { color: '#e6a23c', percentage: 70 },
  { color: '#f56c6c', percentage: 100 },
];

const getRiskClass = (score: number) => {
  if (score >= 80) return 'critical';
  if (score >= 50) return 'warning';
  return 'safe';
};

const radarOption = computed(() => ({
  backgroundColor: 'transparent',
  radar: {
    indicator: props.profile.risk_dimensions.map((d: any) => ({ name: d.name, max: 100 })),
    center: ['50%', '55%'],
    radius: '70%',
    splitNumber: 4,
    axisName: { color: '#00bcd4', fontSize: 10, fontWeight: 'bold' },
    splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
    splitArea: { 
        show: true,
        areaStyle: {
            color: ['rgba(0, 188, 212, 0.05)', 'transparent']
        }
    },
    axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } }
  },
  series: [{
    type: 'radar',
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 2, color: '#00bcd4' },
    areaStyle: { color: 'rgba(0, 188, 212, 0.4)' },
    data: [{ value: props.profile.risk_dimensions.map((d: any) => d.value) }]
  }]
}));
</script>

<style scoped>
.dossier-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(8px);
  z-index: 9999; display: flex; align-items: center; justify-content: center;
}

.dossier-card {
  width: 850px;
  background: #0f1319;
  border: 1px solid #333;
  border-top: 4px solid #00bcd4;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 188, 212, 0.2);
  display: flex; flex-direction: column;
  font-family: 'Inter', system-ui, sans-serif;
  color: #e6edf3;
  position: relative;
  overflow: hidden;
}

/* Header */
.card-header {
  padding: 25px 30px;
  border-bottom: 1px solid #222;
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(90deg, rgba(0,188,212,0.05) 0%, transparent 100%);
}
.header-left { display: flex; align-items: center; gap: 20px; }
.avatar {
  width: 60px; height: 60px; background: #1c2128; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; border: 2px solid #333; color: #555;
}
.identity .name { margin: 0; font-size: 1.8rem; font-weight: 800; letter-spacing: 1px; color: #fff; }
.identity .alias { font-size: 0.8rem; color: #00bcd4; font-family: monospace; letter-spacing: 2px; }

.risk-badge {
  text-align: right; border: 2px solid #333; padding: 5px 15px; border-radius: 6px;
  display: flex; flex-direction: column; align-items: flex-end;
}
.risk-badge.critical { border-color: #f56c6c; color: #f56c6c; background: rgba(245, 108, 108, 0.1); }
.risk-badge.warning { border-color: #e6a23c; color: #e6a23c; }
.risk-badge.safe { border-color: #67c23a; color: #67c23a; }
.risk-label { font-size: 0.6rem; font-weight: bold; opacity: 0.8; }
.risk-val { font-size: 1.8rem; font-weight: 900; line-height: 1; }

/* Body */
.card-body { display: flex; padding: 30px; gap: 40px; min-height: 350px; }
.col-visual { flex: 1; display: flex; flex-direction: column; }
.col-intel { flex: 1.2; }

.chart-title, .section-title {
  font-size: 0.75rem; color: #8b949e; font-weight: bold; letter-spacing: 1px; margin-bottom: 15px;
  display: flex; align-items: center; gap: 8px;
}
.radar-wrapper { flex-grow: 1; position: relative; }
.radar-chart { width: 100%; height: 300px; }

.metric-item { margin-bottom: 12px; }
.m-label { font-size: 0.75rem; margin-bottom: 4px; color: #ccc; }

.incident-list { list-style: none; padding: 0; margin: 0; font-size: 0.8rem; color: #aaa; }
.incident-list li { margin-bottom: 8px; border-left: 2px solid #333; padding-left: 10px; }
.inc-time { color: #00bcd4; font-family: monospace; margin-right: 5px; }

/* Footer */
.card-footer {
  background: #161b22; padding: 15px 30px; border-top: 1px solid #222;
  display: flex; justify-content: space-between; align-items: center;
}
.ai-verdict { font-size: 0.9rem; }
.verdict-label { color: #00bcd4; font-weight: bold; margin-right: 10px; }
.verdict-text { color: #fff; font-style: italic; }

.stamp-verified {
  border: 2px solid #67c23a; color: #67c23a; font-weight: bold; padding: 2px 10px;
  transform: rotate(-5deg); font-size: 0.8rem; letter-spacing: 2px; opacity: 0.8;
}
</style>