<template>
  <div class="analytics-dashboard" :class="{ 'is-dark': darkMode }">
    <!-- ─── 顶栏：标题 + 主题切换 + 同步 ─── -->
    <div class="dashboard-header">
      <div class="title-area">
        <h3>📈 教研学情多维透视面板</h3>
        <p>{{ isWebTeacher ? '前端响应式设计规范与 UI/UX 体验能级评估大屏' : '基于 AI 逐题诊断的班级学情数据汇总与可视化图表' }}</p>
      </div>
      <div class="header-actions">
        <div class="theme-switch">
          <button :class="{ active: !darkMode }" @click="setDark(false)">☀️ 报表</button>
          <button :class="{ active: darkMode }" @click="setDark(true)">🌙 大屏</button>
        </div>
        <button class="btn-sync" @click="loadDashboardStats(true)" :disabled="loading">
          <span class="sync-icon" :class="{ 'is-spinning': loading }">🔄</span>
          {{ loading ? '云端同步中...' : '强制同步飞书最新数据' }}
        </button>
      </div>
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
      <!-- ╔══════════════════════════════════════════════╗
           ║  🌙 大屏模式：投屏面板（隐藏后台筛选/明细）  ║
           ╚══════════════════════════════════════════════╝ -->
      <div v-if="darkMode" class="bigscreen-shell">
        <!-- 顶部条：班级标题 + 实时时钟 -->
        <div class="bs-topbar">
          <div class="bs-class">
            <span class="bs-class-icon">🏫</span>
            <div>
              <strong>{{ globalStore.auth.subject || '学情分析大屏' }}</strong>
              <small>{{ activeTableName }}</small>
            </div>
          </div>
          <div class="bs-clock">
            <span class="bs-time">{{ clockTime }}</span>
            <small>{{ clockDate }}</small>
          </div>
        </div>

        <!-- KPI 巨型卡片 -->
        <div class="bs-kpi-row">
          <div v-for="(k, i) in (isWebTeacher ? webKpiList : normalKpiList)" :key="k.title" class="bs-kpi" :class="'kpi-' + i">
            <div class="bs-kpi-label">{{ k.title }}</div>
            <div class="bs-kpi-num" :class="k.cls">
              <span class="num">{{ k.value }}</span>
              <span v-if="k.unit" class="unit">{{ k.unit }}</span>
            </div>
            <div class="bs-kpi-glow"></div>
          </div>
        </div>

        <!-- 主视觉区：左 主图 / 中 AI摘要 / 右 风险榜 -->
        <div class="bs-main">
          <div class="bs-main-left">
            <div class="bs-panel">
              <div class="bs-panel-title">
                🏆 班级综合评分排行
                <span class="bs-panel-sub">基于当前筛选数据 · 共 {{ studentScores.length }} 人</span>
              </div>
              <div ref="bsMainBarRef" class="bs-chart" style="height: 320px;"></div>
            </div>

            <div class="bs-panel" v-if="!isWebTeacher">
              <div class="bs-panel-title">
                🔥 知识点 × 学生 热力图
                <span class="bs-panel-sub">色越深 = 错误率越高</span>
              </div>
              <div ref="bsHeatRef" class="bs-chart" style="height: 280px;"></div>
            </div>

            <div class="bs-panel" v-else>
              <div class="bs-panel-title">
                🕸️ 五维能力雷达
                <span class="bs-panel-sub">全班均分</span>
              </div>
              <div ref="bsRadarRef" class="bs-chart" style="height: 280px;"></div>
            </div>
          </div>

          <div class="bs-main-mid">
            <div class="bs-panel bs-ai">
              <div class="bs-panel-title">
                🤖 AI 学情摘要
                <button class="bs-mini-btn" @click="generateAiSummary" :disabled="aiLoading || !globalStore.config.apiKey">
                  {{ aiLoading ? '生成中…' : (aiSummary ? '🔁 重生成' : '✨ 生成') }}
                </button>
              </div>
              <div v-if="aiSummary" class="bs-ai-text" v-html="renderMarkdownLite(aiSummary)"></div>
              <div v-else class="bs-ai-empty">
                <span class="bs-ai-empty-icon">💭</span>
                <p>{{ globalStore.config.apiKey ? '点击右上"生成"即可让 AI 总结当前学情' : '请先配置大模型 API Key' }}</p>
              </div>
            </div>

            <div class="bs-panel bs-secondary" v-if="!isWebTeacher">
              <div class="bs-panel-title">🎯 共性错因 TOP 5</div>
              <div class="bs-top-list">
                <div v-for="(item, i) in topErrors" :key="item.name" class="bs-top-row">
                  <span class="bs-top-rank">{{ i + 1 }}</span>
                  <span class="bs-top-name" :title="item.name">{{ item.name }}</span>
                  <span class="bs-top-bar"><span :style="{ width: (item.value / (topErrors[0]?.value || 1)) * 100 + '%' }"></span></span>
                  <span class="bs-top-val">{{ item.value }}</span>
                </div>
                <div v-if="topErrors.length === 0" class="bs-top-empty">暂无错因数据</div>
              </div>
            </div>

            <div class="bs-panel bs-secondary" v-else>
              <div class="bs-panel-title">📊 五维能力均分</div>
              <div class="bs-top-list">
                <div v-for="(v, name) in (webStats.averages || {})" :key="name" class="bs-top-row">
                  <span class="bs-top-name">{{ name }}</span>
                  <span class="bs-top-bar"><span :style="{ width: v + '%', background: getDynamicColor(v) }"></span></span>
                  <span class="bs-top-val" :style="{ color: getDynamicColor(v) }">{{ v }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="bs-main-right">
            <div class="bs-panel bs-risk">
              <div class="bs-panel-title">
                🚨 班级风险预警榜
                <span class="bs-risk-count">{{ riskStudents.length }} 人</span>
              </div>
              <div v-if="riskStudents.length === 0" class="bs-risk-empty">
                🎉 全员表现良好<br/>暂无风险预警
              </div>
              <div v-else class="bs-risk-list">
                <div v-for="(stu, i) in riskStudents.slice(0, 10)" :key="stu.name" class="bs-risk-item">
                  <span class="bs-risk-rank">#{{ i + 1 }}</span>
                  <span class="bs-risk-name">{{ stu.name.replace('-UI评测','') }}</span>
                  <span class="bs-risk-score" :style="{ color: getDynamicColor(stu.score) }">{{ stu.score }}</span>
                </div>
              </div>
            </div>

            <div class="bs-panel bs-secondary">
              <div class="bs-panel-title">🏅 优等生 TOP 5</div>
              <div v-if="topStudents.length === 0" class="bs-top-empty">暂无数据</div>
              <div v-else class="bs-honor-list">
                <div v-for="(stu, i) in topStudents" :key="stu.name" class="bs-honor-row">
                  <span class="bs-honor-medal">{{ ['🥇','🥈','🥉','🏅','🏅'][i] }}</span>
                  <span class="bs-honor-name">{{ stu.name.replace('-UI评测','') }}</span>
                  <span class="bs-honor-score">{{ stu.score }} 分</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部 ticker：滚动播报薄弱知识点 -->
        <div class="bs-ticker">
          <span class="bs-ticker-tag">📢 实时学情</span>
          <div class="bs-ticker-track">
            <span class="bs-ticker-text">{{ tickerText }}</span>
          </div>
        </div>
      </div>

      <!-- ╔══════════════════════════════════════════════╗
           ║  ☀️ 报表模式：完整后台分析（KPI/筛选/明细）  ║
           ╚══════════════════════════════════════════════╝ -->
      <template v-else>
      <!-- ─── KPI 区 ─── -->
      <template v-if="isWebTeacher">
        <div class="kpi-cards">
          <div class="kpi-card" v-for="k in webKpiList" :key="k.title">
            <div class="kpi-title">{{ k.title }}</div>
            <div class="kpi-value" :class="k.cls" :style="{ fontSize: k.small ? '16px' : '' }">
              {{ k.value }} <span v-if="k.unit" class="unit">{{ k.unit }}</span>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="kpi-cards">
          <div class="kpi-card" v-for="k in normalKpiList" :key="k.title">
            <div class="kpi-title">{{ k.title }}</div>
            <div class="kpi-value" :class="k.cls" :style="{ fontSize: k.small ? '16px' : '' }" :title="k.value">
              {{ k.value }} <span v-if="k.unit" class="unit">{{ k.unit }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- ─── AI 学情摘要卡 + 风险榜 ─── -->
      <div class="ai-risk-row">
        <div class="ai-summary-card">
          <div class="card-head">
            <span class="card-icon">🤖</span>
            <strong>AI 学情摘要</strong>
            <button class="mini-btn" @click="generateAiSummary" :disabled="aiLoading">
              {{ aiLoading ? '🔄 生成中…' : (aiSummary ? '🔁 重新生成' : '✨ 生成 AI 总结') }}
            </button>
          </div>
          <div v-if="aiSummary" class="ai-text" v-html="renderMarkdownLite(aiSummary)"></div>
          <div v-else-if="aiLoading" class="ai-placeholder">
            <div class="dot-flow"><span></span><span></span><span></span></div>
            正在调用 ChatBI 引擎，基于当前过滤数据生成班级摘要…
          </div>
          <div v-else class="ai-placeholder">
            点击右上角"生成 AI 总结"，AI 将根据当前筛选数据生成一段班级学情评估与教学建议。
            <small v-if="!globalStore.config.apiKey">⚠️ 请先在右侧面板配置大模型 API Key</small>
          </div>
        </div>

        <div class="risk-list-card">
          <div class="card-head">
            <span class="card-icon">🚨</span>
            <strong>班级风险预警榜</strong>
            <span class="risk-count">{{ riskStudents.length }} 人</span>
          </div>
          <div v-if="riskStudents.length === 0" class="risk-empty">🎉 全员表现良好，暂无风险预警</div>
          <div v-else class="risk-list">
            <div v-for="(stu, i) in riskStudents" :key="stu.name" class="risk-item">
              <span class="risk-rank">#{{ i + 1 }}</span>
              <span class="risk-name">{{ stu.name.replace('-UI评测','') }}</span>
              <span class="risk-score" :style="{ color: getDynamicColor(stu.score) }">{{ stu.score }} 分</span>
              <button class="risk-jump" @click="filterByStudent(stu.name)" title="筛选该学生的明细">🔍</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ─── 图表区 ─── -->
      <template v-if="isWebTeacher">
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
          <div class="chart-card full-width">
            <div class="chart-title">🔥 知识点掌握热力图（横轴=学生，纵轴=知识点，色越深=正确率越低）</div>
            <div ref="heatmapRef" class="chart-container" style="height: 360px;"></div>
          </div>
        </div>
      </template>

      <!-- ─── 多维筛选控制台 ─── -->
      <div class="filter-console mt-5">
        <span class="filter-label">🔍 多维筛选</span>
        <div class="filter-group">
          <select v-model="filterStatus">
            <option value="ALL">所有状态</option>
            <template v-if="isWebTeacher">
              <option value="EXCELLENT">🟢 优秀 (90+)</option>
              <option value="GOOD">🔵 良好 (80-89)</option>
              <option value="PASS">🟠 及格 (60-79)</option>
              <option value="POOR">🔴 待优化 (&lt;60)</option>
            </template>
            <template v-else>
              <option value="PASS">✅ 回答正确</option>
              <option value="FAIL">❌ 回答错误</option>
            </template>
          </select>

          <select v-model="filterStudent">
            <option value="">全部学生</option>
            <option v-for="s in studentNameOptions" :key="s" :value="s">{{ s.replace('-UI评测','') }}</option>
          </select>

          <select v-if="!isWebTeacher" v-model="filterKp">
            <option value="">全部知识点</option>
            <option v-for="kp in kpOptions" :key="kp" :value="kp">{{ kp }}</option>
          </select>

          <select v-model="filterQ">
            <option value="">全部题号</option>
            <option v-for="q in questionOptions" :key="q" :value="q">{{ q }}</option>
          </select>

          <select v-model="filterScoreRange">
            <option value="">全部分数段</option>
            <option value="90-100">90-100 分</option>
            <option value="80-89">80-89 分</option>
            <option value="60-79">60-79 分</option>
            <option value="0-59">0-59 分</option>
          </select>

          <label class="toggle-pill">
            <input type="checkbox" v-model="onlyWrong" />
            <span>只看错题</span>
          </label>
          <label class="toggle-pill">
            <input type="checkbox" v-model="onlyRisk" />
            <span>只看高风险学生</span>
          </label>
          <button v-if="hasAnyFilter" class="reset-btn" @click="resetFilters">✕ 重置筛选</button>
        </div>
        <div class="filter-result-count">
          当前检索出 <strong>{{ filteredRecords.length }}</strong> 条明细
        </div>
      </div>

      <!-- ─── 明细表 ─── -->
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
            <tr v-for="(record, idx) in pagedRecords" :key="'record_'+idx">
              <td class="font-bold">🧑 {{ (record.student_name || '未知学生').replace('-UI评测','') }}</td>
              <td class="font-bold-q">{{ record.question_number === '综合评测' ? '网页作品' : (record.question_number || '未知') }}</td>
              <td><span class="kp-tag">{{ record.knowledge_point || '无考点' }}</span></td>
              <td>
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

        <!-- 分页（>50 条才显示） -->
        <div v-if="filteredRecords.length > PAGE_SIZE" class="pager">
          <button @click="page = Math.max(1, page - 1)" :disabled="page === 1">‹ 上一页</button>
          <span>第 {{ page }} / {{ totalPages }} 页 · 共 {{ filteredRecords.length }} 条</span>
          <button @click="page = Math.min(totalPages, page + 1)" :disabled="page === totalPages">下一页 ›</button>
        </div>
      </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, nextTick, watch, shallowRef } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';
import { globalStore } from '../../store';
import syncCenter from '../../services/syncCenter';

const API_BASE_URL = '/api/homework';
const loading = ref(false);

const rawRecords = ref([]);

// ─── 主题 ───
const DARK_KEY = 'ai_assistant_analytics_dark';
const darkMode = ref(localStorage.getItem(DARK_KEY) === '1');
const setDark = (v) => {
  darkMode.value = v;
  try { localStorage.setItem(DARK_KEY, v ? '1' : '0'); } catch (e) {}
  // 主题变了，图表样式也要跟着重渲
  scheduleRender();
};

// ─── 多维筛选 ───
const filterStatus = ref('ALL');
const filterStudent = ref('');
const filterKp = ref('');
const filterQ = ref('');
const filterScoreRange = ref('');
const onlyWrong = ref(false);
const onlyRisk = ref(false);

const hasAnyFilter = computed(() =>
  filterStatus.value !== 'ALL' || filterStudent.value || filterKp.value
  || filterQ.value || filterScoreRange.value || onlyWrong.value || onlyRisk.value);

const resetFilters = () => {
  filterStatus.value = 'ALL';
  filterStudent.value = ''; filterKp.value = '';
  filterQ.value = ''; filterScoreRange.value = '';
  onlyWrong.value = false; onlyRisk.value = false;
  page.value = 1;
};
const filterByStudent = (name) => { filterStudent.value = name; };

// ─── chart refs ───
const pieRef = ref(null);
const barRef = ref(null);
const hbarRef = ref(null);
const radarRef = ref(null);
const heatmapRef = ref(null);
const webBarRef = ref(null);
const webRadarRef = ref(null);
const webScoreBarRef = ref(null);
const normalScoreBarRef = ref(null);
// 🌟 大屏模式专用
const bsMainBarRef = ref(null);
const bsHeatRef = ref(null);
const bsRadarRef = ref(null);

const chartInstances = shallowRef({});

const isWebTeacher = computed(() => globalStore.auth.role === 'web_teacher');

// ─── helpers ───
const checkPass = (status) => {
  const s = String(status || '').trim();
  return s === '正确' || s.includes('部分正确') || s.includes('基本正确') || s.includes('合格') || s === 'true';
};

const getCleanFeedback = (text) => {
  if (!text) return '无';
  let clean = String(text).replace(/`{3}json_array[\s\S]*?`{3}/g, '')
                  .replace(/`{3}json[\s\S]*?`{3}/g, '')
                  .replace(/#/g, '').replace(/\*/g, '').trim();
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

const getWebEvalClass = (score) => score >= 90 ? 'eval-excellent' : score >= 80 ? 'eval-good' : score >= 60 ? 'eval-pass' : 'eval-poor';
const getWebEvalText = (score) => score >= 90 ? '🟢 优秀' : score >= 80 ? '🔵 良好' : score >= 60 ? '🟠 及格' : '🔴 优化';
const getDynamicColor = (score) => score >= 90 ? '#10b981' : score >= 80 ? '#3b82f6' : score >= 60 ? '#f59e0b' : '#ef4444';

// ─── 选项派生 ───
const studentNameOptions = computed(() => {
  const set = new Set();
  rawRecords.value.forEach(r => { if (r.student_name) set.add(r.student_name); });
  return Array.from(set).sort();
});
const kpOptions = computed(() => {
  const set = new Set();
  rawRecords.value.forEach(r => {
    const kp = String(r.knowledge_point || '').trim();
    if (kp && kp !== '-' && kp !== '未归类') set.add(kp);
  });
  return Array.from(set).sort();
});
const questionOptions = computed(() => {
  const set = new Set();
  rawRecords.value.forEach(r => { if (r.question_number) set.add(String(r.question_number)); });
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'zh-CN', { numeric: true }));
});

// ─── 高风险学生（score < 60，或正确率 < 60%）───
const studentScores = computed(() => {
  const map = {};
  rawRecords.value.forEach(r => {
    const sName = r.student_name || '未知学生';
    if (!map[sName]) map[sName] = { name: sName, total: 0, correct: 0, sumScore: 0 };
    map[sName].total++;
    if (checkPass(r.is_correct)) map[sName].correct++;
    if (isWebTeacher.value) map[sName].sumScore += getProjectScore(r.error_cause);
  });
  return Object.values(map).map(stu => {
    const score = isWebTeacher.value
      ? (stu.total > 0 ? Math.round(stu.sumScore / stu.total) : 0)
      : (stu.total > 0 ? Math.round((stu.correct / stu.total) * 100) : 0);
    return { ...stu, score };
  }).sort((a, b) => b.score - a.score);
});

const riskStudents = computed(() =>
  studentScores.value.filter(s => s.score < 60).sort((a, b) => a.score - b.score)
);
const riskNameSet = computed(() => new Set(riskStudents.value.map(s => s.name)));

// 🌟 大屏专用派生：优等生 TOP5 / 共性错因 TOP5
const topStudents = computed(() => studentScores.value.filter(s => s.score >= 60).slice(0, 5));
const topErrors = computed(() => {
  const counts = normalStats.value.errorCounts || {};
  return Object.entries(counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 5);
});

// 🌟 当前激活表名（顶部显示）
const activeTableName = computed(() => {
  const list = globalStore.config.bitableList || [];
  const tbl = list.find(i => i.token === globalStore.config.feishuToken);
  return tbl?.name || (globalStore.config.feishuToken ? '已绑定飞书表格' : '');
});

// 🌟 实时时钟（每秒刷新）
const clockNow = ref(new Date());
let clockTimer = null;
const clockTime = computed(() => {
  const t = clockNow.value;
  const h = String(t.getHours()).padStart(2, '0');
  const m = String(t.getMinutes()).padStart(2, '0');
  const s = String(t.getSeconds()).padStart(2, '0');
  return `${h}:${m}:${s}`;
});
const clockDate = computed(() => {
  const t = clockNow.value;
  const weekDay = ['周日','周一','周二','周三','周四','周五','周六'][t.getDay()];
  return `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')} ${weekDay}`;
});

// 🌟 底部 ticker 文案：滚动播报薄弱知识点
const tickerText = computed(() => {
  const parts = [];
  if (isWebTeacher.value) {
    parts.push(`📐 已测评 ${webStats.value.totalProjects || 0} 个网页项目`);
    if (webStats.value.weakestDimension) parts.push(`⚠️ 最薄弱维度：${webStats.value.weakestDimension}`);
    if (webStats.value.strongestDimension) parts.push(`✨ 最强维度：${webStats.value.strongestDimension}`);
  } else {
    parts.push(`📚 累计批改 ${normalStats.value.total || 0} 题`);
    parts.push(`📊 班级正确率 ${normalStats.value.overall_correct_rate || 0}%`);
    const weak = (normalStats.value.kpMastery || []).slice(0, 3).map(k => k.knowledge_point).join('、');
    if (weak) parts.push(`🚨 薄弱知识点 TOP3：${weak}`);
  }
  if (riskStudents.value.length > 0) parts.push(`🆘 高风险学生 ${riskStudents.value.length} 人，请重点关注`);
  parts.push(`🕐 数据更新：${new Date().toLocaleString()}`);
  return parts.join('   •   ');
});

// ─── 过滤链 ───
const filteredRecords = computed(() => {
  return rawRecords.value.filter(record => {
    // 学生
    if (filterStudent.value && record.student_name !== filterStudent.value) return false;
    // 知识点
    if (filterKp.value && String(record.knowledge_point || '').trim() !== filterKp.value) return false;
    // 题号
    if (filterQ.value && String(record.question_number || '') !== filterQ.value) return false;
    // 只看错题
    if (onlyWrong.value && checkPass(record.is_correct)) return false;
    // 只看风险学生
    if (onlyRisk.value && !riskNameSet.value.has(record.student_name)) return false;

    // 状态档位
    if (filterStatus.value !== 'ALL') {
      if (isWebTeacher.value) {
        const sc = getProjectScore(record.error_cause);
        if (filterStatus.value === 'EXCELLENT' && sc < 90) return false;
        if (filterStatus.value === 'GOOD' && (sc < 80 || sc >= 90)) return false;
        if (filterStatus.value === 'PASS' && (sc < 60 || sc >= 80)) return false;
        if (filterStatus.value === 'POOR' && sc >= 60) return false;
      } else {
        const ok = checkPass(record.is_correct);
        if (filterStatus.value === 'PASS' && !ok) return false;
        if (filterStatus.value === 'FAIL' && ok) return false;
      }
    }

    // 分数区间（基于项目得分；普通老师按 0/100）
    if (filterScoreRange.value) {
      const sc = isWebTeacher.value ? getProjectScore(record.error_cause) : (checkPass(record.is_correct) ? 100 : 0);
      const [lo, hi] = filterScoreRange.value.split('-').map(Number);
      if (sc < lo || sc > hi) return false;
    }
    return true;
  });
});

// ─── 明细分页 ───
const PAGE_SIZE = 50;
const page = ref(1);
const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / PAGE_SIZE)));
const pagedRecords = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE;
  return filteredRecords.value.slice(start, start + PAGE_SIZE);
});
watch(filteredRecords, () => { page.value = 1; });

