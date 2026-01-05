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
}>();

const chartOption = computed(() => {
  if (!props.data || props.data.length === 0) return {};

  // Assumption: Data structure is [{ month: '2023-01', value: 123, ... }, ...]
  // We try to find the 'axis' key (usually time) and 'value' key.
  const keys = Object.keys(props.data[0]);
  
  // Heuristic: Find a key that looks like a date/category for X-axis
  const xAxisKey = keys.find(k => ['month', 'date', 'year', 'day'].includes(k.toLowerCase())) || keys[0];
  // Heuristic: Find the numerical key for Y-axis
  const seriesKey = keys.find(k => k !== xAxisKey && typeof props.data[0][k] === 'number') || keys[1];

  const xAxisData = props.data.map(item => item[xAxisKey]);
  const seriesData = props.data.map(item => item[seriesKey]);

  return {
    title: {
      text: props.title || 'Trend Analysis',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
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
      data: xAxisData
    },
    yAxis: {
      type: 'value'
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
          color: '#5470C6'
        }
      }
    ]
  };
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 300px; /* Fixed height for the chart */
  margin-top: 1rem;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fff;
  padding: 10px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
