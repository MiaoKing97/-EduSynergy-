<template>
  <div class="w-full mt-6 bg-slate-50/70 rounded-xl border border-blue-100 shadow-inner p-4 transition-all relative">
    <div class="text-xs text-slate-400 font-bold mb-2 uppercase tracking-widest border-b pb-2 flex justify-between items-center">
      <span>☁️ 词频质量透视</span><span class="text-xs text-slate-400">(绿色:优 / 红色:冗)</span>
    </div>
    <div ref="wcRef" class="w-full h-[300px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import 'echarts-wordcloud';

const props = defineProps({ data: Array });
const wcRef = ref(null);
let myChart = null, obs = null;

const renderChart = () => {
  if (!wcRef.value || !props.data) return;
  if (!myChart) {
    myChart = echarts.init(wcRef.value);
    obs = new ResizeObserver(() => myChart?.resize());
    obs.observe(wcRef.value);
  }
  const processedData = props.data.map(item => ({
    name: item.name || item.text || item.word || '未命名',
    value: (item.value || 10) + Math.random() * 20,
    textStyle: { color: item.type === 'good' ? '#10b981' : '#ef4444' }
  }));
  myChart.setOption({
    tooltip: { show: true },
    series: [{
      type: 'wordCloud', shape: 'circle', gridSize: 8, sizeRange: [14, 65],
      rotationRange: [-45, 90], textStyle: { fontFamily: 'sans-serif', fontWeight: 'bold' },
      data: processedData
    }]
  }, true);
};

onMounted(() => setTimeout(renderChart, 150));
watch(() => props.data, renderChart, { deep: true });
onBeforeUnmount(() => { obs?.disconnect(); myChart?.dispose(); });
</script>