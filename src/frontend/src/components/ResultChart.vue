<template>
  <div class="case-visualization">
    <div class="chart-header">
      <h3 v-if="title" class="chart-title">{{ title }}</h3>
      <div class="actions">
        <el-button 
          size="small" 
          type="danger" 
          plain 
          @click="checkAnomalies" 
          :loading="analyzing"
          v-if="!anomalies.length"
        >
           Find Anomalies
        </el-button>
        <el-button 
          size="small" 
          type="info" 
          plain 
          @click="clearAnomalies" 
          v-else
        >
           Clear Anomalies
        </el-button>
        <el-button 
          size="small" 
          type="warning" 
          plain 
          @click="analyzeCause"
        >
           Root Cause Probe
        </el-button>
        <el-tag size="small" type="info" effect="plain" class="chart-tag">Interactive Analytics</el-tag>
      </div>
    </div>
    
    <div class="chart-body" style="position: relative;">
      <v-chart class="chart" :option="chartOption" autoresize :loading="!data || data.length === 0" />
      
      <!-- Causal Overlay (Clean Linear Layout) -->
      <transition name="fade">
        <div v-if="showCause && activeCause" class="cause-overlay" @click="showCause = false">
            <div class="cause-card">
                <div class="cause-header">
                    <div class="main-title">PROBABILISTIC CAUSAL GRAPH</div>
                    <div class="sub-title">Bayesian Inference Chain: Event Correlation Analysis</div>
                </div>

                <div class="cause-body">
                    <!-- ROOT -->
                    <div class="step-group">
                        <div class="step-label">ROOT EVENT</div>
                        <div class="step-content root">{{ activeCause.root }}</div>
                    </div>

                    <!-- ARROW 1 -->
                    <div class="connector-line">
                        <div class="line"></div>
                        <div class="prob-tag">Likelihood: {{ (activeCause.prob1 * 100).toFixed(0) }}%</div>
                        <div class="line"></div>
                    </div>

                    <!-- TRIGGER -->
                    <div class="step-group">
                        <div class="step-label">TRIGGER</div>
                        <div class="step-content trigger">{{ activeCause.event }}</div>
                    </div>

                    <!-- ARROW 2 -->
                    <div class="connector-line">
                        <div class="line"></div>
                        <div class="prob-tag">Impact: {{ (activeCause.prob2 * 100).toFixed(0) }}%</div>
                        <div class="line"></div>
                    </div>

                    <!-- OUTCOME -->
                    <div class="step-group">
                        <div class="step-label">OUTCOME</div>
                        <div class="step-content outcome">{{ activeCause.outcome }}</div>
                    </div>

                    <!-- ALT PATH -->
                    <div class="alt-cause" v-if="activeCause.alt">
                        <span class="alt-connector">↳</span> 
                        <span class="alt-prob">({{ activeCause.alt_prob }})</span> 
                        <span class="alt-text">{{ activeCause.alt }}</span>
                    </div>
                </div>
            </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart, PieChart, ScatterChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  ToolboxComponent,
  DataZoomComponent,
  MarkPointComponent
} from 'echarts/components';
import VChart from 'vue-echarts';

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  ToolboxComponent,
  DataZoomComponent,
  MarkPointComponent
]);

const props = defineProps<{
  data: any[];
  title?: string;
  theme?: 'light' | 'dark';
  customCause?: any; // { root, event, outcome, prob1, prob2, alt }
}>();

const analyzing = ref(false);
const anomalies = ref<any[]>([]);
const showCause = ref(false);
const activeCause = ref<any>(null);

const analyzeCause = () => {
    if (props.customCause) {
        activeCause.value = props.customCause;
    } else {
        // Default Mock
        activeCause.value = {
            root: 'Activity Spike',
            event: 'Feature Release',
            outcome: 'Issue Increase',
            prob1: 0.95,
            prob2: 0.82,
            alt: 'HackerNews Trend',
            alt_prob: 0.60
        };
    }
    showCause.value = true;
};

const clearAnomalies = () => {
    anomalies.value = [];
};

const checkAnomalies = async () => {
    analyzing.value = true;
    try {
        const response = await fetch('/api/v1/analytics/anomalies', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: props.data })
        });
        if (!response.ok) throw new Error("API Error");
        
        const result = await response.json();
        if (result.anomalies && result.anomalies.length > 0) {
            anomalies.value = result.anomalies;
            ElMessage.success(`Found ${result.anomalies.length} anomalies`);
        } else {
            ElMessage.info('No significant anomalies found.');
            anomalies.value = [];
        }
    } catch (e) {
        ElMessage.error('Analysis failed');
        console.error(e);
    } finally {
        analyzing.value = false;
    }
};