// ─── KPI 计算（基于 filteredRecords）───
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
    } catch (e) {}
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
          const val = Number(values[index]) || 0;
          totals[matchedKey] += val; counts[matchedKey]++;
          if (matchedKey === "响应式适配" && val >= 60) responsivePassCount++;
        }
      });
    }
  });
  const averages = {};
  Object.keys(totals).forEach(k => { averages[k] = counts[k] > 0 ? Math.round(totals[k] / counts[k]) : 0; });
  const validAverages = Object.entries(averages).filter(a => counts[a[0]] > 0);
  const sorted = validAverages.sort((a, b) => a[1] - b[1]);
  const weakestDimension = sorted.length ? `${sorted[0][0]} (${sorted[0][1]}分)` : '暂无数据';
  const strongestDimension = sorted.length ? `${sorted[sorted.length - 1][0]} (${sorted[sorted.length - 1][1]}分)` : '暂无数据';
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
  const kpMastery = Object.entries(kpStats).map(([kp, c]) => ({
    knowledge_point: kp,
    rate: Math.round((c.correct/c.total)*100),
    error_rate: Math.round(((c.total-c.correct)/c.total)*100),
  })).sort((a, b) => b.error_rate - a.error_rate);
  return { total: filteredRecords.value.length, overall_correct_rate, topError, worstKp: kpMastery[0]?.knowledge_point || '暂无数据', kpMastery, errorCounts };
});

