<template>
  <div class="report-wrapper">

    <div class="report-banner">
      <span class="banner-icon">✨</span>
      <div class="banner-text">
        <strong>网页多设备响应式与 UX/UI 体验设计报告</strong>
        <p>AI 视觉引擎已对 PC 端与移动端快照进行像素级对齐分析与诊断。</p>
      </div>
    </div>

    <div class="semantic-report-container">

      <div v-if="parsedReport.intro" class="section-block intro-block">
        <div class="prose markdown-override" v-html="parsedReport.intro"></div>
      </div>

      <div v-if="parsedReport.advantages" class="section-block advantage-card">
        <div class="block-header text-emerald-700">
          <span class="block-icon">🟢</span> <strong>现有优点与亮点</strong>
        </div>
        <div class="prose markdown-override mt-2" v-html="parsedReport.advantages"></div>
      </div>

      <div v-if="parsedReport.disadvantages" class="section-block defect-card">
        <div class="block-header text-rose-700">
          <span class="block-icon">🔴</span> <strong>现存明显缺陷</strong>
        </div>
        <div class="prose markdown-override mt-2" v-html="parsedReport.disadvantages"></div>
      </div>

      <div v-if="parsedReport.suggestions" class="section-block suggestion-card">
        <div class="block-header text-blue-700">
          <span class="block-icon">🔵</span> <strong>架构优化与改进建议</strong>
        </div>
        <div class="prose markdown-override mt-2" v-html="parsedReport.suggestions"></div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt({ html: true, breaks: true });

const props = defineProps({
  detail: {
    type: Object,
    required: true
  }
});

const parsedReport = computed(() => {
  if (!props.detail || !props.detail.feedback) return {};

  // 1. 物理移除可能夹杂在最后的 JSON 配置串
  let text = props.detail.feedback;
  text = text.replace(/```json_array[\s\S]*?```/g, '')
             .replace(/```json[\s\S]*?```/g, '')
             .replace(/\{[\s\S]*"radar"[\s\S]*\}/, '')
             .trim();

  // 2. 🌟 核心修复：使用正则表达式定义宽容的切片分流标识
  // 适配各种 ## 现有优点、**现有优点**、【现有优点】、现有优点：等各种野生排版
  const advRegex = /(?:#*\s*\*?【?现有优点】?.*?)(?:\n|$)/i;
  const disRegex = /(?:#*\s*\*?【?(?:现存明显缺陷|现存缺陷|现存问题|存在问题|主要缺陷|缺陷)】?.*?)(?:\n|$)/i;
  const sugRegex = /(?:#*\s*\*?【?(?:改进建议|优化建议|改进意见|建议)】?.*?)(?:\n|$)/i;

  let intro = '';
  let advantages = '';
  let disadvantages = '';
  let suggestions = '';

  // 执行正则搜寻
  const advMatch = text.match(advRegex);
  const disMatch = text.match(disRegex);
  const sugMatch = text.match(sugRegex);

  // 3. 动态边界锚定算法：抓取各自命中的起止点进行切片
  if (advMatch && disMatch && sugMatch) {
    const advStart = advMatch.index;
    const advLen = advMatch[0].length;

    const disStart = disMatch.index;
    const disLen = disMatch[0].length;

    const sugStart = sugMatch.index;
    const sugLen = sugMatch[0].length;

    // 斩断各流区间
    intro = text.substring(0, advStart).replace(/详细综合评价|详细的综合评价文字/g, '').trim();
    advantages = text.substring(advStart + advLen, disStart).trim();
    disadvantages = text.substring(disStart + disLen, sugStart).trim();
    suggestions = text.substring(sugStart + sugLen).trim();
  } else {
    // 降级沙盒：如果有些古怪作业实在匹配不到，交由基础段落渲染，绝不报错崩白屏
    intro = text;
  }

  // 4. 清理残留的头部冒号等杂质并渲染 Markdown
  const cleanHead = (str) => str.replace(/^[:：\s]+/, '').trim();

  return {
    intro: md.render(intro),
    advantages: advantages ? md.render(cleanHead(advantages)) : '',
    disadvantages: disadvantages ? md.render(cleanHead(disadvantages)) : '',
    suggestions: suggestions ? md.render(cleanHead(suggestions)) : ''
  };
});
</script>

<style scoped>
.report-wrapper { display: flex; flex-direction: column; gap: 16px; }

.report-banner { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce3 100%); border: 1px solid #bbf7d0; border-radius: 10px; padding: 14px 20px; display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.banner-icon { font-size: 20px; }
.banner-text strong { color: #166534; font-size: 15px; display: block; margin-bottom: 4px;}
.banner-text p { margin: 0; color: #15803d; font-size: 13px; }

/* 卡片容器 */
.semantic-report-container { display: flex; flex-direction: column; gap: 16px; }
.section-block { padding: 18px 20px; border-radius: 12px; }
.intro-block { background: #f8fafc; border: 1px dashed #cbd5e1; }

.block-header { display: flex; align-items: center; gap: 8px; font-size: 15px; margin-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 10px;}
.block-icon { font-size: 16px; }

/* 🟢 翠绿优点卡 */
.advantage-card { background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%); border: 1px solid #bbf7d0; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.05);}
/* 🔴 猩红缺陷卡 */
.defect-card { background: linear-gradient(180deg, #fef2f2 0%, #ffffff 100%); border: 1px solid #fecaca; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.05);}
/* 🔵 幽蓝建议卡 */
.suggestion-card { background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%); border: 1px solid #bae6fd; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.05);}

/* Markdown 样式重写 */
:deep(.markdown-override p) { margin-top: 0; margin-bottom: 8px; font-size: 14px; color: #334155; line-height: 1.6; }
:deep(.markdown-override p:last-child) { margin-bottom: 0; }
:deep(.markdown-override ul), :deep(.markdown-override ol) { margin-top: 6px; margin-bottom: 6px; padding-left: 20px; }
:deep(.markdown-override li) { color: #475569; margin-bottom: 6px; font-size: 14px; line-height: 1.6;}
:deep(.markdown-override strong) { color: #0f172a; font-weight: 700; }
</style>