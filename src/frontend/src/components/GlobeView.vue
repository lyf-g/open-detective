<template>
  <div class="globe-container">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { GlobeComponent } from 'echarts-gl/components';
import { Scatter3DChart } from 'echarts-gl/charts';
import VChart from 'vue-echarts';
import 'echarts-gl';

use([
  CanvasRenderer,
  GlobeComponent,
  Scatter3DChart
]);

// Mock Global Data (Lat, Lng, Value)
const data = [
    [121.4737, 31.2304, 10], // Shanghai
    [-122.4194, 37.7749, 20], // SF
    [139.6917, 35.6895, 15], // Tokyo
    [-0.1278, 51.5074, 8], // London
    [2.3522, 48.8566, 7], // Paris
    [151.2093, -33.8688, 5], // Sydney
    [-74.0060, 40.7128, 18], // NYC
    [13.4050, 52.5200, 9], // Berlin
    [77.2090, 28.6139, 12], // Delhi
    [-43.1729, -22.9068, 6], // Rio
];

// Add more random points
for (let i = 0; i < 50; i++) {
    data.push([
        Math.random() * 360 - 180,
        Math.random() * 180 - 90,
        Math.random() * 5
    ]);
}

const option = computed(() => {
  return {
    backgroundColor: '#000',
    globe: {
      baseTexture: '/earth.jpg', // We assume this exists or it will be black. Or use a color.
      // If no texture, use color
      baseColor: '#111',
      heightTexture: null,
      displacementScale: 0.1,
      shading: 'lambert',
      environment: '#000',
      light: {
        ambient: {
          intensity: 0.4
        },
        main: {
          intensity: 0.4
        }
      },
      viewControl: {
        autoRotate: true,
        autoRotateSpeed: 5
      }
    },
    series: [
      {
        type: 'scatter3D',
        coordinateSystem: 'globe',
        blendMode: 'lighter',
        symbolSize: 5,
        itemStyle: {
          color: '#00bcd4',
          opacity: 0.8
        },
        data: data
      }
    ]
  };
});
</script>

<style scoped>
.globe-container {
  width: 100%;
  height: 600px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>