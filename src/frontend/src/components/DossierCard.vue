<template>
  <div class="dossier-container">
    <div class="scan-line"></div>
    <div class="corner tl"></div><div class="corner tr"></div>
    <div class="corner bl"></div><div class="corner br"></div>
    
    <div class="stamp">TOP SECRET // CLASSIFIED</div>
    
    <div class="dossier-content-wrapper">
      <!-- Left Column: Identity & Radar -->
      <div class="col-left">
        <div class="photo-frame">
          <div class="avatar-placeholder">
            <el-icon :size="50"><User /></el-icon>
          </div>
          <div class="id-number">ID: {{ Math.floor(Math.random() * 1000000).toString().padStart(6, '0') }}</div>
        </div>
        
        <div class="radar-box">
          <v-chart class="mini-chart" :option="radarOption" autoresize />
        </div>
      </div>
      
      <!-- Right Column: Intel -->
      <div class="col-right">
        <div class="header-info">
          <h1 class="glitch-text" :data-text="profile.username">SUBJECT: {{ profile.username }}</h1>
          <div class="codename">CODENAME: {{ profile.codename }}</div>
          <div class="threat-box">
            <span>THREAT LEVEL</span>
            <span :class="['threat-val', getThreatClass(profile.threat_level)]">{{ profile.threat_level }}</span>
          </div>
        </div>
        
        <div class="section">
          <h3><el-icon><Reading /></el-icon> PSYCHOLOGICAL PROFILE</h3>
          <p class="typewriter">{{ profile.psych_profile }}</p>
        </div>
        
        <div class="section tech-stats">
          <div class="stat-row">
            <span class="label">CONTRIBUTION RATE</span>
            <div class="tech-bar"><div class="fill" style="width: 87%"></div></div>
          </div>
          <div class="stat-row">
            <span class="label">INFLUENCE</span>
            <div class="tech-bar"><div class="fill" style="width: 65%"></div></div>
          </div>
        </div>
        
        <div class="status-footer">
          CURRENT STATUS: <span class="blink">{{ profile.status }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { User, Reading } from '@element-plus/icons-vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { RadarChart } from 'echarts/charts';
import { TitleComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, RadarChart, TitleComponent, LegendComponent]);

const props = defineProps<{
  profile: any;
}>();

const radarOption = computed(() => ({
  backgroundColor: 'transparent',
  radar: {
    indicator: props.profile.skills.map((s: any) => ({ name: s.name, max: 100 })),
    splitNumber: 3,
    axisName: { color: '#00bcd4', fontSize: 10 },
    splitLine: { lineStyle: { color: 'rgba(0, 188, 212, 0.3)' } },
    splitArea: { show: false },
    axisLine: { lineStyle: { color: 'rgba(0, 188, 212, 0.3)' } }
  },
  series: [{
    type: 'radar',
    symbol: 'none',
    lineStyle: { width: 2, color: '#f56c6c' },
    areaStyle: { color: 'rgba(245, 108, 108, 0.3)' },
    data: [{ value: props.profile.skills.map((s: any) => s.value) }]
  }]
}));

const getThreatClass = (level: string) => {
  if (level.includes('5')) return 'text-red';
  if (level.includes('4')) return 'text-orange';
  return 'text-yellow';
};
</script>

<style scoped>
.dossier-container {
  background: #050505;
  border: 1px solid #333;
  padding: 40px;
  position: relative;
  font-family: 'Share Tech Mono', 'Courier New', monospace;
  color: #a0a0a0;
  width: 800px;
  background-image: 
    linear-gradient(rgba(0, 255, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 0, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  box-shadow: 0 0 50px rgba(0,0,0,0.9);
  overflow: hidden;
}

/* Decorators */
.corner { position: absolute; width: 20px; height: 20px; border: 2px solid #00bcd4; }
.tl { top: 0; left: 0; border-right: 0; border-bottom: 0; }
.tr { top: 0; right: 0; border-left: 0; border-bottom: 0; }
.bl { bottom: 0; left: 0; border-right: 0; border-top: 0; }
.br { bottom: 0; right: 0; border-left: 0; border-top: 0; }

.scan-line {
  position: absolute; top: 0; left: 0; width: 100%; height: 5px;
  background: rgba(0, 255, 255, 0.3);
  animation: scan 3s linear infinite;
  pointer-events: none;
  z-index: 10;
}
@keyframes scan { 0% { top: -10%; } 100% { top: 110%; } }

.stamp {
  position: absolute;
  top: 30px;
  right: -20px;
  border: 4px solid rgba(255, 0, 0, 0.6);
  color: rgba(255, 0, 0, 0.6);
  font-size: 2.5rem;
  font-weight: 900;
  padding: 10px 20px;
  transform: rotate(15deg);
  letter-spacing: 5px;
  z-index: 5;
}

.dossier-content-wrapper { display: flex; gap: 40px; position: relative; z-index: 2; }
.col-left { width: 250px; flex-shrink: 0; display: flex; flex-direction: column; gap: 20px; }
.col-right { flex-grow: 1; }

.photo-frame {
  width: 100%; height: 200px;
  border: 2px solid #333;
  background: #000;
  display: flex; flex-direction: column;
  position: relative;
}
.avatar-placeholder {
  flex-grow: 1; display: flex; align-items: center; justify-content: center;
  color: #333;
  background: radial-gradient(circle, #111 0%, #000 100%);
}
.id-number {
  background: #00bcd4; color: #000; font-weight: bold; text-align: center; font-size: 0.9rem; padding: 4px;
}

.radar-box { height: 250px; border: 1px dashed #333; background: rgba(0,0,0,0.5); }
.mini-chart { width: 100%; height: 100%; }

.header-info h1 { margin: 0; font-size: 2rem; color: #fff; letter-spacing: 2px; }
.codename { font-size: 1.2rem; color: #00bcd4; margin-top: 5px; }
.threat-box { margin-top: 15px; display: flex; align-items: center; gap: 15px; border: 1px solid #444; padding: 10px; background: rgba(255,0,0,0.05); }
.threat-val { font-size: 1.5rem; font-weight: 900; }

.section { margin-top: 30px; }
.section h3 { border-bottom: 2px solid #00bcd4; padding-bottom: 5px; color: #00bcd4; display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
.typewriter { line-height: 1.6; color: #ccc; }

.tech-bar { height: 8px; background: #222; width: 100%; margin-top: 5px; }
.tech-bar .fill { height: 100%; background: #00bcd4; }

.status-footer { margin-top: 40px; font-size: 1.5rem; text-align: right; border-top: 1px dotted #444; padding-top: 10px; }
.blink { color: #f56c6c; animation: blink 1s infinite; text-shadow: 0 0 10px red; }
@keyframes blink { 50% { opacity: 0; } }

.text-red { color: #ff4d4f; }
.text-orange { color: #faad14; }
.text-yellow { color: #fadb14; }
</style>