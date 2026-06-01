<template>
  <div class="w-full mt-6 bg-slate-50/70 rounded-xl border border-blue-100 shadow-inner p-4 transition-all relative">
    <div class="text-xs text-slate-400 font-bold mb-2 uppercase tracking-widest border-b pb-2">📊 学情数据分析图表</div>
    <div ref="chartRef" class="w-full h-[350px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({ data: Object });
const chartRef = ref(null);
let myChart = null, chartObs = null;

const renderChart = () => {
  if (!chartRef.value || !props.data) return;
  if (!myChart) {
    myChart = echarts.init(chartRef.value);
    chartObs = new ResizeObserver(() => myChart?.resize());
    chartObs.observe(chartRef.value);
  }
  try {
    if (props.data.series) {
      const opt = { ...props.data };
      if (!opt.color) opt.color = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
      myChart.setOption(opt, true);
    } else {
      myChart.clear();
      chartRef.value.innerHTML = "<div class='text-red-500 pt-10 text-center font-bold'>⚠️ ECharts 缺少 series 配置。</div>";
    }
  } catch (err) {
    chartRef.value.innerHTML = `<div class='text-red-500 pt-10 text-center font-bold'>⚠️ 渲染崩溃: ${err.message}</div>`;
  }
};

onMounted(() => setTimeout(renderChart, 150));
watch(() => props.data, renderChart, { deep: true });
onBeforeUnmount(() => { chartObs?.disconnect(); myChart?.dispose(); });
</script>