// ─── KPI 列表（含风险学生数）───
const webKpiList = computed(() => [
  { title: '已测评网站总数',     value: webStats.value.totalProjects ?? 0,        unit: '个', cls: 'text-slate-800' },
  { title: '📱 响应式合格率',     value: webStats.value.responsivePassRate ?? 0,  unit: '%',  cls: 'text-emerald-600' },
  { title: '🚨 高风险学生',       value: riskStudents.value.length,                unit: '人', cls: 'warning-text' },
  { title: '⚠️ 班级最薄弱项',    value: webStats.value.weakestDimension || '—',   small: true, cls: 'warning-text' },
]);

const normalKpiList = computed(() => [
  { title: '已批改总题数',   value: normalStats.value.total ?? 0,                 unit: '题', cls: 'text-slate-800' },
  { title: '班级综合正确率', value: normalStats.value.overall_correct_rate ?? 0, unit: '%',  cls: 'text-emerald-600' },
  { title: '🚨 高风险学生',   value: riskStudents.value.length,                    unit: '人', cls: 'warning-text' },
  { title: '⚠️ 最薄弱知识点', value: normalStats.value.worstKp || '—',             small: true, cls: 'warning-text' },
]);

// ─── 主题相关：图表样式 token ───
const axisColor = computed(() => darkMode.value ? '#cbd5e1' : '#475569');
const splitColor = computed(() => darkMode.value ? 'rgba(148,163,184,0.18)' : 'rgba(148,163,184,0.3)');
const labelColor = computed(() => darkMode.value ? '#f1f5f9' : '#1e293b');

const baseTextStyle = () => ({ color: axisColor.value });

// ─── 渲染 ───
const renderCharts = () => {
  Object.values(chartInstances.value).forEach(c => { try { c.dispose(); } catch(e) {} });
  chartInstances.value = {};
  if (rawRecords.value.length === 0) return;
  try {
    // 🌟 大屏模式走专用渲染分支，只画 2 张图（主排行 + 热力/雷达）
    if (darkMode.value) {
      renderBigscreenCharts();
      return;
    }
    if (isWebTeacher.value) renderWebTeacherCharts();
    else renderNormalCharts();
  } catch (err) { console.error('❌ ECharts 渲染失败:', err); }
};

