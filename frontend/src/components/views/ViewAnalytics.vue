<template>
  <div class="analytics-dashboard">
    <div class="dashboard-header">
      <div class="title-area">
        <h3>📈 教研学情多维透视面板</h3>
        <p>{{ isWebTeacher ? '前端响应式设计规范与 UI/UX 体验能级评估大屏' : '基于 AI 逐题诊断的班级学情数据汇总与可视化图表' }}</p>
      </div>
      <button class="btn-sync" @click="loadDashboardStats(true)" :disabled="loading">
        <span class="sync-icon" :class="{ 'is-spinning': loading }">🔄</span>
        {{ loading ? '云端数据同步中...' : '强制同步飞书最新数据' }}
      </button>
    </div>

    <div v-if="loading && rawRecords.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>正在从飞书多维表格提取数据引擎并渲染图表，请稍候...</p>
    </div>

    <div v-else-if="!loading && rawRecords.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>当前批改结果表为空，请先前往【智能作业批改】完成 AI 判卷。</p>
    </div>

    <template v-else>
      <template v-if="isWebTeacher">
        <div class="kpi-cards">
          <div class="kpi-card">
            <div class="kpi-title">已测评网站总数</div>
            <div class="kpi-value text-slate-800">{{ webStats.totalProjects }} <span class="unit">个</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">📱 响应式设计合格率</div>
            <div class="kpi-value text-emerald-600">{{ webStats.responsivePassRate }} <span class="unit">%</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">⚠️ 班级架构最薄弱项</div>
            <div class="kpi-value warning-text" style="font-size: 16px;">{{ webStats.weakestDimension }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">🎨 UI均分最高优势项</div>
            <div class="kpi-value text-blue-600" style="font-size: 16px;">{{ webStats.strongestDimension }}</div>
          </div>
        </div>

        <div class="charts-grid">
          <div class="chart-card full-width">
            <div class="chart-title">🏆 班级学生综合评分排行大盘</div>
            <div ref="webScoreBarRef" class="chart-container" style="height: 320px;"></div>
          </div>

          <div class="chart-card">
            <div class="chart-title">📊 班级前沿五维能级平均分</div>
            <div ref="webBarRef" class="chart-container" style="height: 350px;"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">🕸️ 全班前端设计综合实力热力网络</div>
            <div ref="webRadarRef" class="chart-container" style="height: 350px;"></div>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="kpi-cards">
          <div class="kpi-card">
            <div class="kpi-title">已批改总题数</div>
            <div class="kpi-value text-slate-800">{{ normalStats.total }} <span class="unit">题</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">班级综合正确率</div>
            <div class="kpi-value text-emerald-600">{{ normalStats.overall_correct_rate }} <span class="unit">%</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">最薄弱知识点</div>
            <div class="kpi-value warning-text" :title="normalStats.worstKp">{{ normalStats.worstKp }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">最高频错因</div>
            <div class="kpi-value warning-text" :title="normalStats.topError">{{ normalStats.topError }}</div>
          </div>
        </div>

        <div class="charts-grid">
          <div class="chart-card full-width">
            <div class="chart-title">🏆 班级学生成绩评分排行大盘</div>
            <div ref="normalScoreBarRef" class="chart-container" style="height: 300px;"></div>
          </div>

          <div class="chart-card">
            <div class="chart-title">🎯 核心共性错因分布</div>
            <div ref="pieRef" class="chart-container"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">📊 各题目错题量分布</div>
            <div ref="barRef" class="chart-container"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">📉 知识点薄弱分布排行</div>
            <div ref="hbarRef" class="chart-container"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">🕸️ 班级综合能力画像</div>
            <div ref="radarRef" class="chart-container"></div>
          </div>
        </div>
      </template>

      <div class="filter-console mt-5">
        <span class="filter-label">🔍 快速多维筛选</span>
        <div class="filter-group">
          <!-- 🌟 核心优化：智能双轨分流的下拉选项 -->
          <select v-model="filterStatus">
            <option value="ALL">所有状态</option>
            <template v-if="isWebTeacher">
              <option value="EXCELLENT">🟢 优秀 (90分及以上)</option>
              <option value="GOOD">🔵 良好 (80-89分)</option>
              <option value="PASS">🟠 及格 (60-79分)</option>
              <option value="POOR">🔴 待优化 (60分以下)</option>
            </template>
            <template v-else>
              <option value="PASS">✅ 回答正确</option>
              <option value="FAIL">❌ 回答错误</option>
            </template>
          </select>
        </div>
        <div class="filter-result-count">
          当前检索出 <strong>{{ filteredRecords.length }}</strong> 条明细
        </div>
      </div>

      <div class="data-table-wrapper">
        <table class="styled-table">
          <thead>
            <tr>
              <th style="width: 15%">学生姓名</th>
              <th style="width: 12%">题号/项目</th>
              <th style="width: 18%">核心考点</th>
              <th style="width: 15%">{{ isWebTeacher ? '评分与状态' : '状态' }}</th>
              <th style="width: 40%">{{ isWebTeacher ? '🖥️ 资深前端架构师评审详报' : 'AI 智能错因诊断' }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(record, idx) in filteredRecords" :key="'record_'+idx">
              <td class="font-bold">🧑 {{ (record.student_name || '未知学生').replace('-UI评测','') }}</td>
              <td class="font-bold-q">{{ record.question_number === '综合评测' ? '网页作品' : (record.question_number || '未知') }}</td>
              <td><span class="kp-tag">{{ record.knowledge_point || '无考点' }}</span></td>
              <td>
                <!-- 🌟 核心优化：与筛选器同色的四档徽章 -->
                <div v-if="isWebTeacher" class="project-score-badge">
                  <span class="proj-score">{{ getProjectScore(record.error_cause) }} <span class="proj-unit">分</span></span>
                  <span class="proj-eval" :class="getWebEvalClass(getProjectScore(record.error_cause))">
                    {{ getWebEvalText(getProjectScore(record.error_cause)) }}
                  </span>
                </div>
                <div v-else>
                   <span class="proj-eval" :class="checkPass(record.is_correct) ? 'pass-tag' : 'fail-tag'">
                    {{ checkPass(record.is_correct) ? '✅ 正确' : '❌ 错误' }}
                  </span>
                </div>
              </td>
              <td :class="checkPass(record.is_correct) ? 'no-error' : 'error-cause'">
                <div class="clamped-text" :title="getCleanFeedback(record.error_cause)">
                  {{ getCleanFeedback(record.error_cause) }}
                </div>
              </td>
            </tr>
            <tr v-if="filteredRecords.length === 0">
              <td colspan="5" class="no-data-cell">没有找到符合筛选条件的作答记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, nextTick, watch } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';
import { globalStore } from '../../store';

const API_BASE_URL = 'http://localhost:8000/api/homework';
const loading = ref(false);

const rawRecords = ref([]);
const filterStatus = ref('ALL');

const pieRef = ref(null);
const barRef = ref(null);
const hbarRef = ref(null);
const radarRef = ref(null);
const webBarRef = ref(null);
const webRadarRef = ref(null);
const webScoreBarRef = ref(null);
const normalScoreBarRef = ref(null);

let chartInstances = {};

const isWebTeacher = computed(() => globalStore.auth.role === 'web_teacher');

const checkPass = (status) => {
  const s = String(status || '').trim();
  return s === '正确' || s.includes('部分正确') || s.includes('基本正确') || s.includes('合格') || s === 'true';
};

const getCleanFeedback = (text) => {
  if (!text) return '无';
  let clean = String(text).replace(/`{3}json_array[\s\S]*?`{3}/g, '')
                  .replace(/`{3}json[\s\S]*?`{3}/g, '')
                  .replace(/#/g, '')
                  .replace(/\*/g, '')
                  .trim();
  return clean || '已完成评测';
};

const getProjectScore = (errorCause) => {
  if (!errorCause) return 0;
  try {
    const match = String(errorCause).match(/`{3}json([\s\S]*?)`{3}/);
    let jsonObj = match ? JSON.parse(match[1].trim()) : null;
    if (!jsonObj) {
      const start = String(errorCause).indexOf('{');
      const end = String(errorCause).lastIndexOf('}');
      if (start !== -1 && end !== -1) {
        const possibleJson = String(errorCause).substring(start, end + 1);
        if (possibleJson.includes('"radar"')) jsonObj = JSON.parse(possibleJson);
      }
    }
    if (jsonObj && jsonObj.series?.[0]?.data?.[0]?.value) {
      const vals = jsonObj.series[0].data[0].value;
      return Math.round(vals.reduce((a, b) => Number(a) + Number(b), 0) / vals.length);
    }
  } catch(e) {}
  return 0;
};

// 🌟 新增：表格状态徽章配色助手
const getWebEvalClass = (score) => {
  if (score >= 90) return 'eval-excellent';
  if (score >= 80) return 'eval-good';
  if (score >= 60) return 'eval-pass';
  return 'eval-poor';
};

const getWebEvalText = (score) => {
  if (score >= 90) return '🟢 优秀';
  if (score >= 80) return '🔵 良好';
  if (score >= 60) return '🟠 及格';
  return '🔴 优化';
};

// 🌟 核心优化：动态打分筛选计算逻辑
const filteredRecords = computed(() => {
  return rawRecords.value.filter(record => {
    if (filterStatus.value === 'ALL') return true;

    if (isWebTeacher.value) {
      const score = getProjectScore(record.error_cause);
      if (filterStatus.value === 'EXCELLENT') return score >= 90;
      if (filterStatus.value === 'GOOD') return score >= 80 && score < 90;
      if (filterStatus.value === 'PASS') return score >= 60 && score < 80;
      if (filterStatus.value === 'POOR') return score < 60;
      return true;
    } else {
      const isPassed = checkPass(record.is_correct);
      if (filterStatus.value === 'PASS') return isPassed;
      if (filterStatus.value === 'FAIL') return !isPassed;
      return true;
    }
  });
});

const studentScores = computed(() => {
  const map = {};
  filteredRecords.value.forEach(r => {
    const sName = (r.student_name || '未知学生').replace('-UI评测', '');
    if (!map[sName]) map[sName] = { name: sName, total: 0, correct: 0, sumScore: 0 };
    map[sName].total++;

    if (checkPass(r.is_correct)) {
      map[sName].correct++;
    }
    if (isWebTeacher.value) {
      map[sName].sumScore += getProjectScore(r.error_cause);
    }
  });

  return Object.values(map).map(stu => {
    let score = 0;
    if (isWebTeacher.value) {
      score = stu.total > 0 ? Math.round(stu.sumScore / stu.total) : 0;
    } else {
      score = stu.total > 0 ? Math.round((stu.correct / stu.total) * 100) : 0;
    }
    return { ...stu, score };
  }).sort((a, b) => b.score - a.score);
});

const webStats = computed(() => {
  if (!isWebTeacher.value) return {};
  const totals = { "UI美观度": 0, "响应式适配": 0, "语义化与规范": 0, "性能与体验": 0, "交互逻辑": 0 };
  const counts = { "UI美观度": 0, "响应式适配": 0, "语义化与规范": 0, "性能与体验": 0, "交互逻辑": 0 };
  let responsivePassCount = 0; let totalProjects = 0;

  filteredRecords.value.forEach(r => {
    if (!r.error_cause) return;
    let jsonObj = null;
    try {
      const match = String(r.error_cause).match(/`{3}json([\s\S]*?)`{3}/);
      if (match) jsonObj = JSON.parse(match[1].trim());
      else {
        const start = String(r.error_cause).indexOf('{'); const end = String(r.error_cause).lastIndexOf('}');
        if (start !== -1 && end !== -1) {
          const possibleJson = String(r.error_cause).substring(start, end + 1);
          if (possibleJson.includes('"radar"')) jsonObj = JSON.parse(possibleJson);
        }
      }
    } catch (e) { }

    if (jsonObj) {
      totalProjects++;
      const values = jsonObj.series?.[0]?.data?.[0]?.value || [];
      const indicators = jsonObj.radar?.indicator || [];
      indicators.forEach((ind, index) => {
        const rawName = String(ind.name || ''); let matchedKey = null;
        if (rawName.includes('UI') || rawName.includes('美观')) matchedKey = 'UI美观度';
        else if (rawName.includes('响应')) matchedKey = '响应式适配';
        else if (rawName.includes('语义') || rawName.includes('规范')) matchedKey = '语义化与规范';
        else if (rawName.includes('性能') || rawName.includes('体验')) matchedKey = '性能与体验';
        else if (rawName.includes('交互') || rawName.includes('逻辑')) matchedKey = '交互逻辑';
        if (matchedKey) {
          const val = Number(values[index]) || 0; totals[matchedKey] += val; counts[matchedKey]++;
          if (matchedKey === "响应式适配" && val >= 60) responsivePassCount++;
        }
      });
    }
  });

  const averages = {};
  Object.keys(totals).forEach(k => { averages[k] = counts[k] > 0 ? Math.round(totals[k] / counts[k]) : 0; });
  const validAverages = Object.entries(averages).filter(a => counts[a[0]] > 0);
  const sorted = validAverages.sort((a, b) => a[1] - b[1]);
  const weakestDimension = sorted.length > 0 ? `${sorted[0][0]} (${sorted[0][1]}分)` : '暂无数据';
  const strongestDimension = sorted.length > 0 ? `${sorted[sorted.length - 1][0]} (${sorted[sorted.length - 1][1]}分)` : '暂无数据';
  const responsivePassRate = totalProjects > 0 ? Math.round((responsivePassCount / totalProjects) * 100) : 0;

  return { totalProjects, responsivePassRate, weakestDimension, strongestDimension, averages };
});

const normalStats = computed(() => {
  if (isWebTeacher.value) return {};
  let correctCount = 0; const errorCounts = {}; const kpStats = {};
  filteredRecords.value.forEach(r => {
    const isPassed = checkPass(r.is_correct);
    if (isPassed) correctCount++;
    if (!isPassed && r.error_cause && r.error_cause !== '无') {
      let shortCause = getCleanFeedback(r.error_cause);
      if (shortCause.length > 12) shortCause = shortCause.substring(0, 12) + '...';
      errorCounts[shortCause] = (errorCounts[shortCause] || 0) + 1;
    }
    const kp = String(r.knowledge_point || '').trim();
    if (kp && kp !== '-' && kp !== '未归类') {
      if (!kpStats[kp]) kpStats[kp] = { total: 0, correct: 0 };
      kpStats[kp].total++; if (isPassed) kpStats[kp].correct++;
    }
  });
  const overall_correct_rate = filteredRecords.value.length > 0 ? Math.round((correctCount / filteredRecords.value.length) * 100) : 0;
  const topError = Object.entries(errorCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '暂无数据';
  const kpMastery = Object.entries(kpStats).map(([kp, c]) => ({ knowledge_point: kp, rate: Math.round((c.correct/c.total)*100), error_rate: Math.round(((c.total-c.correct)/c.total)*100) })).sort((a, b) => b.error_rate - a.error_rate);
  return { total: filteredRecords.value.length, overall_correct_rate, topError, worstKp: kpMastery[0]?.knowledge_point || '暂无数据', kpMastery, errorCounts };
});

const getDynamicColor = (score) => {
  if (score >= 90) return '#10b981'; // 优秀：绿
  if (score >= 80) return '#3b82f6'; // 良好：蓝
  if (score >= 60) return '#f59e0b'; // 及格：橙
  return '#ef4444'; // 待优化：红
};

const renderCharts = () => {
  Object.values(chartInstances).forEach(c => c && c.dispose());
  chartInstances = {};

  if (isWebTeacher.value) {
    if (webScoreBarRef.value && studentScores.value.length > 0) {
      chartInstances.webScoreBar = echarts.init(webScoreBarRef.value);
      const names = studentScores.value.map(s => s.name);
      const scores = studentScores.value.map(s => s.score);

      chartInstances.webScoreBar.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}: {c}分' },
        grid: { top: '15%', bottom: '20%', left: '5%', right: '5%', containLabel: true },
        xAxis: { type: 'category', data: names, axisLabel: { interval: 0, rotate: names.length > 5 ? 25 : 0, fontWeight: 'bold' } },
        yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { type: 'dashed' } } },
        series: [{
          type: 'bar',
          data: scores.map(s => ({ value: s, itemStyle: { color: getDynamicColor(s) } })),
          barWidth: 35,
          itemStyle: { borderRadius: [6, 6, 0, 0] },
          label: { show: true, position: 'top', formatter: '{c}分', fontWeight: 'bold', fontSize: 13 }
        }]
      });
    }

    if (webBarRef.value && webRadarRef.value) {
      chartInstances.webBar = echarts.init(webBarRef.value); chartInstances.webRadar = echarts.init(webRadarRef.value);
      const dimensions = Object.keys(webStats.value.averages); const values = Object.values(webStats.value.averages);
      chartInstances.webBar.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}: {c}分' }, grid: { top: '15%', bottom: '15%', left: '5%', right: '5%', containLabel: true },
        xAxis: { type: 'category', data: dimensions, axisLabel: { fontSize: 12, fontWeight: 'bold' } }, yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { type: 'dashed' } } },
        series: [{ type: 'bar', data: values, barWidth: 35, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#10b981' }, { offset: 1, color: '#047857' }]), borderRadius: [6, 6, 0, 0] }, label: { show: true, position: 'top', formatter: '{c}分', color: '#1e293b', fontWeight: 'bold' } }]
      });
      chartInstances.webRadar.setOption({
        tooltip: { trigger: 'item' }, radar: { indicator: dimensions.map(d => ({ name: d, max: 100 })), radius: '65%', center: ['50%', '50%'] },
        series: [{ type: 'radar', data: [{ value: values, name: '全班技术均分', areaStyle: { color: 'rgba(16, 185, 129, 0.3)' }, lineStyle: { color: '#10b981', width: 2 }, symbolSize: 6 }] }]
      });
    }
  } else {
    if (normalScoreBarRef.value && studentScores.value.length > 0) {
      chartInstances.normalScoreBar = echarts.init(normalScoreBarRef.value);
      const names = studentScores.value.map(s => s.name);
      const scores = studentScores.value.map(s => s.score);

      chartInstances.normalScoreBar.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}: {c}分' },
        grid: { top: '15%', bottom: '20%', left: '5%', right: '5%', containLabel: true },
        xAxis: { type: 'category', data: names, axisLabel: { interval: 0, rotate: names.length > 5 ? 25 : 0, fontWeight: 'bold' } },
        yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { type: 'dashed' } } },
        series: [{
          type: 'bar',
          data: scores.map(s => ({ value: s, itemStyle: { color: getDynamicColor(s) } })),
          barWidth: 35,
          itemStyle: { borderRadius: [6, 6, 0, 0] },
          label: { show: true, position: 'top', formatter: '{c}分', fontWeight: 'bold', fontSize: 13 }
        }]
      });
    }

    if (pieRef.value && barRef.value && hbarRef.value && radarRef.value) {
      chartInstances.pie = echarts.init(pieRef.value); chartInstances.bar = echarts.init(barRef.value); chartInstances.hbar = echarts.init(hbarRef.value); chartInstances.radar = echarts.init(radarRef.value);
      const pieData = Object.entries(normalStats.value.errorCounts).map(([cause, count]) => ({name: cause, value: count})).sort((a, b) => b.value - a.value);
      chartInstances.pie.setOption({ tooltip: {trigger: 'item'}, series: [{ type: 'pie', radius: ['40%', '70%'], itemStyle: {borderRadius: 8, borderColor: '#fff', borderWidth: 2}, data: pieData.length ? pieData : [{name: '无错题', value: 0}] }] });
      const errMap = {}; filteredRecords.value.forEach(r => { if (!checkPass(r.is_correct)) { const q = String(r.question_number || '未知'); errMap[q] = (errMap[q] || 0) + 1; } });
      const qKeys = Object.keys(errMap).sort((a, b) => a.localeCompare(b, 'zh-CN', {numeric: true}));
      chartInstances.bar.setOption({ tooltip: {trigger: 'axis'}, grid: {left: '5%', right: '5%', bottom: '10%', containLabel: true}, xAxis: {type: 'category', data: qKeys}, yAxis: {type: 'value', minInterval: 1}, series: [{ type: 'bar', data: qKeys.map(k => errMap[k]), barWidth: 20, itemStyle: { color: '#10b981', borderRadius: [4,4,0,0] } }] });
      const worstKps = normalStats.value.kpMastery.slice(0, 5).reverse();
      chartInstances.hbar.setOption({ tooltip: {trigger: 'axis', formatter: '{b}: 错误率 {c}%'}, grid: {left: '5%', right: '15%', bottom: '5%', containLabel: true}, xAxis: {type: 'value', max: 100}, yAxis: { type: 'category', data: worstKps.map(k => k.knowledge_point.substring(0, 8)) }, series: [{ type: 'bar', data: worstKps.map(k => k.error_rate), label: {show: true, position: 'right', formatter: '{c}%'}, itemStyle: {color: '#ef4444', borderRadius: [0,4,4,0]} }] });
      chartInstances.radar.setOption({ tooltip: {trigger: 'item'}, radar: { indicator: normalStats.value.kpMastery.map(k => ({name: k.knowledge_point.substring(0, 6), max: 100})).slice(0,6), radius: '60%' }, series: [{ type: 'radar', data: [{ value: normalStats.value.kpMastery.slice(0,6).map(k => k.rate), areaStyle: {color: 'rgba(16, 185, 129, 0.2)'}, lineStyle: {color: '#10b981'}, itemStyle: {color: '#10b981'} }] }] });
    }
  }
};

