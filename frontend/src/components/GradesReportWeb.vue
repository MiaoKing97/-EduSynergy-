<template>
  <div class="web-report-container">
    <div class="radar-section">
      <div class="section-header">
        <span class="icon">📊</span>
        <h4 class="section-title">前端全栈五维能力雷达画像</h4>
      </div>
      <p class="section-sub">基于该学生提交的所有网页作品，由 AI 视觉引擎综合计算得出的能力评估与百分制得分。</p>

      <div class="radar-wrapper" v-if="hasRadarData">
        <div class="overall-score-panel">
          <div class="score-ring" :class="scoreClass">
            <span class="score-val">{{ overallScore }}</span>
            <span class="score-unit">分</span>
          </div>
          <div class="score-label">AI 综合评估得分</div>
          <div class="score-desc">{{ scoreDesc }}</div>
        </div>

        <div class="radar-chart-container">
          <div ref="radarChartRef" class="radar-chart"></div>
        </div>
      </div>

      <div v-else class="radar-empty">
        <span class="empty-icon">🕸️</span>
        <span>该学生的作品暂未能成功解析出雷达维度数据</span>
      </div>
    </div>

    <div class="portfolio-section">
      <div class="section-header">
        <span class="icon">📁</span>
        <h4 class="section-title">网页作品评审明细 (共 {{ student.total }} 项)</h4>
      </div>

      <div class="card-list">
        <div class="project-card" v-for="(record, index) in student.records" :key="index">
          <div class="card-header" :class="checkPass(record.is_correct) ? 'pass' : 'fail'">
            <div class="project-name">
              <span class="status-dot"></span>
              <span class="p-name">{{ record.question_number === '综合评测' ? '网页端/移动端响应式综合评测项目' : record.question_number }}</span>
            </div>
            <div class="project-score-badge">
              <span class="proj-score">{{ getProjectScore(record.error_cause) }} <span class="proj-unit">分</span></span>
              <span class="proj-eval">{{ checkPass(record.is_correct) ? '✅ 规范达标' : '⚠️ 待优化' }}</span>
            </div>
          </div>

          <div class="card-body">
            <div class="feedback-title">🧑‍💻 资深前端架构师评审详报：</div>

            <template v-if="getParsedFeedback(record.error_cause).hasParsed">
              <div class="feedback-blocks">
                <div class="f-block f-summary" v-if="getParsedFeedback(record.error_cause).summary">
                  <div class="f-block-title">💡 综合评价</div>
                  <div class="f-block-content">{{ getParsedFeedback(record.error_cause).summary }}</div>
                </div>

                <div class="f-block f-pros" v-if="getParsedFeedback(record.error_cause).pros">
                  <div class="f-block-title">✨ 现有优点</div>
                  <div class="f-block-content">{{ getParsedFeedback(record.error_cause).pros }}</div>
                </div>

                <div class="f-block f-cons" v-if="getParsedFeedback(record.error_cause).cons">
                  <div class="f-block-title">🚨 缺陷与疏漏</div>
                  <div class="f-block-content">{{ getParsedFeedback(record.error_cause).cons }}</div>
                </div>

                <div class="f-block f-advice" v-if="getParsedFeedback(record.error_cause).advice">
                  <div class="f-block-title">🛠️ 架构改进建议</div>
                  <div class="f-block-content">{{ getParsedFeedback(record.error_cause).advice }}</div>
                </div>
              </div>
            </template>

            <template v-else>
              <p class="ai-feedback">{{ getParsedFeedback(record.error_cause).raw }}</p>
            </template>

          </div>

          <div class="card-footer">
            <span class="time-tag">提交时间：{{ record.submit_time || '近期提交' }}</span>
            <span class="kp-tag">考察核心：{{ record.knowledge_point || '综合运用' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  student: {
    type: Object,
    required: true
  }
});

const radarChartRef = ref(null);
let chartInstance = null;
const hasRadarData = ref(true);

// 🌟 新增：用于存储和渲染左侧的总体均分
const overallScore = ref(0);

const scoreClass = computed(() => {
  if (overallScore.value >= 85) return 'excellent';
  if (overallScore.value >= 60) return 'good';
  return 'poor';
});

const scoreDesc = computed(() => {
  if (overallScore.value >= 85) return '👑 架构级优秀代码，规范严谨';
  if (overallScore.value >= 60) return '✅ 达标上线水平，细节待打磨';
  return '🚨 存在严重体验缺陷，需重构';
});

const checkPass = (status) => {
  const s = String(status || '').trim();
  return s === '正确' || s.includes('部分正确') || s.includes('基本正确') || s.includes('合格') || s === 'true';
};