// 🌟 大屏专用渲染：3 张图，深色配色，加发光效果
const renderBigscreenCharts = () => {
  // ── 主排行柱图 ──
  if (bsMainBarRef.value && studentScores.value.length > 0) {
    const top = studentScores.value.slice(0, 15);
    const names = top.map(s => s.name.replace('-UI评测', ''));
    const scores = top.map(s => s.score);
    const chart = echarts.init(bsMainBarRef.value);
    chart.setOption({
      textStyle: { color: '#cbd5e1' },
      tooltip: { trigger: 'axis', formatter: '{b}: {c}分', backgroundColor: 'rgba(15,23,42,0.95)', borderColor: '#334155', textStyle: { color: '#f1f5f9' } },
      grid: { top: '12%', bottom: '18%', left: '5%', right: '5%', containLabel: true },
      xAxis: { type: 'category', data: names, axisLabel: { interval: 0, rotate: names.length > 6 ? 30 : 0, color: '#e2e8f0', fontWeight: 'bold', fontSize: 12 }, axisLine: { lineStyle: { color: '#334155' } } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.15)', type: 'dashed' } } },
      series: [{
        type: 'bar',
        data: scores.map(s => ({
          value: s,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: getDynamicColor(s) },
              { offset: 1, color: getDynamicColor(s) + '60' },
            ]),
            shadowColor: getDynamicColor(s),
            shadowBlur: 12,
          },
        })),
        barWidth: 28,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}', fontWeight: 900, fontSize: 13, color: '#f8fafc', textBorderColor: '#0f172a', textBorderWidth: 2 },
      }],
    });
    chartInstances.value.bsMainBar = chart;
  }

  // ── 副图：普通老师走热力图，网页老师走雷达 ──
  if (!isWebTeacher.value && bsHeatRef.value) {
    const students = Array.from(new Set(filteredRecords.value.map(r => r.student_name || '未知'))).sort();
    const kps = kpOptions.value;
    const chart = echarts.init(bsHeatRef.value);
    if (students.length === 0 || kps.length === 0) {
      chart.setOption({ textStyle: { color: '#cbd5e1' }, title: { text: '暂无热力图数据', textStyle: { color: '#94a3b8' }, left: 'center', top: 'center' } });
    } else {
      const matrix = {};
      kps.forEach(kp => { matrix[kp] = {}; students.forEach(s => matrix[kp][s] = { t: 0, c: 0 }); });
      filteredRecords.value.forEach(r => {
        const kp = String(r.knowledge_point || '').trim();
        if (!kps.includes(kp)) return;
        const s = r.student_name || '未知';
        matrix[kp][s].t++;
        if (checkPass(r.is_correct)) matrix[kp][s].c++;
      });
      const data = [];
      kps.forEach((kp, ki) => {
        students.forEach((s, si) => {
          const cell = matrix[kp][s];
          if (cell.t > 0) data.push([si, ki, Math.round(((cell.t - cell.c) / cell.t) * 100)]);
        });
      });
      chart.setOption({
        textStyle: { color: '#cbd5e1' },
        tooltip: {
          position: 'top', backgroundColor: 'rgba(15,23,42,0.95)', borderColor: '#334155', textStyle: { color: '#f1f5f9' },
          formatter: (p) => `${students[p.data[0]].replace('-UI评测','')} · ${kps[p.data[1]]}<br/>错误率：${p.data[2]}%`,
        },
        grid: { top: 10, bottom: 60, left: 90, right: 20 },
        xAxis: { type: 'category', data: students.map(s => s.replace('-UI评测','')), axisLabel: { rotate: 30, color: '#94a3b8', interval: 0, fontSize: 11 }, splitArea: { show: true } },
        yAxis: { type: 'category', data: kps, axisLabel: { color: '#94a3b8', fontSize: 11 }, splitArea: { show: true } },
        visualMap: { min: 0, max: 100, calculable: true, orient: 'horizontal', left: 'center', bottom: 5, textStyle: { color: '#cbd5e1' }, inRange: { color: ['#10b981', '#fbbf24', '#ef4444'] } },
        series: [{ type: 'heatmap', data, label: { show: true, color: '#fff', fontWeight: 'bold' }, itemStyle: { borderColor: '#0b1220', borderWidth: 1 } }],
      });
    }
    chartInstances.value.bsHeat = chart;
  }

  if (isWebTeacher.value && bsRadarRef.value) {
    const dims = Object.keys(webStats.value.averages || {});
    const vals = Object.values(webStats.value.averages || {});
    const chart = echarts.init(bsRadarRef.value);
    chart.setOption({
      textStyle: { color: '#cbd5e1' },
      tooltip: { trigger: 'item', backgroundColor: 'rgba(15,23,42,0.95)', borderColor: '#334155', textStyle: { color: '#f1f5f9' } },
      radar: {
        indicator: dims.map(d => ({ name: d, max: 100 })),
        radius: '70%',
        axisName: { color: '#cbd5e1', fontSize: 12, fontWeight: 'bold' },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.25)' } },
        splitArea: { areaStyle: { color: ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.04)'] } },
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } },
      },
      series: [{
        type: 'radar',
        data: dims.length ? [{ value: vals, name: '全班均分', areaStyle: { color: 'rgba(96, 165, 250, 0.35)' }, lineStyle: { color: '#60a5fa', width: 2 }, itemStyle: { color: '#60a5fa' }, symbolSize: 6 }] : [{ value: [0] }],
      }],
    });
    chartInstances.value.bsRadar = chart;
  }
};

const renderWebTeacherCharts = () => {
  if (webScoreBarRef.value && studentScores.value.length > 0) {
    const names = studentScores.value.map(s => s.name.replace('-UI评测',''));
    const scores = studentScores.value.map(s => s.score);
    const chart = echarts.init(webScoreBarRef.value);
    chart.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'axis', formatter: '{b}: {c}分' },
      grid: { top: '15%', bottom: '20%', left: '5%', right: '5%', containLabel: true },
      xAxis: { type: 'category', data: names, axisLabel: { interval: 0, rotate: names.length > 5 ? 25 : 0, fontWeight: 'bold', color: axisColor.value } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: axisColor.value }, splitLine: { lineStyle: { type: 'dashed', color: splitColor.value } } },
      series: [{
        type: 'bar',
        data: scores.map(s => ({ value: s, itemStyle: { color: getDynamicColor(s) } })),
        barWidth: 35,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}分', fontWeight: 'bold', fontSize: 13, color: labelColor.value }
      }]
    });
    chartInstances.value.webScoreBar = chart;
  }
  if (webBarRef.value && webRadarRef.value) {
    const dimensions = Object.keys(webStats.value.averages || {});
    const values = Object.values(webStats.value.averages || {});
    const chartBar = echarts.init(webBarRef.value);
    chartBar.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'axis', formatter: '{b}: {c}分' },
      grid: { top: '15%', bottom: '15%', left: '5%', right: '5%', containLabel: true },
      xAxis: { type: 'category', data: dimensions, axisLabel: { fontSize: 12, fontWeight: 'bold', color: axisColor.value } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: axisColor.value }, splitLine: { lineStyle: { type: 'dashed', color: splitColor.value } } },
      series: [{
        type: 'bar',
        data: dimensions.length ? values : [0],
        barWidth: 35,
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#10b981' }, { offset: 1, color: '#047857' }]), borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}分', color: labelColor.value, fontWeight: 'bold' }
      }]
    });
    chartInstances.value.webBar = chartBar;

    const chartRadar = echarts.init(webRadarRef.value);
    chartRadar.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'item' },
      radar: { indicator: dimensions.map(d => ({ name: d, max: 100 })), radius: '65%', center: ['50%', '50%'], axisName: { color: axisColor.value } },
      series: [{
        type: 'radar',
        data: dimensions.length ? [{ value: values, name: '全班技术均分', areaStyle: { color: 'rgba(16, 185, 129, 0.3)' }, lineStyle: { color: '#10b981', width: 2 }, symbolSize: 6 }] : [{ value: [0], name: '暂无数据' }]
      }]
    });
    chartInstances.value.webRadar = chartRadar;
  }
};

