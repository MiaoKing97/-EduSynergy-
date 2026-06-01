<template>
  <div class="report-wrapper">
    <div class="modal-score-banner" :class="getScoreClass(detail.score)">
      <div class="score-num-box">
        <span class="num">{{ detail.score }}</span>
        <span class="unit">分</span>
      </div>
      <div class="score-text-box">
        <h5>综合阅卷评定</h5>
        <p>{{ getDetailedScoreText(detail.score) }}</p>
      </div>
    </div>

    <div class="detail-section mt-5">
      <div class="section-title-mod">📋 完整的成绩列表与诊断图谱</div>
      <div class="analysis-list">
        <div v-for="(line, idx) in parsedFeedback" :key="idx" class="analysis-card" :class="line.isCorrect ? 'is-correct' : 'is-wrong'">
          <div class="card-top">
            <span class="q-indicator" :class="line.isCorrect ? 'bg-success' : 'bg-danger'">
              {{ line.isCorrect ? '✓ 正确' : '✕ 诊断建议' }}
            </span>
            <span class="q-main-info">{{ line.mainInfo }}</span>
          </div>

          <div v-if="(!line.isCorrect && line.errorCause) || line.htmlContent || line.parsedChart" class="card-error-box">
            <strong>🚨 核心错因诊断 / AI 深度评估：</strong>
            <p v-if="!line.htmlContent && !line.parsedChart">{{ line.errorCause }}</p>

            <div v-if="line.htmlContent || line.parsedChart" class="rich-content-box">
              <div class="prose max-w-none text-sm text-slate-700 leading-relaxed markdown-override" v-html="line.htmlContent"></div>
              <ChartBase v-if="line.parsedChart" :data="line.parsedChart" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import MarkdownIt from 'markdown-it';
import { parseAIContent } from '../utils/aiDataParser';
import ChartBase from './renderers/ChartBase.vue';

const props = defineProps({
  detail: { type: Object, required: true }
});

const md = new MarkdownIt({ html: true, breaks: true });

const getScoreClass = (score) => {
  if (score >= 85) return 'good';
  if (score >= 60) return 'pass';
  return 'fail';
};

const getDetailedScoreText = (score) => {
  if (score >= 85) return '本次测评表现惊艳，具备极强的解题逻辑，请保持目前的学习节奏！';
  if (score >= 60) return '整体掌握情况处于及格线以上，请重点关注下方列出的做错题目的考点归集。';
  return '多项核心考点亮起红灯，建议针对薄弱项及时找老师进行精准面对面辅导。';
};

// 提取原有的强力清洗与解析逻辑
const parsedFeedback = computed(() => {
  if (!props.detail.feedback) return [];
  const blocks = props.detail.feedback.split('📝').filter(b => b.trim());

  return blocks.map(block => {
    const isCorrect = block.includes('➡️ 正确') || block.includes('➡️ true');
    let errorCause = '';
    let htmlContent = '';
    let parsedChart = null;

    const causeIndex = block.indexOf('🚨 错因:');
    if (causeIndex !== -1) {
      let rawCause = block.substring(causeIndex + 6).trim();
      rawCause = rawCause.replace(/```json_array[\s\S]*?```/g, '').trim();
      if (rawCause.includes('```json') || rawCause.includes('```') || rawCause.includes('**')) {
        const parsed = parseAIContent(rawCause);
        parsedChart = parsed.echartsData;
        htmlContent = md.render(parsed.text);
      } else {
        errorCause = rawCause;
      }
    }
    const mainLine = block.split('\n')[0] || '';
    let mainInfo = mainLine.replace('➡️ 正确', '').replace('➡️ 错误', '').trim();

    return { isCorrect, mainInfo, errorCause, htmlContent, parsedChart };
  });
});
</script>

<style scoped>
.modal-score-banner { display: flex; align-items: center; gap: 20px; padding: 16px 20px; border-radius: 12px; box-shadow: inset 0 1px 2px rgba(255,255,255,0.6); }
.modal-score-banner.good { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce3 100%); border: 1px solid #bbf7d0; color: #14532d; }
.modal-score-banner.pass { background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 1px solid #fde68a; color: #78350f; }
.modal-score-banner.fail { background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 1px solid #fecaca; color: #7f1d1d; }
.score-num-box { display: flex; align-items: baseline; }
.score-num-box .num { font-size: 36px; font-weight: 900; line-height: 1; }
.score-num-box .unit { font-size: 14px; margin-left: 2px; font-weight: 700; }
.score-text-box h5 { margin: 0 0 4px 0; font-size: 15px; font-weight: 800; }
.score-text-box p { margin: 0; font-size: 12px; opacity: 0.85; font-weight: 500; }

.mt-5 { margin-top: 20px; }
.section-title-mod { font-size: 14px; font-weight: 800; color: #1e293b; display: flex; align-items: center; gap: 6px; }
.section-title-mod::before { content: ''; width: 4px; height: 14px; background: #2563eb; border-radius: 2px; }
.analysis-list { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }

.analysis-card { background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.analysis-card.is-correct { border-left: 4px solid #10b981; }
.analysis-card.is-wrong { border-left: 4px solid #ef4444; background: #fffafb; border-color: #fca5a5; }

.card-top { display: flex; align-items: center; gap: 10px; }
.q-indicator { font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 4px; color: #fff; }
.q-indicator.bg-success { background: #10b981; }
.q-indicator.bg-danger { background: #ef4444; }
.q-main-info { font-size: 13.5px; font-weight: 600; color: #334155; line-height: 1.4; }

.card-error-box { background: #fef2f2; border: 1px dashed #fca5a5; border-radius: 6px; padding: 10px 14px; font-size: 13px; }
.card-error-box strong { color: #991b1b; display: block; margin-bottom: 2px; }
.card-error-box p { margin: 0; color: #b91c1c; line-height: 1.5; font-weight: 500; }
.rich-content-box { margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(239, 68, 68, 0.2); }

:deep(.markdown-override p) { margin-top: 0; margin-bottom: 8px; }
:deep(.markdown-override p:last-child) { margin-bottom: 0; }
:deep(.markdown-override ul), :deep(.markdown-override ol) { margin-top: 4px; margin-bottom: 8px; padding-left: 20px; }
</style>