const getCleanFeedback = (text) => {
  if (!text) return 'AI 视觉引擎暂未给出详细建议。';
  let clean = String(text)
    .replace(/```json_array[\s\S]*?```/g, '')
    .replace(/```json[\s\S]*?```/g, '')
    .replace(/#/g, '')
    .replace(/\*/g, '')
    .trim();
  return clean || '项目已完成结构评测。';
};

const getParsedFeedback = (text) => {
  const cleanText = getCleanFeedback(text);
  const parsed = { hasParsed: false, summary: '', pros: '', cons: '', advice: '', raw: cleanText };

  const summaryMatch = cleanText.match(/【综合评价】([\s\S]*?)(?=【|$)/);
  const prosMatch = cleanText.match(/【(?:现有)?优点】([\s\S]*?)(?=【|$)/);
  const consMatch = cleanText.match(/【(?:现有)?缺陷】([\s\S]*?)(?=【|$)/);
  const adviceMatch = cleanText.match(/【改进建议】([\s\S]*?)(?=【|$)/);

  if (summaryMatch) parsed.summary = summaryMatch[1].trim();
  if (prosMatch) parsed.pros = prosMatch[1].trim();
  if (consMatch) parsed.cons = consMatch[1].trim();
  if (adviceMatch) parsed.advice = adviceMatch[1].trim();

  if (parsed.summary || parsed.pros || parsed.cons || parsed.advice) {
    parsed.hasParsed = true;
  }
  return parsed;
};

// 🌟 新增：独立解析提取某次特定作业的雷达图平均分
const getProjectScore = (errorCause) => {
  if (!errorCause) return 0;
  try {
    const match = String(errorCause).match(/```json([\s\S]*?)```/);
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

const renderRadar = () => {
  if (!props.student || !props.student.records) return;

  const totals = { "UI美观度": 0, "响应式适配": 0, "语义化与规范": 0, "性能与体验": 0, "交互逻辑": 0 };
  const counts = { "UI美观度": 0, "响应式适配": 0, "语义化与规范": 0, "性能与体验": 0, "交互逻辑": 0 };

  let dataFound = false;

  props.student.records.forEach(r => {
    if (!r.error_cause) return;
    let jsonObj = null;
    try {
      const match = String(r.error_cause).match(/```json([\s\S]*?)```/);
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
      dataFound = true;
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
        }
      });
    }
  });

  hasRadarData.value = dataFound;

  if (dataFound) {
    // 🌟 计算大盘雷达平均分
    const dimensions = ["UI美观度", "响应式适配", "语义化与规范", "性能与体验", "交互逻辑"];
    const values = dimensions.map(d => counts[d] > 0 ? Math.round(totals[d] / counts[d]) : 0);
    overallScore.value = Math.round(values.reduce((a, b) => a + b, 0) / values.length) || 0;

    nextTick(() => {
      if (!radarChartRef.value) return;
      if (chartInstance) chartInstance.dispose();
      chartInstance = echarts.init(radarChartRef.value);

      const option = {
        tooltip: { trigger: 'item', formatter: '{b}: {c}分' },
        radar: {
          indicator: dimensions.map(d => ({ name: d, max: 100 })),
          radius: '65%',
          center: ['50%', '50%'],
          axisName: { color: '#475569', fontSize: 13, fontWeight: 'bold', padding: [3, 5] },
          splitArea: { areaStyle: { color: ['#f8fafc', '#f1f5f9', '#f8fafc', '#f1f5f9'] } }
        },
        series: [{
          type: 'radar',
          data: [{
            value: values,
            name: '综合能力得分',
            itemStyle: { color: '#8b5cf6' },
            areaStyle: { color: 'rgba(139, 92, 246, 0.25)' },
            lineStyle: { width: 2, color: '#8b5cf6' },
            symbolSize: 6
          }]
        }]
      };

      chartInstance.setOption(option);
    });
  }
};

watch(() => props.student, async () => {
  await nextTick();
  renderRadar();
}, { deep: true, immediate: true });
</script>

<style scoped>
.web-report-container { display: flex; flex-direction: column; gap: 24px; }