const renderNormalCharts = () => {
  if (normalScoreBarRef.value && studentScores.value.length > 0) {
    const names = studentScores.value.map(s => s.name);
    const scores = studentScores.value.map(s => s.score);
    const chart = echarts.init(normalScoreBarRef.value);
    chart.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'axis', formatter: '{b}: {c}分' },
      grid: { top: '15%', bottom: '20%', left: '5%', right: '5%', containLabel: true },
      xAxis: { type: 'category', data: names, axisLabel: { interval: 0, rotate: names.length > 5 ? 25 : 0, fontWeight: 'bold', color: axisColor.value } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: axisColor.value }, splitLine: { lineStyle: { type: 'dashed', color: splitColor.value } } },
      series: [{
        type: 'bar', data: scores.map(s => ({ value: s, itemStyle: { color: getDynamicColor(s) } })),
        barWidth: 35, itemStyle: { borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}分', fontWeight: 'bold', fontSize: 13, color: labelColor.value }
      }]
    });
    chartInstances.value.normalScoreBar = chart;
  }

  if (pieRef.value && barRef.value && hbarRef.value && radarRef.value) {
    const pieData = Object.entries(normalStats.value.errorCounts || {}).map(([cause, count]) => ({ name: cause, value: count })).sort((a, b) => b.value - a.value);
    const chartPie = echarts.init(pieRef.value);
    chartPie.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'item' },
      legend: { textStyle: { color: axisColor.value }, bottom: 0 },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        itemStyle: { borderRadius: 8, borderColor: darkMode.value ? '#0f172a' : '#fff', borderWidth: 2 },
        label: { color: axisColor.value },
        data: pieData.length ? pieData : [{ name: '无错题', value: 0 }]
      }]
    });
    chartInstances.value.pie = chartPie;

    const errMap = {};
    filteredRecords.value.forEach(r => {
      if (!checkPass(r.is_correct)) {
        const q = String(r.question_number || '未知');
        errMap[q] = (errMap[q] || 0) + 1;
      }
    });
    const qKeys = Object.keys(errMap).sort((a, b) => a.localeCompare(b, 'zh-CN', { numeric: true }));
    const chartBar = echarts.init(barRef.value);
    chartBar.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'axis' },
      grid: { left: '5%', right: '5%', bottom: '10%', containLabel: true },
      xAxis: { type: 'category', data: qKeys, axisLabel: { color: axisColor.value } },
      yAxis: { type: 'value', minInterval: 1, axisLabel: { color: axisColor.value }, splitLine: { lineStyle: { color: splitColor.value } } },
      series: [{ type: 'bar', data: qKeys.map(k => errMap[k]), barWidth: 20, itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] } }]
    });
    chartInstances.value.bar = chartBar;

    const worstKps = (normalStats.value.kpMastery || []).slice(0, 5).reverse();
    const chartHBar = echarts.init(hbarRef.value);
    chartHBar.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'axis', formatter: '{b}: 错误率 {c}%' },
      grid: { left: '5%', right: '15%', bottom: '5%', containLabel: true },
      xAxis: { type: 'value', max: 100, axisLabel: { color: axisColor.value }, splitLine: { lineStyle: { color: splitColor.value } } },
      yAxis: { type: 'category', data: worstKps.map(k => String(k.knowledge_point || '未知').substring(0, 8)), axisLabel: { color: axisColor.value } },
      series: [{
        type: 'bar', data: worstKps.map(k => k.error_rate || 0),
        label: { show: true, position: 'right', formatter: '{c}%', color: labelColor.value },
        itemStyle: { color: '#ef4444', borderRadius: [0, 4, 4, 0] }
      }]
    });
    chartInstances.value.hbar = chartHBar;

    const radarData = (normalStats.value.kpMastery || []).slice(0, 6);
    const chartRadar = echarts.init(radarRef.value);
    chartRadar.setOption({
      textStyle: baseTextStyle(),
      tooltip: { trigger: 'item' },
      radar: { indicator: radarData.map(k => ({ name: String(k.knowledge_point || '未知').substring(0, 6), max: 100 })), radius: '60%', axisName: { color: axisColor.value } },
      series: [{
        type: 'radar',
        data: radarData.length ? [{
          value: radarData.map(k => k.rate || 0),
          areaStyle: { color: 'rgba(16, 185, 129, 0.2)' },
          lineStyle: { color: '#10b981' },
          itemStyle: { color: '#10b981' }
        }] : [{ value: [0], name: '暂无数据' }]
      }]
    });
    chartInstances.value.radar = chartRadar;
  }

  // 🌟 知识点 × 学生 热力图
  if (heatmapRef.value) {
    const students = Array.from(new Set(filteredRecords.value.map(r => r.student_name || '未知'))).sort();
    const kps = kpOptions.value;
    if (students.length === 0 || kps.length === 0) {
      const chart = echarts.init(heatmapRef.value);
      chart.setOption({
        textStyle: baseTextStyle(),
        title: { text: '暂无热力图数据', textStyle: { color: axisColor.value, fontSize: 13 }, left: 'center', top: 'center' }
      });
      chartInstances.value.heatmap = chart;
    } else {
      // matrix[kpIdx][studentIdx] = error_rate%
      const matrix = {};
      kps.forEach(kp => { matrix[kp] = {}; students.forEach(s => matrix[kp][s] = { t: 0, c: 0 }); });
      filteredRecords.value.forEach(r => {
        const kp = String(r.knowledge_point || '').trim();
        if (!kps.includes(kp)) return;
        const s = r.student_name || '未知';
        matrix[kp][s].t++;
        if (checkPass(r.is_correct)) matrix[kp][s].c++;
      });
      const data = [];
      kps.forEach((kp, ki) => {
        students.forEach((s, si) => {
          const cell = matrix[kp][s];
          if (cell.t === 0) data.push([si, ki, '-']);
          else data.push([si, ki, Math.round(((cell.t - cell.c) / cell.t) * 100)]);
        });
      });
      const chart = echarts.init(heatmapRef.value);
      chart.setOption({
        textStyle: baseTextStyle(),
        tooltip: {
          position: 'top',
          formatter: (p) => {
            const sName = students[p.data[0]].replace('-UI评测','');
            const kp = kps[p.data[1]];
            const v = p.data[2];
            return `${sName} · ${kp}<br/>错误率：${v === '-' ? '无作答' : v + '%'}`;
          }
        },
        grid: { top: 20, bottom: 80, left: 100, right: 20 },
        xAxis: { type: 'category', data: students.map(s => s.replace('-UI评测','')), axisLabel: { rotate: 30, color: axisColor.value, interval: 0 } },
        yAxis: { type: 'category', data: kps, axisLabel: { color: axisColor.value } },
        visualMap: {
          min: 0, max: 100, calculable: true, orient: 'horizontal', left: 'center', bottom: 10,
          textStyle: { color: axisColor.value },
          inRange: { color: ['#10b981', '#fbbf24', '#ef4444'] },
        },
        series: [{
          type: 'heatmap',
          data: data.filter(d => d[2] !== '-'),
          label: { show: true, color: '#fff', fontWeight: 'bold', formatter: (p) => p.data[2] + '' },
          itemStyle: { borderColor: darkMode.value ? '#0f172a' : '#fff', borderWidth: 1 },
        }]
      });
      chartInstances.value.heatmap = chart;
    }
  }
};

let renderTimer = null;
const scheduleRender = () => {
  if (renderTimer) clearTimeout(renderTimer);
  renderTimer = setTimeout(async () => {
    await nextTick();
    renderCharts();
  }, 80);
};

watch(filteredRecords, scheduleRender, { deep: true });
watch(darkMode, scheduleRender);

const handleResize = () => {
  Object.values(chartInstances.value).forEach(c => { try { c.resize(); } catch(e) {} });
};

const loadDashboardStats = async (forceSync = false) => {
  const token = globalStore.config.feishuToken;
  if (!token || loading.value) return;
  loading.value = true;
  try {
    const data = await syncCenter.loadDashboardStats(token, forceSync);
    if (data) {
      rawRecords.value = data.raw_records || [];
      console.log(`✅ 学情数据加载完成: ${rawRecords.value.length} 条记录`);
    }
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || String(error);
    console.error('❌ 加载大盘数据失败:', detail);
    alert('❌ 加载学情数据失败: ' + detail);
  } finally { loading.value = false; }
};

// ─── AI 学情摘要（复用 /api/homework/chat_with_data） ───
const aiSummary = ref('');
const aiLoading = ref(false);

const buildSummaryContext = () => {
  // 抽样取前 80 条，避免 token 爆炸
  const sample = filteredRecords.value.slice(0, 80).map(r => ({
    name: (r.student_name || '').replace('-UI评测', ''),
    q: r.question_number,
    kp: r.knowledge_point,
    pass: checkPass(r.is_correct) ? '对' : '错',
    err: getCleanFeedback(r.error_cause).slice(0, 40),
  }));
  return JSON.stringify({
    overall: isWebTeacher.value ? webStats.value : normalStats.value,
    riskCount: riskStudents.value.length,
    riskNames: riskStudents.value.slice(0, 10).map(s => s.name.replace('-UI评测','')),
    records: sample,
  });
};

const generateAiSummary = async () => {
  if (!globalStore.config.apiKey) return alert('⚠️ 请先在右侧配置大模型 API Key');
  if (filteredRecords.value.length === 0) return alert('当前没有可分析的数据');
  aiLoading.value = true;
  try {
    const subject = globalStore.auth.subject || '通用学科';
    const prompt = `请基于上述 JSON 数据，为${subject}老师生成一段 4 段以内的班级学情摘要：
1) 第一段：整体表现一句话概括（正确率、风险人数）。
2) 第二段：主要薄弱知识点 / 维度（具体到名称）。
3) 第三段：最高频错因或共性问题。
4) 第四段：3 条可执行的下一节课教学建议（用 - 列表）。
要求语气专业、克制、可读，长度控制在 250 字以内。`;

    const res = await axios.post('/api/homework/chat_with_data', {
      user_message: prompt,
      data_context: buildSummaryContext(),
      ai_model: globalStore.config.model || 'doubao-seed-2-0-pro-260215',
      api_key: globalStore.config.apiKey,
    }, { headers: { 'Authorization': `Bearer ${globalStore.auth.token}` } });
    if (res.data?.status === 'success') {
      aiSummary.value = res.data.reply || '';
    } else {
      alert('AI 摘要生成失败：' + (res.data?.detail || '未知原因'));
    }
  } catch (e) {
    alert('AI 摘要生成失败：' + (e.response?.data?.detail || e.message));
  } finally { aiLoading.value = false; }
};

