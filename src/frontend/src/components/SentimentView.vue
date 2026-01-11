<template>
  <div class="sentiment-container">
    <div class="sentiment-gauge">
      <h3>SENTIMENT SCORE</h3>
      <v-chart class="chart" :option="gaugeOption" autoresize />
    </div>
    <div class="sentiment-cloud">
      <h3>COMMUNITY VOICE</h3>
      <v-chart class="chart" :option="cloudOption" autoresize />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { GaugeChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import 'echarts-wordcloud';

use([
  CanvasRenderer,
  GaugeChart,
  TitleComponent,
  TooltipComponent
]);

const props = defineProps<{
  data: { score: number, keywords: any[] };
}>();

const gaugeOption = computed(() => {
  const score = props.data.score * 100;
  return {
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        splitNumber: 5,
        itemStyle: {
          color: score > 60 ? '#00bcd4' : '#ff4d4f',
          shadowColor: 'rgba(0,138,138,0.45)',
          shadowBlur: 10,
          shadowOffsetX: 2,
          shadowOffsetY: 2
        },
        progress: {
          show: true,
          roundCap: true,
          width: 15
        },
        pointer: {
          icon: 'path://M2090.36389,615.30999 L2090.36389,615.30999 C2091.48372,615.30999 2092.40383,616.194028 2092.44859,617.312956 L2096.90698,728.755929 C2097.05155,732.369577 2094.2393,735.416212 2090.62566,735.56078 C2090.53845,735.564269 2090.45117,735.566014 2090.36389,735.566014 L2090.36389,735.566014 C2086.74736,735.566014 2083.81557,732.63423 2083.81557,729.017692 C2083.81557,728.930412 2083.81732,728.84314 2083.82081,728.755929 L2088.2792,617.312956 C2088.32396,616.194028 2089.24407,615.30999 2090.36389,615.30999 Z',
          length: '75%',
          width: 16,
          offsetCenter: [0, '5%']
        },
        axisLine: {
          roundCap: true,
          lineStyle: {
            width: 15
          }
        },
        axisTick: {
          splitNumber: 2,
          lineStyle: {
            width: 2,
            color: '#999'
          }
        },
        splitLine: {
          length: 12,
          lineStyle: {
            width: 3,
            color: '#999'
          }
        },
        axisLabel: {
          distance: 20,
          color: '#999',
          fontSize: 10
        },
        title: {
          show: false
        },
        detail: {
          backgroundColor: '#fff',
          borderColor: '#999',
          borderWidth: 1,
          width: '60%',
          lineHeight: 30,
          height: 30,
          borderRadius: 8,
          offsetCenter: [0, '35%'],
          valueAnimation: true,
          formatter: function (value: number) {
            return '{value|' + value.toFixed(0) + '}{unit|%}';
          },
          rich: {
            value: {
              fontSize: 20,
              fontWeight: 'bolder',
              color: '#777'
            },
            unit: {
              fontSize: 10,
              color: '#999',
              padding: [0, 0, -10, 5]
            }
          }
        },
        data: [
          {
            value: score
          }
        ]
      }
    ]
  };
});

const cloudOption = computed(() => {
  return {
    backgroundColor: 'transparent',
    tooltip: { show: true },
    series: [{
      type: 'wordCloud',
      gridSize: 2,
      sizeRange: [12, 50],
      rotationRange: [-90, 90],
      shape: 'pentagon',
      width: '100%',
      height: '100%',
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: function () {
          return 'rgb(' + [
            Math.round(Math.random() * 160 + 50),
            Math.round(Math.random() * 160 + 50),
            Math.round(Math.random() * 160 + 50)
          ].join(',') + ')';
        }
      },
      emphasis: {
        focus: 'self',
        textStyle: {
          textShadowBlur: 10,
          textShadowColor: '#333'
        }
      },
      data: props.data.keywords
    }]
  };
});
</script>

<style scoped>
.sentiment-container {
  display: flex;
  gap: 20px;
  width: 100%;
  height: 300px;
}
.sentiment-gauge, .sentiment-cloud {
  flex: 1;
  background: rgba(0,0,0,0.3);
  border: 1px solid #333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}
h3 {
  color: #00bcd4;
  text-align: center;
  margin: 10px 0 0 0;
  font-size: 0.9rem;
  letter-spacing: 1px;
}
.chart {
  flex-grow: 1;
  width: 100%;
}
</style>