watch(filteredRecords, async () => { if (rawRecords.value.length > 0) { await nextTick(); renderCharts(); } }, { deep: true, immediate: true });
const handleResize = () => Object.values(chartInstances).forEach(c => c && c.resize());

const loadDashboardStats = async (forceSync = false, isAutoSync = false) => {
  const token = globalStore.config.feishuToken;
  if (!token || loading.value) return;

  if (globalStore.tableDataCache[token] && !forceSync) {
    rawRecords.value = globalStore.tableDataCache[token].rawRecords;
  }

  loading.value = true;
  try {
    if (isAutoSync) await new Promise(resolve => setTimeout(resolve, 800));

    const res = await axios.post(`${API_BASE_URL}/get_dashboard_stats`, { feishu_app_id: globalStore.config.feishuAppId, feishu_app_secret: globalStore.config.feishuAppSecret, app_token: token });
    if (res.data.status === 'success') {
      rawRecords.value = res.data.stats.raw_records || [];
      globalStore.tableDataCache[token] = { rawRecords: rawRecords.value };
    }
  } catch (error) { console.error("加载大盘数据失败:", error); } finally { loading.value = false; }
};

onMounted(() => { if (globalStore.config.feishuToken) loadDashboardStats(true); window.addEventListener('resize', handleResize); });
onActivated(() => { if (globalStore.config.feishuToken) loadDashboardStats(true, true); });
onUnmounted(() => { window.removeEventListener('resize', handleResize); Object.values(chartInstances).forEach(c => c && c.dispose()); });
</script>

