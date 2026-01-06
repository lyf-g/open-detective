<template>
  <div class="chart-container">
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
]);

const props = defineProps<{
  data: any[];
  title?: string;
  theme?: 'light' | 'dark';
}>();

const chartOption = computed(() => {
  if (!props.data || props.data.length === 0) return {};

  const isDark = props.theme === 'dark';
  const textColor = isDark ? '#ccc' : '#333';
  const splitLineColor = isDark ? '#444' : '#eee';

  // Assumption: Data structure is [{ month: '2023-01', value: 123, ... }, ...]
  const keys = Object.keys(props.data[0]);
  
  // Heuristic: Find a key that looks like a date/category for X-axis
  const xAxisKey = keys.find(k => ['month', 'date', 'year', 'day'].includes(k.toLowerCase())) || keys[0];

  // Check if we have 'repo_name' for multi-series comparison
  const hasRepoName = keys.includes('repo_name');

  if (hasRepoName) {
    // Multi-series logic
    const repos = [...new Set(props.data.map(d => d.repo_name))];
    const valKey = 'value'; // We enforce this from backend query

    // Get all unique time points and sort them
    const allTimePoints = [...new Set(props.data.map(d => d[xAxisKey]))].sort();
    
    const seriesList = repos.map((repo, idx) => {
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
            areaStyle: { opacity: 0.1 }, // Less opacity for multiple series
            // Auto color assignment by ECharts
        };
    });

    return {
      title: {
        text: props.title || 'Comparison Analysis',
        left: 'center',
        textStyle: { fontSize: 14, color: textColor }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? 'rgba(50,50,50,0.9)' : '#fff',
        textStyle: { color: isDark ? '#fff' : '#333' },
        borderColor: isDark ? '#555' : '#ccc'
      },
      legend: {
        data: repos,
        top: '30px',
        textStyle: { color: textColor }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
        top: '80px' // More space for legend
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: allTimePoints,
        axisLabel: { color: textColor },
        axisLine: { lineStyle: { color: splitLineColor } }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { color: splitLineColor } }
      },
      series: seriesList
    };
  }

  // Single Series Fallback (Existing Logic)
  // Heuristic: Find the numerical key for Y-axis
  const seriesKey = keys.find(k => k !== xAxisKey && typeof props.data[0][k] === 'number') || keys[1];

  const xAxisData = props.data.map(item => item[xAxisKey]);
  const seriesData = props.data.map(item => item[seriesKey]);

  return {
    title: {
      text: props.title || 'Trend Analysis',
      left: 'center',
      textStyle: { fontSize: 14, color: textColor }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(50,50,50,0.9)' : '#fff',
      textStyle: { color: isDark ? '#fff' : '#333' },
      borderColor: isDark ? '#555' : '#ccc'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData,
      axisLabel: { color: textColor },
      axisLine: { lineStyle: { color: splitLineColor } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { color: splitLineColor } }
    },
    series: [
      {
        name: seriesKey,
        type: 'line', // Default to Line chart for time series
        data: seriesData,
        smooth: true,
        areaStyle: {
          opacity: 0.3
        },
        itemStyle: {
          color: '#00bcd4' // Cyan color matches the theme
        }
      }
    ]
  };
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 300px;
  margin-top: 0; /* Handled by parent */
  border: none;
  background: transparent;
  padding: 10px 0;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