const chartOption = computed(() => {
  if (!props.data || props.data.length === 0) return {};

  const textColor = '#909399';
  const splitLineColor = '#2c2c2c';

  const keys = Object.keys(props.data[0]);
  const xAxisKey = keys.find(k => ['month', 'date', 'year', 'day'].includes(k.toLowerCase())) || keys[0];
  const hasRepoName = keys.includes('repo_name');
  
  // Identify value key (heuristic: number and not xAxis)
  const valKey = keys.find(k => k !== xAxisKey && k !== 'repo_name' && k !== 'is_forecast' && typeof props.data[0][k] === 'number') || 'value';

  // Get all unique time points sorted
  const allTimePoints = [...new Set(props.data.map(d => d[xAxisKey]))].sort();

  const seriesList: any[] = [];
  
  const repos = hasRepoName ? [...new Set(props.data.map(d => d.repo_name))] : ['Value'];

  repos.forEach((repo) => {
      const repoData = hasRepoName ? props.data.filter(d => d.repo_name === repo) : props.data;
      
      // Split into Actual vs Forecast
      // We rely on 'is_forecast' flag.
      const actualRows = repoData.filter(d => !d.is_forecast);
      const forecastRows = repoData.filter(d => d.is_forecast);
      
      if (forecastRows.length === 0) {
          // Standard single line
          const dataPoints = allTimePoints.map(t => {
              const found = repoData.find(d => d[xAxisKey] === t);
              return found ? found[valKey] : null;
          });
          seriesList.push({
              name: repo,
              type: 'line',
              data: dataPoints,
              smooth: true,
              showSymbol: false,
              areaStyle: { opacity: 0.05 },
              emphasis: { focus: 'series' }
          });
      } else {
          // Complex split line
          // 1. Actual Series
          const actualPoints = allTimePoints.map(t => {
              const found = actualRows.find(d => d[xAxisKey] === t);
              return found ? found[valKey] : null;
          });
          
          seriesList.push({
              name: repo,
              type: 'line',
              data: actualPoints,
              smooth: true,
              showSymbol: false,
              areaStyle: { opacity: 0.05 },
              emphasis: { focus: 'series' }
          });

          // 2. Forecast Series
          // To connect lines, we need the LAST actual point to be the FIRST forecast point (visually).
          // We find the last actual row's index in allTimePoints
          const lastActualRow = actualRows[actualRows.length - 1];
          
          const forecastPoints = allTimePoints.map(t => {
              const foundForecast = forecastRows.find(d => d[xAxisKey] === t);
              if (foundForecast) return foundForecast[valKey];
              
              // Connector point
              if (lastActualRow && t === lastActualRow[xAxisKey]) {
                  return lastActualRow[valKey];
              }
              return null;
          });

          seriesList.push({
              name: repo + ' (Forecast)',
              type: 'line',
              data: forecastPoints,
              smooth: true,
              showSymbol: false,
              lineStyle: { type: 'dashed', opacity: 0.7 },
              itemStyle: { opacity: 0.7 },
              emphasis: { focus: 'series' }
          });
      }
  });
    
  if (anomalies.value.length > 0) {
        const anomalyData = anomalies.value.map(a => {
           return [a[xAxisKey], a[valKey]];
        });
        seriesList.push({
            name: 'Anomalies',
            type: 'scatter',
            symbolSize: 12,
            itemStyle: { color: '#ff4d4f', shadowBlur: 10, shadowColor: '#ff4d4f' },
            z: 20,
            data: anomalyData,
            tooltip: {
               formatter: (params: any) => {
                   const item = anomalies.value[params.dataIndex];
                   if (!item) return '';
                   return `<b>Anomaly Detected!</b><br/>${item['repo_name'] || ''}<br/>Date: ${item[xAxisKey]}<br/>Value: ${item[valKey]}<br/>Z-Score: ${item.z_score?.toFixed(2)}`;
               }
            }
        });
  }

  return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1a1a1a',
        borderColor: '#333',
        textStyle: { color: textColor },
        axisPointer: { lineStyle: { color: '#00bcd4', width: 1 } }
      },
      legend: {
        data: seriesList.map(s => s.name),
        top: 0,
        textStyle: { color: textColor },
        icon: 'circle'
      },
      toolbox: {
        show: true,
        feature: {
          magicType: { type: ['line', 'bar'] },
          saveAsImage: { title: 'Save' }
        },
        iconStyle: { borderColor: '#555' }
      },
      grid: { left: '2%', right: '4%', bottom: '15%', containLabel: true, top: '40px' },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', bottom: 10, height: 20, borderColor: '#333', handleStyle: { color: '#00bcd4' } }
      ],
      xAxis: {
        type: 'category',
        data: allTimePoints,
        axisLabel: { color: textColor },
        axisLine: { lineStyle: { color: splitLineColor } }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } }
      },
      series: seriesList
  };
});
</script>

<style scoped>
.case-visualization {
  background: rgba(25, 25, 25, 0.6);
  border: 1px solid #333;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.actions {
    display: flex;
    align-items: center;
    gap: 10px;
}
.chart-title {
  color: #00bcd4;
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.chart-container {
  width: 100%;
  height: 350px;
}
.chart {
  height: 300px;
  width: 100%;
}

.cause-overlay {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.85);
    backdrop-filter: blur(4px);
    display: flex; justify-content: center; align-items: center;
    z-index: 50;
    cursor: pointer;
}
.cause-card {
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 25px 40px;
    min-width: 320px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    display: flex;
    flex-direction: column;
    align-items: center;
}

.cause-header {
    text-align: center;
    margin-bottom: 25px;
    border-bottom: 1px solid #333;
    padding-bottom: 15px;
    width: 100%;
}
.main-title {
    color: #e6a23c;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 5px;
}
.sub-title {
    color: #888;
    font-size: 0.8rem;
    font-family: monospace;
}

.cause-body {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}

.step-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
}

.step-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #666;
    letter-spacing: 1px;
}

.step-content {
    font-size: 1.2rem;
    font-weight: 500;
    color: #eee;
}
.step-content.root { color: #f56c6c; }
.step-content.trigger { color: #409eff; }
.step-content.outcome { color: #67c23a; }

.connector-line {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 5px 0;
}
.connector-line .line {
    width: 1px;
    height: 15px;
    background: #444;
}
.prob-tag {
    font-size: 0.75rem;
    color: #888;
    background: #252525;
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid #333;
}

.alt-cause {
    margin-top: 20px;
    font-family: monospace;
    color: #888;
    font-size: 0.9rem;
    display: flex;
    gap: 8px;
    opacity: 0.7;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>