<style scoped>
@keyframes spin { 100% { transform: rotate(360deg); } }
.is-spinning { animation: spin 1s linear infinite; }

.analytics-dashboard { display: flex; flex-direction: column; gap: 20px; min-height: 100%; padding-bottom: 20px; position: relative;}
.dashboard-header { display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); padding: 20px 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #edf2f7; }
.title-area h3 { margin: 0 0 6px 0; font-size: 20px; color: #1a202c; font-weight: 700; }
.title-area p { margin: 0; font-size: 13px; color: #718096; }
.btn-sync { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e2e8f0; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; color: #4a5568; transition: all 0.2s ease; }
.btn-sync:hover:not(:disabled) { color: #1890ff; border-color: #1890ff; background: #f0f7ff; box-shadow: 0 4px 12px rgba(24,144,255,0.1); transform: translateY(-1px); }
.btn-sync:disabled { background: #f8fafc; color: #cbd5e1; cursor: not-allowed; }

.kpi-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.kpi-card { background: #fff; padding: 24px 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #edf2f7; transition: transform 0.3s ease, box-shadow 0.3s ease; display: flex; flex-direction: column; gap: 8px;}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); border-color: #cbd5e1; }
.kpi-title { font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;}
.kpi-value { font-size: 28px; font-weight: 900; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;}
.unit { font-size: 14px; font-weight: 700; color: #94a3b8; margin-left: 2px; }

.text-slate-800 { color: #1e293b; }
.text-emerald-600 { color: #059669; }
.text-blue-600 { color: #2563eb; }
.warning-text { color: #dc2626; }

.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 10px;}
.chart-card { background: #fff; border-radius: 12px; border: 1px solid #edf2f7; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); transition: 0.3s;}
.chart-card:hover { border-color: #cbd5e1; box-shadow: 0 8px 24px rgba(0,0,0,0.05); }
.chart-card.full-width { grid-column: span 2; }
.chart-title { font-size: 15px; font-weight: 800; color: #334155; margin-bottom: 16px; display: flex; align-items: center; gap: 6px;}
.chart-container { width: 100%; height: 280px; }

.filter-console { display: flex; align-items: center; gap: 20px; background: #fff; padding: 16px 24px; border-radius: 12px; border: 1px solid #edf2f7; box-shadow: 0 4px 20px rgba(0,0,0,0.03); flex-wrap: wrap; }
.filter-label { font-weight: 800; color: #1e293b; font-size: 14px; }
.filter-group { display: flex; gap: 12px; flex: 1; flex-wrap: wrap; }
.filter-group select { padding: 10px 14px; border: 1.5px solid #cbd5e1; border-radius: 8px; font-size: 13px; font-weight: 600; color: #475569; outline: none; transition: 0.2s; min-width: 150px; background: #f8fafc; cursor: pointer; }
.filter-group select:focus { border-color: #3b82f6; background: #fff; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.filter-result-count { font-size: 14px; color: #64748b; font-weight: 600;}
.filter-result-count strong { color: #2563eb; font-size: 16px; font-weight: 900;}

.mt-5 { margin-top: 20px; }
.data-table-wrapper { background: #fff; border-radius: 12px; border: 1px solid #edf2f7; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
.styled-table { width: 100%; border-collapse: collapse; text-align: left; table-layout: fixed; }
.styled-table thead tr { background: #f8fafc; }
.styled-table th { padding: 16px; font-size: 13px; font-weight: 800; color: #475569; border-bottom: 1px solid #edf2f7; }
.styled-table td { padding: 16px; border-bottom: 1px solid #edf2f7; font-size: 14px; color: #334155; line-height: 1.6; }
.styled-table tbody tr:hover { background: #f1f5f9; }
.font-bold { font-weight: 700; color: #1e293b; }
.font-bold-q { font-weight: 800; color: #3b82f6; }
.kp-tag { background: #eff6ff; color: #2563eb; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; white-space: nowrap; border: 1px solid #bfdbfe;}

.project-score-badge { display: inline-flex; align-items: center; gap: 8px; background: #fff; padding: 4px 6px 4px 12px; border-radius: 20px; border: 1px solid #e2e8f0; }
.proj-score { font-size: 14px; font-weight: 900; color: #0f172a; }
.proj-unit { font-size: 11px; color: #94a3b8; font-weight: bold; }
.proj-eval { font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 16px; }

/* 🌟 核心优化：四档彩色徽章样式集 */
.eval-excellent { color: #059669; background: #ecfdf5; }
.eval-good { color: #2563eb; background: #eff6ff; }
.eval-pass { color: #d97706; background: #fffbeb; }
.eval-poor { color: #dc2626; background: #fef2f2; }

/* 兼容普通老师的传统对错标签 */
.pass-tag { color: #166534; background: #dcfce3; }
.fail-tag { color: #dc2626; background: #fef2f2; }

.clamped-text { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; white-space: normal; word-break: break-all; font-size: 13px; color: #475569; }
.error-cause { color: #b91c1c; font-weight: 500;}
.no-error { color: #15803d; font-weight: 500;}

.loading-state, .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 350px; color: #94a3b8; font-weight: 600;}
.empty-icon { font-size: 50px; margin-bottom: 20px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.05)); }
.spinner { width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
.no-data-cell { text-align: center; color: #94a3b8; padding: 40px !important; }
</style>