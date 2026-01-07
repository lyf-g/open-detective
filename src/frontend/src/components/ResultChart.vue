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
        <el-tag size="small" type="info" effect="plain" class="chart-tag">Interactive Analytics</el-tag>
      </div>
    </div>
    <div class="chart-body">
      <v-chart class="chart" :option="chartOption" autoresize />
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
}>();

const analyzing = ref(false);
const anomalies = ref<any[]>([]);

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

  const isDark = true; // Hardcoded dark for cyberpunk theme
  const textColor = '#909399';
  const splitLineColor = '#2c2c2c';

  const keys = Object.keys(props.data[0]);
  const xAxisKey = keys.find(k => ['month', 'date', 'year', 'day'].includes(k.toLowerCase())) || keys[0];
  const hasRepoName = keys.includes('repo_name');

  // Multi-series logic
  if (hasRepoName) {
    const repos = [...new Set(props.data.map(d => d.repo_name))];
    const valKey = keys.find(k => k !== xAxisKey && k !== 'repo_name' && typeof props.data[0][k] === 'number') || 'value';
    const allTimePoints = [...new Set(props.data.map(d => d[xAxisKey]))].sort();
    
    const seriesList = repos.map((repo) => {
        const repoData = props.data.filter(d => d.repo_name === repo);
        const dataPoints = allTimePoints.map(t => {
            const found = repoData.find(d => d[xAxisKey] === t);
            return found ? found[valKey] : null;
        });
        
        return {
            name: repo,
            type: 'line',
            data: dataPoints,
            smooth: true,
            showSymbol: false,
            areaStyle: { opacity: 0.05 },
            emphasis: { focus: 'series', lineStyle: { width: 3 } }
        };
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
                   return `<b>Anomaly Detected!</b><br/>${item['repo_name']}<br/>Date: ${item[xAxisKey]}<br/>Value: ${item[valKey]}<br/>Z-Score: ${item.z_score?.toFixed(2)}`;
               }
            }
        } as any);
    }

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1a1a1a',
        borderColor: '#333',
        textStyle: { color: '#fff' },
        axisPointer: { lineStyle: { color: '#00bcd4', width: 1 } }
      },
      legend: {
        data: [...repos, 'Anomalies'],
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
  }

  // Single series logic
  const seriesKey = keys.find(k => k !== xAxisKey && typeof props.data[0][k] === 'number') || keys[1];
  const seriesData = [{
      name: seriesKey,
      type: 'line',
      data: props.data.map(item => item[seriesKey]),
      smooth: true,
      itemStyle: { color: '#00bcd4' },
      areaStyle: { opacity: 0.2, color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{offset: 0, color: '#00bcd4'}, {offset: 1, color: 'rgba(0,188,212,0)'}] } }
  }];
  
  if (anomalies.value.length > 0) {
        const anomalyData = anomalies.value.map(a => {
           return [a[xAxisKey], a[seriesKey]];
        });
        seriesData.push({
            name: 'Anomalies',
            type: 'scatter',
            symbolSize: 15,
            itemStyle: { color: '#ff4d4f', shadowBlur: 10, shadowColor: '#ff4d4f' },
            z: 20,
            data: anomalyData,
            tooltip: {
               formatter: (params: any) => {
                   const item = anomalies.value[params.dataIndex];
                   if (!item) return '';
                   return `<b>Anomaly Detected!</b><br/>Date: ${item[xAxisKey]}<br/>Value: ${item[seriesKey]}<br/>Z-Score: ${item.z_score?.toFixed(2)}`;
               }
            }
        } as any);
  }
  
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1a1a1a', textStyle: { color: '#fff' } },
    toolbox: {
      show: true,
      feature: {
        magicType: { type: ['line', 'bar'] },
        saveAsImage: { title: 'Save' }
      },
      iconStyle: { borderColor: '#555' }
    },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', bottom: 10, height: 20, borderColor: '#333', handleStyle: { color: '#00bcd4' } }
    ],
    xAxis: { type: 'category', data: props.data.map(item => item[xAxisKey]), axisLabel: { color: textColor } },
    yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: splitLineColor } } },
    series: seriesData
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
</style>