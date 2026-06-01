<template>
  <div class="analytics-wrapper">
    <div class="kpi-cards">
      <div class="kpi-card blue">
        <div class="kpi-title">已批改总题数</div>
        <div class="kpi-value">{{ stats.total }} <span class="unit">题</span></div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-title">班级综合正确率</div>
        <div class="kpi-value">{{ stats.overall_correct_rate }} <span class="unit">%</span></div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-title">最薄弱知识点</div>
        <div class="kpi-value warning-text" :title="stats.worstKp">{{ stats.worstKp }}</div>
      </div>
      <div class="kpi-card orange">
        <div class="kpi-title">最高频错因</div>
        <div class="kpi-value warning-text" :title="stats.topError">{{ stats.topError }}</div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">🎯 核心共性错因分布</div>
        <div ref="pieChartRef" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">📊 各题目错题量分布</div>
        <div ref="barChartRef" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">📉 知识点薄弱分布排行</div>
        <div ref="hbarChartRef" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🕸️ 班级综合能力画像</div>
        <div ref="radarChartRef" class="chart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  records: Array,
  stats: Object
});

const pieChartRef = ref(null);
const barChartRef = ref(null);
const hbarChartRef = ref(null);
const radarChartRef = ref(null);
let charts = {};

const renderCharts = () => {
  if (!pieChartRef.value || !barChartRef.value || !hbarChartRef.value || !radarChartRef.value) return;

  if (!charts.pie) charts.pie = echarts.init(pieChartRef.value);
  if (!charts.bar) charts.bar = echarts.init(barChartRef.value);
  if (!charts.hbar) charts.hbar = echarts.init(hbarChartRef.value);
  if (!charts.radar) charts.radar = echarts.init(radarChartRef.value);

  // 1. 核心共性错因分布 (Pie)
  const pieData = Object.entries(props.stats.errorCounts || {}).map(([cause, count]) => ({ name: cause, value: count }));
  charts.pie.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
    legend: { bottom: '0%', type: 'scroll' },
    series: [{ type: 'pie', radius: ['45%', '70%'], itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 }, label: { show: false }, data: pieData.length ? pieData : [{ name: '无错题', value: 0 }] }]
  });

  // 2. 各题目错题量分布 (Bar)
  const errMap = {};
  props.records.forEach(r => { if (String(r.is_correct).trim() !== '正确') { const q = String(r.question_number || '未知'); errMap[q] = (errMap[q] || 0) + 1; } });
  const qKeys = Object.keys(errMap).sort((a, b) => a.localeCompare(b, 'zh-CN', { numeric: true }));
  charts.bar.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: qKeys },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: '做错人次', type: 'bar', data: qKeys.map(k => errMap[k]), itemStyle: { color: '#2563eb' } }]
  });

  // 3. 知识点薄弱分布排行 (HBar)
  const worstKps = (props.stats.kpMastery || []).slice(0, 6).reverse();
  charts.hbar.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'value', max: 100 },
    yAxis: { type: 'category', data: worstKps.map(k => k.knowledge_point) },
    series: [{ name: '错误率', type: 'bar', data: worstKps.map(k => k.error_rate), label: { show: true, position: 'right' }, itemStyle: { color: '#ef4444' } }]
  });

  // 4. 班级综合能力画像 (Radar)
  charts.radar.setOption({
    radar: { indicator: (props.stats.kpMastery || []).map(k => ({ name: k.knowledge_point, max: 100 })), radius: '65%' },
    series: [{ type: 'radar', data: [{ value: (props.stats.kpMastery || []).map(k => k.rate), name: '掌握率', areaStyle: { color: 'rgba(59, 130, 246, 0.2)' } }] }]
  });
};

watch(() => props.records, async () => { await nextTick(); renderCharts(); }, { deep: true, immediate: true });
const handleResize = () => Object.values(charts).forEach(c => c && c.resize());
onMounted(() => { window.addEventListener('resize', handleResize); });
onUnmounted(() => { window.removeEventListener('resize', handleResize); Object.values(charts).forEach(c => c && c.dispose()); });
</script>