// 极简 markdown 转换：仅处理标题/加粗/列表/换行，不引入额外依赖
const renderMarkdownLite = (text) => {
  if (!text) return '';
  let html = String(text)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n/g, '<br/>');
  html = html.replace(/(<li>.*?<\/li>(?:<br\/>)?)+/g, m => '<ul>' + m.replace(/<br\/>/g, '') + '</ul>');
  return html;
};

// 数据变化 → 清空旧 AI 摘要（避免与新筛选不匹配）
watch(filteredRecords, () => { aiSummary.value = ''; });

let resizeHandler = null;
onMounted(() => {
  if (globalStore.config.feishuToken) loadDashboardStats(true);
  setTimeout(() => { resizeHandler = handleResize; window.addEventListener('resize', resizeHandler); }, 0);
  clockTimer = setInterval(() => { clockNow.value = new Date(); }, 1000);
});
onActivated(() => { if (globalStore.config.feishuToken) loadDashboardStats(true); });
onDeactivated(() => {
  Object.values(chartInstances.value).forEach(c => { try { c.dispose(); } catch(e) {} });
  chartInstances.value = {};
});
onUnmounted(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler);
  Object.values(chartInstances.value).forEach(c => { try { c.dispose(); } catch(e) {} });
  chartInstances.value = {};
  if (renderTimer) clearTimeout(renderTimer);
  if (clockTimer) clearInterval(clockTimer);
});
</script>

<style scoped>
@keyframes spin { 100% { transform: rotate(360deg); } }
.is-spinning { animation: spin 1s linear infinite; }