.section-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.section-header .icon { font-size: 20px; }
.section-title { margin: 0; font-size: 17px; font-weight: 800; color: #1e293b; }
.section-sub { margin: 0 0 16px 28px; font-size: 13px; color: #64748b; }

/* 🌟 雷达图与打分区块深度定制 */
.radar-section { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
.radar-wrapper { width: 100%; height: 320px; background: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; display: flex; align-items: center; justify-content: space-between; overflow: hidden; }

/* 左侧得分面板 */
.overall-score-panel { flex: 0 0 240px; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #fff; border-right: 1px dashed #e2e8f0; gap: 12px; padding: 20px; z-index: 2;}
.score-ring { width: 110px; height: 110px; border-radius: 50%; border: 6px solid #e2e8f0; display: flex; align-items: baseline; justify-content: center; flex-direction: row; box-shadow: inset 0 4px 10px rgba(0,0,0,0.05); }
.score-ring.excellent { border-color: #34d399; color: #059669; background: #ecfdf5; box-shadow: 0 0 20px rgba(52,211,153,0.2); }
.score-ring.good { border-color: #fbbf24; color: #d97706; background: #fffbeb; box-shadow: 0 0 20px rgba(251,191,36,0.2); }
.score-ring.poor { border-color: #f87171; color: #dc2626; background: #fef2f2; box-shadow: 0 0 20px rgba(248,113,113,0.2); }
.score-val { font-size: 40px; font-weight: 900; line-height: 110px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial; letter-spacing: -1px;}
.score-unit { font-size: 14px; font-weight: bold; opacity: 0.8; margin-left: 2px;}

.score-label { font-size: 15px; font-weight: 800; color: #334155; letter-spacing: 0.5px; }
.score-desc { font-size: 12px; color: #64748b; text-align: center; line-height: 1.5; padding: 0 10px; }

/* 右侧雷达图容器 */
.radar-chart-container { flex: 1; height: 100%; padding: 10px; }
.radar-chart { width: 100%; height: 100%; }

.radar-empty { width: 100%; height: 320px; background: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; font-size: 14px; gap: 10px; }
.empty-icon { font-size: 32px; opacity: 0.5; }

/* 作品集卡片区 */
.portfolio-section { display: flex; flex-direction: column; gap: 16px; }
.card-list { display: flex; flex-direction: column; gap: 16px; }

.project-card { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.02); transition: transform 0.2s; }
.project-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.05); border-color: #cbd5e1; }

.card-header { padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; }
.card-header.pass { background: #f0fdf4; border-bottom-color: #bbf7d0; }
.card-header.fail { background: #fffbeb; border-bottom-color: #fde68a; }

.project-name { display: flex; align-items: center; gap: 10px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.pass .status-dot { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.4); }
.fail .status-dot { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,0.4); }

.p-name { font-weight: 700; color: #1e293b; font-size: 15px; }

/* 🌟 单次作业精准打分徽章 */
.project-score-badge { display: flex; align-items: center; gap: 10px; background: #fff; padding: 4px 6px 4px 14px; border-radius: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #edf2f7; }
.proj-score { font-size: 16px; font-weight: 900; color: #0f172a; }
.proj-unit { font-size: 11px; color: #94a3b8; font-weight: bold; }
.proj-eval { font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 16px; }
.pass .proj-eval { color: #166534; background: #dcfce3; }
.fail .proj-eval { color: #d97706; background: #fef3c7; }

.card-body { padding: 20px; background: #fff; }
.feedback-title { font-size: 14px; font-weight: 800; color: #475569; margin-bottom: 16px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px;}

/* 彩色文本区块精美样式 */
.feedback-blocks { display: flex; flex-direction: column; gap: 12px; }
.f-block { padding: 14px 16px; border-radius: 8px; border: 1px solid transparent; transition: 0.2s;}
.f-block:hover { transform: translateX(2px); }
.f-block-title { font-size: 13px; font-weight: 800; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
.f-block-content { font-size: 14px; line-height: 1.6; white-space: pre-wrap; margin: 0; }

.f-summary { background: #eff6ff; border-color: #bfdbfe; color: #1e3a8a; }
.f-summary .f-block-title { color: #1d4ed8; }

.f-pros { background: #f0fdf4; border-color: #bbf7d0; color: #14532d; }
.f-pros .f-block-title { color: #15803d; }

.f-cons { background: #fef2f2; border-color: #fecaca; color: #7f1d1d; }
.f-cons .f-block-title { color: #b91c1c; }

.f-advice { background: #fffbeb; border-color: #fde68a; color: #78350f; }
.f-advice .f-block-title { color: #b45309; }

.ai-feedback { margin: 0; font-size: 14px; color: #334155; line-height: 1.6; white-space: pre-wrap; background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; }

.card-footer { padding: 12px 20px; background: #f8fafc; border-top: 1px dashed #e2e8f0; display: flex; gap: 16px; font-size: 12px; color: #64748b; }
.time-tag, .kp-tag { display: flex; align-items: center; background: #fff; border: 1px solid #e2e8f0; padding: 4px 10px; border-radius: 6px; }
</style>