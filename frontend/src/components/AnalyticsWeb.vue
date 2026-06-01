<template>
  <div class="analytics-wrapper">
    <div class="kpi-cards">
      <div class="kpi-card blue">
        <div class="kpi-title">已测评网站总数</div>
        <div class="kpi-value">{{ webStats.totalProjects }} <span class="unit">个</span></div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-title">📱 响应式设计合格率</div>
        <div class="kpi-value">{{ webStats.responsivePassRate }} <span class="unit">%</span></div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-title">⚠️ 班级技术架构最薄弱项</div>
        <div class="kpi-value warning-text" style="font-size: 15px;">{{ webStats.weakestDimension }}</div>
      </div>
      <div class="kpi-card orange">
        <div class="kpi-title">🎨 UI均分最高优势项</div>
        <div class="kpi-value text-emerald-600" style="font-size: 15px; font-weight: 800; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">
          {{ webStats.strongestDimension }}
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card col-span-2">
        <div class="chart-title">📊 班级前沿五维能级平均分 (UI/UX 核心诊断大盘)</div>
        <div ref="barChartRef" class="chart-container" style="height: 320px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🕸️ 全班前端设计综合实力热力网络</div>
        <div ref="radarChartRef" class="chart-container" style="height: 320px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  records: Array
});

const barChartRef = ref(null);
const radarChartRef = ref(null);
let charts = {};

// 🌟 核心数据工程：穿透清洗并动态解算五个核心维度
const webStats = computed(() => {
  const totals = { "UI美观度": 0, "响应式适配": 0, "语义化与规范": 0, "性能与体验": 0, "交互逻辑": 0 };
  const counts = { "UI美观度": 0, "响应式适配": 0, "语义化与规范": 0, "性能与体验": 0, "交互逻辑": 0 };
  let responsivePassCount = 0;
  let totalProjects = 0;

  props.records.forEach(r => {
    if (!r.error_cause) return;
    totalProjects++;
    const match = r.error_cause.match(/```json([\s\S]*?)```/);
    if (match) {
      try {
        const json = JSON.parse(match[1].trim());
        const values = json.series?.[0]?.data?.[0]?.value || [];
        const indicators = json.radar?.indicator || [];

        indicators.forEach((ind, index) => {
          const cleanName = ind.name.replace(/[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDC00-\uDFFF]/g, '').trim();
          if (totals[cleanName] !== undefined) {
            const val = values[index] || 0;
            totals[cleanName] += val;
            counts[cleanName]++;
            if (cleanName === "响应式适配" && val >= 60) responsivePassCount++;
          }
        });
      } catch (e) {}
    }
  });

  const averages = {};
  Object.keys(totals).forEach(k => {
    averages[k] = counts[k] > 0 ? Math.round(totals[k] / counts[k]) : 0;
  });

  const sorted = Object.entries(averages).sort((a, b) => a[1] - b[1]);
  const weakestDimension = sorted[0]?.[0] ? `${sorted[0][0]} (${sorted[0][1]}分)` : '暂无数据';
  const strongestDimension = sorted[sorted.length - 1]?.[0] ? `${sorted[sorted.length - 1][0]} (${sorted[sorted.length - 1][1]}分)` : '暂无数据';
  const responsivePassRate = totalProjects > 0 ? Math.round((responsivePassCount / totalProjects) * 100) : 0;

  return { totalProjects, responsivePassRate, weakestDimension, strongestDimension, averages };
});

const renderCharts = () => {
  if (!barChartRef.value || !radarChartRef.value) return;

  if (!charts.bar) charts.bar = echarts.init(barChartRef.value);
  if (!charts.radar) charts.radar = echarts.init(radarChartRef.value);

  const dimensions = Object.keys(webStats.value.averages);
  const values = Object.values(webStats.value.averages);

  // 1. Bar Chart
  charts.bar.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}: {c}分' },
    xAxis: { type: 'category', data: dimensions, axisLabel: { fontSize: 11, fontWeight: 'bold' } },
    yAxis: { type: 'value', max: 100, name: '均分' },
    series: [{
      name: '能级均分', type: 'bar', data: values, barWidth: '40%',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#10b981' }, { offset: 1, color: '#059669' }]),
        borderRadius: [6, 6, 0, 0]
      },
      label: { show: true, position: 'top', formatter: '{c}分', fontWeight: 'bold' }
    }]
  });

  // 2. Radar Chart
  charts.radar.setOption({
    radar: { indicator: dimensions.map(d => ({ name: d, max: 100 })), radius: '65%', axisName: { color: '#475569', fontWeight: 'bold' } },
    series: [{ type: 'radar', data: [{ value: values, name: '全班技术均分', areaStyle: { color: 'rgba(16, 185, 129, 0.2)' }, lineStyle: { color: '#10b981', width: 2 } }] }]
  });
};

watch(webStats, async () => { await nextTick(); renderCharts(); }, { deep: true, immediate: true });
const handleResize = () => Object.values(charts).forEach(c => c && c.resize());
onMounted(() => { window.addEventListener('resize', handleResize); });
onUnmounted(() => { window.removeEventListener('resize', handleResize); Object.values(charts).forEach(c => c && c.dispose()); });
</script>

<style scoped>
.col-span-2 { grid-column: span 2 / span 2; }
</style>