.analytics-dashboard { display: flex; flex-direction: column; gap: 20px; min-height: 100%; padding-bottom: 20px; position: relative; transition: background 0.3s; }
.analytics-dashboard.is-dark { background: #0b1220; padding: 16px; border-radius: 16px; }

.dashboard-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); padding: 20px 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #edf2f7; }
.is-dark .dashboard-header { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-color: #334155; }
.title-area h3 { margin: 0 0 6px 0; font-size: 20px; color: #1a202c; font-weight: 700; }
.title-area p { margin: 0; font-size: 13px; color: #718096; }
.is-dark .title-area h3 { color: #f1f5f9; }
.is-dark .title-area p { color: #94a3b8; }

.header-actions { display: flex; gap: 10px; align-items: center; }
.theme-switch { display: inline-flex; padding: 3px; border-radius: 10px; background: #e2e8f0; gap: 2px; }
.theme-switch button { height: 30px; padding: 0 12px; border: none; background: transparent; border-radius: 8px; font-size: 12px; font-weight: 700; color: #475569; cursor: pointer; transition: 0.2s; }
.theme-switch button.active { background: #fff; color: #1d4ed8; box-shadow: 0 2px 6px rgba(15,23,42,0.08); }
.is-dark .theme-switch { background: rgba(255,255,255,0.08); }
.is-dark .theme-switch button { color: #cbd5e1; }
.is-dark .theme-switch button.active { background: #2563eb; color: #fff; }

.btn-sync { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e2e8f0; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; color: #4a5568; transition: all 0.2s ease; }
.btn-sync:hover:not(:disabled) { color: var(--edu-primary, #1890ff); border-color: var(--edu-primary, #1890ff); background: #f0f7ff; box-shadow: 0 4px 12px rgba(24,144,255,0.1); transform: translateY(-1px); }
.btn-sync:disabled { background: #f8fafc; color: #cbd5e1; cursor: not-allowed; }
.is-dark .btn-sync { background: rgba(255,255,255,0.06); color: #cbd5e1; border-color: #334155; }
.is-dark .btn-sync:hover:not(:disabled) { background: #1e40af; color: #fff; border-color: #2563eb; }

/* KPI */
.kpi-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.kpi-card { background: #fff; padding: 24px 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #edf2f7; transition: 0.3s; display: flex; flex-direction: column; gap: 8px;}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); border-color: #cbd5e1; }
.is-dark .kpi-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-color: #334155; box-shadow: 0 6px 20px rgba(0,0,0,0.35); }
.is-dark .kpi-card:hover { border-color: #475569; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.25); }
.kpi-title { font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;}
.is-dark .kpi-title { color: #94a3b8; }
.kpi-value { font-size: 28px; font-weight: 900; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;}
.unit { font-size: 14px; font-weight: 700; color: #94a3b8; margin-left: 2px; }

.text-slate-800 { color: #1e293b; } .is-dark .text-slate-800 { color: #e2e8f0; }
.text-emerald-600 { color: #059669; } .is-dark .text-emerald-600 { color: #34d399; }
.warning-text { color: #dc2626; } .is-dark .warning-text { color: #fca5a5; }

/* AI 摘要 + 风险榜 */
.ai-risk-row { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.ai-summary-card, .risk-list-card { background: #fff; border: 1px solid #edf2f7; border-radius: 12px; padding: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); display: flex; flex-direction: column; gap: 12px; }
.is-dark .ai-summary-card, .is-dark .risk-list-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-color: #334155; }
.card-head { display: flex; align-items: center; gap: 8px; }
.card-head strong { flex: 1; color: #0f172a; font-size: 15px; font-weight: 900; }
.is-dark .card-head strong { color: #f1f5f9; }
.card-icon { font-size: 18px; }
.mini-btn { padding: 6px 12px; border-radius: 8px; border: 1px solid #bfdbfe; background: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: 800; cursor: pointer; transition: 0.2s; }
.mini-btn:hover:not(:disabled) { background: #dbeafe; transform: translateY(-1px); }
.mini-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.is-dark .mini-btn { background: #1e40af; color: #fff; border-color: #2563eb; }

.ai-text { font-size: 13.5px; line-height: 1.85; color: #334155; padding: 12px 14px; background: #f8fafc; border-radius: 10px; border-left: 3px solid #3b82f6; }
.is-dark .ai-text { background: rgba(59,130,246,0.08); color: #e2e8f0; border-left-color: #60a5fa; }
.ai-text :deep(ul) { margin: 6px 0; padding-left: 20px; }
.ai-text :deep(strong) { color: #0f172a; }
.is-dark .ai-text :deep(strong) { color: #fde68a; }

.ai-placeholder { font-size: 13px; color: #64748b; line-height: 1.7; padding: 14px; background: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; }
.ai-placeholder small { display: block; margin-top: 6px; color: #d97706; font-weight: 700; }
.is-dark .ai-placeholder { background: rgba(255,255,255,0.04); color: #94a3b8; border-color: #334155; }

.dot-flow { display: inline-flex; gap: 4px; margin-right: 8px; }
.dot-flow span { width: 6px; height: 6px; border-radius: 50%; background: #3b82f6; animation: blink 1.4s infinite both; }
.dot-flow span:nth-child(2) { animation-delay: 0.2s; }
.dot-flow span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.3; } 40% { opacity: 1; } }

.risk-count { padding: 3px 10px; border-radius: 999px; background: #fef2f2; color: #b91c1c; font-size: 11px; font-weight: 900; border: 1px solid #fecaca; }
.is-dark .risk-count { background: rgba(220,38,38,0.18); color: #fca5a5; border-color: rgba(252,165,165,0.3); }
.risk-empty { padding: 20px; text-align: center; color: #16a34a; background: #f0fdf4; border-radius: 10px; font-weight: 800; font-size: 13px; border: 1px solid #bbf7d0; }
.is-dark .risk-empty { background: rgba(16,185,129,0.12); color: #6ee7b7; border-color: rgba(110,231,183,0.3); }
.risk-list { display: flex; flex-direction: column; gap: 6px; max-height: 220px; overflow-y: auto; }
.risk-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 8px; background: #fef2f2; border: 1px solid #fecaca; }
.is-dark .risk-item { background: rgba(220,38,38,0.10); border-color: rgba(252,165,165,0.25); }
.risk-rank { font-size: 11px; font-weight: 900; color: #94a3b8; }
.risk-name { flex: 1; font-size: 13px; font-weight: 800; color: #0f172a; }
.is-dark .risk-name { color: #e2e8f0; }
.risk-score { font-size: 14px; font-weight: 900; }
.risk-jump { background: transparent; border: none; cursor: pointer; opacity: 0.7; padding: 4px; border-radius: 4px; }
.risk-jump:hover { opacity: 1; background: #fee2e2; }

/* 图表区 */
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 4px; }
.chart-card { background: #fff; border-radius: 12px; border: 1px solid #edf2f7; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); transition: 0.3s; }
.chart-card:hover { border-color: #cbd5e1; box-shadow: 0 8px 24px rgba(0,0,0,0.05); }
.is-dark .chart-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-color: #334155; box-shadow: 0 8px 30px rgba(0,0,0,0.35); }
.chart-card.full-width { grid-column: span 2; }
.chart-title { font-size: 15px; font-weight: 800; color: #334155; margin-bottom: 16px; display: flex; align-items: center; gap: 6px;}
.is-dark .chart-title { color: #f1f5f9; }
.chart-container { width: 100%; height: 280px; }

/* 筛选控制台 */
.filter-console { display: flex; align-items: center; gap: 20px; background: #fff; padding: 16px 20px; border-radius: 12px; border: 1px solid #edf2f7; box-shadow: 0 4px 20px rgba(0,0,0,0.03); flex-wrap: wrap; }
.is-dark .filter-console { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-color: #334155; }
.filter-label { font-weight: 800; color: #1e293b; font-size: 14px; }
.is-dark .filter-label { color: #f1f5f9; }
.filter-group { display: flex; gap: 10px; flex: 1; flex-wrap: wrap; align-items: center; }
.filter-group select { padding: 8px 12px; border: 1.5px solid #cbd5e1; border-radius: 8px; font-size: 12px; font-weight: 700; color: #475569; outline: none; transition: 0.2s; min-width: 130px; background: #f8fafc; cursor: pointer; }
.filter-group select:focus { border-color: #3b82f6; background: #fff; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.is-dark .filter-group select { background: rgba(255,255,255,0.06); color: #e2e8f0; border-color: #475569; }
.is-dark .filter-group select:focus { background: rgba(255,255,255,0.12); border-color: #60a5fa; }

.toggle-pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border: 1.5px solid #cbd5e1; border-radius: 999px; font-size: 12px; font-weight: 700; color: #475569; cursor: pointer; transition: 0.2s; background: #fff; }
.toggle-pill input { margin: 0; }
.toggle-pill:hover { border-color: #3b82f6; color: #1d4ed8; }
.is-dark .toggle-pill { background: rgba(255,255,255,0.06); color: #cbd5e1; border-color: #475569; }
.is-dark .toggle-pill:hover { border-color: #60a5fa; color: #fff; }
.reset-btn { padding: 6px 12px; border-radius: 8px; border: 1px dashed #fca5a5; background: #fef2f2; color: #b91c1c; font-size: 12px; font-weight: 800; cursor: pointer; }
.reset-btn:hover { background: #fee2e2; }
.is-dark .reset-btn { background: rgba(220,38,38,0.12); }

.filter-result-count { font-size: 14px; color: #64748b; font-weight: 600;}
.filter-result-count strong { color: #2563eb; font-size: 16px; font-weight: 900;}
.is-dark .filter-result-count { color: #94a3b8; }
.is-dark .filter-result-count strong { color: #60a5fa; }

.mt-5 { margin-top: 8px; }

/* 明细表 */
.data-table-wrapper { background: #fff; border-radius: 12px; border: 1px solid #edf2f7; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
.is-dark .data-table-wrapper { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-color: #334155; }
.styled-table { width: 100%; border-collapse: collapse; text-align: left; table-layout: fixed; }
.styled-table thead tr { background: #f8fafc; }
.is-dark .styled-table thead tr { background: rgba(255,255,255,0.04); }
.styled-table th { padding: 16px; font-size: 13px; font-weight: 800; color: #475569; border-bottom: 1px solid #edf2f7; }
.is-dark .styled-table th { color: #cbd5e1; border-bottom-color: #334155; }
.styled-table td { padding: 16px; border-bottom: 1px solid #edf2f7; font-size: 14px; color: #334155; line-height: 1.6; }
.is-dark .styled-table td { color: #e2e8f0; border-bottom-color: #334155; }
.styled-table tbody tr:hover { background: #f1f5f9; }
.is-dark .styled-table tbody tr:hover { background: rgba(255,255,255,0.04); }

.font-bold { font-weight: 700; color: #1e293b; }
.is-dark .font-bold { color: #f1f5f9; }
.font-bold-q { font-weight: 800; color: #3b82f6; }
.kp-tag { background: #eff6ff; color: #2563eb; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; white-space: nowrap; border: 1px solid #bfdbfe;}
.is-dark .kp-tag { background: rgba(37,99,235,0.18); color: #93c5fd; border-color: rgba(147,197,253,0.3); }

.project-score-badge { display: inline-flex; align-items: center; gap: 8px; background: #fff; padding: 4px 6px 4px 12px; border-radius: 20px; border: 1px solid #e2e8f0; }
.is-dark .project-score-badge { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.12); }
.proj-score { font-size: 14px; font-weight: 900; color: #0f172a; }
.is-dark .proj-score { color: #f1f5f9; }
.proj-unit { font-size: 11px; color: #94a3b8; font-weight: bold; }
.proj-eval { font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 16px; }

.eval-excellent { color: #059669; background: #ecfdf5; }
.eval-good { color: #2563eb; background: #eff6ff; }
.eval-pass { color: #d97706; background: #fffbeb; }
.eval-poor { color: #dc2626; background: #fef2f2; }
.pass-tag { color: #166534; background: #dcfce3; }
.fail-tag { color: #dc2626; background: #fef2f2; }

.clamped-text { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; white-space: normal; word-break: break-all; font-size: 13px; color: #475569; }
.is-dark .clamped-text { color: #cbd5e1; }
.error-cause { color: #b91c1c; font-weight: 500;}
.no-error { color: #15803d; font-weight: 500;}
.is-dark .error-cause { color: #fca5a5; }
.is-dark .no-error { color: #6ee7b7; }

.pager { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 14px; border-top: 1px solid #edf2f7; font-size: 13px; color: #64748b; }
.is-dark .pager { border-top-color: #334155; color: #94a3b8; }
.pager button { padding: 6px 14px; border-radius: 8px; border: 1px solid #cbd5e1; background: #fff; color: #475569; font-weight: 700; cursor: pointer; transition: 0.2s; }
.pager button:hover:not(:disabled) { border-color: #3b82f6; color: #1d4ed8; }
.pager button:disabled { opacity: 0.4; cursor: not-allowed; }
.is-dark .pager button { background: rgba(255,255,255,0.06); color: #cbd5e1; border-color: #475569; }

.loading-state, .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 350px; color: #94a3b8; font-weight: 600;}
.empty-icon { font-size: 50px; margin-bottom: 20px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.05)); }
.spinner { width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
.no-data-cell { text-align: center; color: #94a3b8; padding: 40px !important; }

/* ╔═══════════════════════════════════════════════════════╗
   ║  🌙 大屏模式专属样式（与报表模式完全独立的视觉体系）   ║
   ╚═══════════════════════════════════════════════════════╝ */
.bigscreen-shell {
  display: flex; flex-direction: column; gap: 14px;
  padding: 18px 20px 24px;
  background:
    radial-gradient(ellipse at 20% 0%, rgba(59, 130, 246, 0.18), transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(124, 58, 237, 0.18), transparent 50%),
    linear-gradient(180deg, #050a17 0%, #0b1220 100%);
  border-radius: 18px;
  color: #e2e8f0;
  min-height: 720px;
  position: relative;
  overflow: hidden;
}
/* 装饰：四角科技扫描线 */
.bigscreen-shell::before,
.bigscreen-shell::after {
  content: ''; position: absolute; width: 60px; height: 60px;
  border: 2px solid rgba(59, 130, 246, 0.4); pointer-events: none;
}
.bigscreen-shell::before { top: 10px; left: 10px; border-right: none; border-bottom: none; }
.bigscreen-shell::after { bottom: 10px; right: 10px; border-left: none; border-top: none; }

/* 顶部条 */
.bs-topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.18) 0%, rgba(124, 58, 237, 0.18) 100%);
  border: 1px solid rgba(96, 165, 250, 0.3);
  border-radius: 14px;
  position: relative; z-index: 1;
}
.bs-class { display: flex; align-items: center; gap: 14px; }
.bs-class-icon {
  width: 44px; height: 44px;
  display: grid; place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #fde68a, #f59e0b);
  font-size: 22px;
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
}
.bs-class strong {
  display: block; font-size: 22px; font-weight: 900;
  font-family: "STKaiti", "KaiTi", "楷体", "Microsoft YaHei", serif;
  background: linear-gradient(120deg, #ffffff 0%, #fde68a 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  letter-spacing: 4px;
}
.bs-class small { color: #94a3b8; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
.bs-clock { text-align: right; }
.bs-time {
  display: block;
  font-size: 32px; font-weight: 900; letter-spacing: 2px;
  font-family: "Menlo", "SF Mono", "Consolas", monospace;
  background: linear-gradient(120deg, #60a5fa 0%, #a78bfa 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  text-shadow: 0 0 24px rgba(96, 165, 250, 0.4);
  line-height: 1;
}
.bs-clock small { color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; margin-top: 4px; display: block; }

/* KPI 巨型卡 */
.bs-kpi-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  position: relative; z-index: 1;
}
.bs-kpi {
  position: relative;
  padding: 22px 20px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.88) 0%, rgba(15, 23, 42, 0.92) 100%);
  border: 1px solid rgba(96, 165, 250, 0.22);
  border-radius: 16px;
  overflow: hidden;
  display: flex; flex-direction: column; gap: 8px;
  transition: 0.3s;
}
.bs-kpi:hover { transform: translateY(-3px); border-color: rgba(96, 165, 250, 0.55); box-shadow: 0 12px 30px rgba(37, 99, 235, 0.35); }
.bs-kpi-label {
  font-size: 12px; color: #94a3b8; font-weight: 800;
  letter-spacing: 1.2px; text-transform: uppercase;
}
.bs-kpi-num {
  font-family: "Menlo", "SF Mono", "Consolas", monospace;
  font-size: 44px; font-weight: 900; line-height: 1.1;
  display: flex; align-items: baseline; gap: 4px;
}
.bs-kpi-num .num {
  background: linear-gradient(120deg, #ffffff 0%, #cbd5e1 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  text-shadow: 0 0 30px rgba(255, 255, 255, 0.18);
}
.bs-kpi-num .unit { font-size: 14px; color: #94a3b8; font-weight: 700; }
.bs-kpi-num.text-emerald-600 .num { background: linear-gradient(120deg, #6ee7b7 0%, #10b981 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.bs-kpi-num.warning-text .num { background: linear-gradient(120deg, #fca5a5 0%, #ef4444 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.bs-kpi-num.text-slate-800 .num { background: linear-gradient(120deg, #93c5fd 0%, #3b82f6 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }

.bs-kpi-glow {
  position: absolute; top: -40px; right: -40px;
  width: 120px; height: 120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(96, 165, 250, 0.28), transparent 65%);
  pointer-events: none;
}
.bs-kpi.kpi-1 .bs-kpi-glow { background: radial-gradient(circle, rgba(16, 185, 129, 0.28), transparent 65%); }
.bs-kpi.kpi-2 .bs-kpi-glow { background: radial-gradient(circle, rgba(239, 68, 68, 0.32), transparent 65%); }
.bs-kpi.kpi-3 .bs-kpi-glow { background: radial-gradient(circle, rgba(168, 85, 247, 0.28), transparent 65%); }

/* 主视觉区 */
.bs-main {
  display: grid; grid-template-columns: 1.5fr 1fr 0.85fr; gap: 14px;
  position: relative; z-index: 1;
}
.bs-main-left, .bs-main-mid, .bs-main-right {
  display: flex; flex-direction: column; gap: 14px;
}

.bs-panel {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.9) 100%);
  border: 1px solid rgba(96, 165, 250, 0.22);
  border-radius: 14px;
  padding: 16px;
  position: relative;
  box-shadow: 0 8px 26px rgba(0, 0, 0, 0.4);
}
.bs-panel-title {
  font-size: 14px; font-weight: 900; color: #f1f5f9;
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px; padding-bottom: 10px;
  border-bottom: 1px solid rgba(96, 165, 250, 0.18);
}
.bs-panel-sub {
  margin-left: auto; font-size: 11px; color: #94a3b8; font-weight: 700;
}
.bs-mini-btn {
  margin-left: auto;
  padding: 4px 10px; border-radius: 8px;
  border: 1px solid rgba(96, 165, 250, 0.5);
  background: rgba(37, 99, 235, 0.18); color: #93c5fd;
  font-size: 11px; font-weight: 800; cursor: pointer; transition: 0.2s;
}
.bs-mini-btn:hover:not(:disabled) { background: #2563eb; color: #fff; }
.bs-mini-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.bs-chart { width: 100%; }

/* AI 摘要 */
.bs-ai-text {
  font-size: 13px; line-height: 1.85; color: #e2e8f0;
  padding: 12px 14px;
  background: rgba(59, 130, 246, 0.08);
  border-left: 3px solid #60a5fa;
  border-radius: 8px;
  max-height: 220px; overflow-y: auto;
}
.bs-ai-text :deep(strong) { color: #fde68a; }
.bs-ai-text :deep(ul) { margin: 6px 0; padding-left: 18px; }
.bs-ai-empty {
  text-align: center; padding: 30px 12px;
  color: #94a3b8; font-size: 13px;
}
.bs-ai-empty p { margin: 8px 0 0; line-height: 1.6; }
.bs-ai-empty-icon { font-size: 38px; opacity: 0.5; }

/* 共性错因 / 五维均分 列表 */
.bs-top-list { display: flex; flex-direction: column; gap: 8px; }
.bs-top-row {
  display: grid; grid-template-columns: 24px 1fr 110px 30px; gap: 8px;
  align-items: center; font-size: 12px;
}
.bs-top-rank {
  width: 22px; height: 22px; border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff; font-weight: 900; font-size: 11px;
  display: grid; place-items: center;
}
.bs-top-row:nth-child(1) .bs-top-rank { background: linear-gradient(135deg, #fbbf24, #b45309); box-shadow: 0 0 12px rgba(251, 191, 36, 0.5); }
.bs-top-row:nth-child(2) .bs-top-rank { background: linear-gradient(135deg, #cbd5e1, #64748b); }
.bs-top-row:nth-child(3) .bs-top-rank { background: linear-gradient(135deg, #f97316, #c2410c); }
.bs-top-name { color: #e2e8f0; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bs-top-bar { background: rgba(255,255,255,0.08); height: 8px; border-radius: 4px; overflow: hidden; position: relative; }
.bs-top-bar span { display: block; height: 100%; background: linear-gradient(90deg, #ef4444, #f59e0b); border-radius: 4px; transition: width 0.4s; }
.bs-top-val { font-weight: 900; color: #fde68a; text-align: right; }
.bs-top-empty { text-align: center; padding: 20px; color: #64748b; font-size: 12px; }

/* 风险榜 */
.bs-risk { background: linear-gradient(135deg, rgba(127, 29, 29, 0.4) 0%, rgba(15, 23, 42, 0.92) 100%); border-color: rgba(248, 113, 113, 0.3); }
.bs-risk-count {
  margin-left: auto;
  padding: 2px 10px; border-radius: 999px;
  background: rgba(239, 68, 68, 0.22); color: #fca5a5;
  font-size: 11px; font-weight: 900;
  border: 1px solid rgba(252, 165, 165, 0.4);
}
.bs-risk-empty {
  text-align: center; padding: 40px 16px;
  color: #6ee7b7; font-size: 14px; font-weight: 800; line-height: 1.8;
  background: rgba(16, 185, 129, 0.08);
  border: 1px dashed rgba(110, 231, 183, 0.3);
  border-radius: 10px;
}
.bs-risk-list { display: flex; flex-direction: column; gap: 6px; max-height: 320px; overflow-y: auto; }
.bs-risk-item {
  display: grid; grid-template-columns: 30px 1fr 60px; gap: 8px; align-items: center;
  padding: 8px 10px; border-radius: 8px;
  background: rgba(239, 68, 68, 0.10);
  border: 1px solid rgba(252, 165, 165, 0.2);
}
.bs-risk-rank { font-size: 11px; color: #94a3b8; font-weight: 900; }
.bs-risk-name { font-size: 13px; color: #f1f5f9; font-weight: 800; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bs-risk-score { font-size: 16px; font-weight: 900; text-align: right; font-family: "Menlo", monospace; }

/* 优等生 */
.bs-honor-list { display: flex; flex-direction: column; gap: 6px; }
.bs-honor-row {
  display: grid; grid-template-columns: 30px 1fr auto; gap: 8px; align-items: center;
  padding: 8px 10px; border-radius: 8px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(110, 231, 183, 0.2);
}
.bs-honor-medal { font-size: 18px; }
.bs-honor-name { font-size: 13px; color: #f1f5f9; font-weight: 800; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bs-honor-score { font-size: 14px; color: #6ee7b7; font-weight: 900; font-family: "Menlo", monospace; }

/* 底部 ticker */
.bs-ticker {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px;
  background: linear-gradient(90deg, rgba(124, 58, 237, 0.22) 0%, rgba(37, 99, 235, 0.22) 100%);
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 12px;
  overflow: hidden;
  position: relative; z-index: 1;
}
.bs-ticker-tag {
  padding: 4px 10px; border-radius: 6px;
  background: rgba(255, 255, 255, 0.12); color: #fde68a;
  font-size: 11px; font-weight: 900; letter-spacing: 1px;
  white-space: nowrap;
}
.bs-ticker-track { flex: 1; overflow: hidden; }
.bs-ticker-text {
  display: inline-block; white-space: nowrap;
  color: #e2e8f0; font-size: 13px; font-weight: 700;
  animation: ticker-roll 32s linear infinite;
  padding-left: 100%;
}
@keyframes ticker-roll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}

/* 大屏响应式 */
@media (max-width: 1280px) {
  .bs-main { grid-template-columns: 1fr 1fr; }
  .bs-main-right { grid-column: span 2; }
  .bs-main-right .bs-panel { width: 100%; }
}
@media (max-width: 768px) {
  .bs-kpi-row { grid-template-columns: repeat(2, 1fr); }
  .bs-main { grid-template-columns: 1fr; }
  .bs-main-right { grid-column: auto; }
}
</style>
