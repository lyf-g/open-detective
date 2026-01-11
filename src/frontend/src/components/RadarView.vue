<template>
  <div class="radar-container">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { RadarChart } from 'echarts/charts';
import { TitleComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([
  CanvasRenderer,
  RadarChart,
  TitleComponent,
  LegendComponent
]);

const props = defineProps<{
  data: any[]; // Expecting [{name: 'Activity', value: 80, max: 100}, ...]
  title: string;
}>();

const option = computed(() => {
  return {
    backgroundColor: 'transparent',
    title: {
      text: props.title,
      textStyle: { color: '#fff', fontSize: 20 },
      left: 'center',
      top: 20
    },
    radar: {
      indicator: props.data.map(d => ({ name: d.name, max: d.max })),
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#00bcd4',
        fontWeight: 'bold'
      },
      splitLine: {
        lineStyle: {
          color: [
            'rgba(0, 188, 212, 0.1)',
            'rgba(0, 188, 212, 0.2)',
            'rgba(0, 188, 212, 0.4)',
            'rgba(0, 188, 212, 0.6)',
            'rgba(0, 188, 212, 0.8)',
            'rgba(0, 188, 212, 1)'
          ].reverse()
        }
      },
      splitArea: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 188, 212, 0.5)'
        }
      }
    },
    series: [
      {
        name: props.title,
        type: 'radar',
        lineStyle: { width: 3, color: '#00bcd4' },
        areaStyle: { color: 'rgba(0, 188, 212, 0.5)' },
        data: [
          {
            value: props.data.map(d => d.value),
            name: props.title
          }
        ]
      }
    ]
  };
});
</script>

<style scoped>
.radar-container {
  width: 100%;
  height: 400px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>