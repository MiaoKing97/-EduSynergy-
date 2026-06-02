<template>
  <div class="grading-manager">
    <div class="dashboard-header">
      <div class="title-area">
        <h3>✅ 智能作业批改工作台</h3>
        <p>一键调动 AI 大模型，对学生提交的作业进行批量智能阅卷与错因分析</p>
      </div>
      <div class="header-controls">
        <button class="btn-fetch" @click="fetchWorkspace()" :disabled="loading || !globalStore.config.feishuToken">
          <span class="sync-icon" :class="{ 'is-spinning': loading }">🔄</span>
          {{ loading ? '同步队列中...' : '刷新作业队列' }}
        </button>
      </div>
    </div>

    <div v-if="!globalStore.config.feishuToken" class="empty-state">
      <div class="empty-icon">📌</div>
      <p>请先在顶部标签栏或「表格大盘管理」中选择一个绑定的飞书多维表格。</p>
    </div>

    <div v-else class="grading-content-layout">
      <div class="panel-left">
        <div class="panel-title flex-between">
          <span>📥 待批改队列 ({{ pendingList.length }})</span>
          <button class="btn-batch-grade" @click="batchGrade" :disabled="isGrading || pendingList.length === 0">
            <span v-if="isGrading" class="spin">🔄</span>
            {{ isGrading ? 'AI 极速批改中...' : '🚀 一键智能批改全部' }}
          </button>
        </div>
        <div class="list-wrapper">
          <div v-if="pendingList.length === 0 && !loading" class="no-data">
            🎉 太棒了！当前没有任何待批改的作业。
          </div>
          <div v-for="item in pendingList" :key="item.record_id" class="task-card">
            <div class="task-info">
              <span class="avatar">🧑‍🎓</span>
              <span class="name">{{ item.student_name }}</span>
              <span class="status pending">等待 AI 批阅</span>
            </div>
            <button class="btn-single-grade" @click="gradeSingle(item)" :disabled="isGrading">
              单份批改
            </button>
          </div>
        </div>
      </div>

      <div class="panel-right">
        <div class="panel-title">
          <span>✅ 近期已完成批改 ({{ gradedList.length }})</span>
        </div>
        <div class="list-wrapper">

          <div v-if="gradedList.length === 0" class="no-data-pretty">
            <div class="no-data-icon">📭</div>
            <span>暂无已批改的记录</span>
            <span class="no-data-sub">左侧批改完成后将自动在此处展示</span>
          </div>

          <div v-for="item in gradedList" :key="item.record_id" class="task-card graded-card">
            <div class="task-top">
              <div class="task-info">
                <span class="avatar">🧑‍🎓</span>
                <div class="stu-meta">
                  <span class="name">{{ item.student_name.replace('-UI评测','') }}</span>
                  <span class="status done">{{ isWebTeacher ? '已完成双端评测' : '已批阅入库' }}</span>
                </div>
              </div>

              <div class="score-ring" :class="getScoreClassNew(isWebTeacher ? getProjectScore(item.feedback) : item.score)">
                <span class="score-val">{{ isWebTeacher ? getProjectScore(item.feedback) : item.score }}</span>
                <span class="score-unit">分</span>
              </div>
            </div>

            <div class="ai-brief-box">
              <div class="brief-title">🤖 AI 简要评价</div>
              <p class="brief-content">{{ getBriefEvaluation(isWebTeacher ? getProjectScore(item.feedback) : item.score, isWebTeacher) }}</p>
            </div>

            <div v-if="isWebTeacher && extractChartDataMini(item.feedback)" class="quick-chart-wrapper">
              <ChartBase :data="extractChartDataMini(item.feedback)" />
            </div>

            <button class="btn-view-report actionable-button" @click="openDetailReport(item)">
              {{ isWebTeacher ? '查看详细 UX 诊断报告 🔍' : '查看完整成绩列表 & 错误分析 🔍' }}
            </button>
          </div>

        </div>
      </div>
    </div>

    <transition name="modal-fade">
      <div v-if="activeDetail" class="modal-backdrop" @click="activeDetail = null">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <div class="modal-title-box">
              <span class="modal-avatar">📊</span>
              <div>
                <h4>{{ activeDetail.student_name.replace('-UI评测','') }} - {{ isWebTeacher ? '响应式设计诊断报表' : '学情诊断详报' }}</h4>
                <p>数据源：飞书多维表格云端数据库分析引擎</p>
              </div>
            </div>
            <button class="modal-close" @click="activeDetail = null">✕</button>
          </div>

          <div class="modal-body custom-scrollbar">
            <GradingReportWeb v-if="isWebTeacher" :detail="activeDetail" />
            <GradingReportNormal v-else :detail="activeDetail" />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated, watch, computed } from 'vue';
import axios from 'axios';
import { globalStore } from '../../store';
import { parseAIContent } from '../../utils/aiDataParser';
import ChartBase from '../renderers/ChartBase.vue';
import GradingReportNormal from '../GradingReportNormal.vue';
import GradingReportWeb from '../GradingReportWeb.vue';

const loading = ref(false);
const isGrading = ref(false);
const pendingList = ref([]);
const gradedList = ref([]);
const activeDetail = ref(null);

const isWebTeacher = computed(() => globalStore.auth.role === 'web_teacher');

const fetchWorkspace = async (isAutoSync = false) => {
  if (!globalStore.config.feishuToken || loading.value) return;
  loading.value = true;
  try {
    if (isAutoSync) await new Promise(resolve => setTimeout(resolve, 800));

    const payload = {
      feishu_app_id: globalStore.config.feishuAppId,
      feishu_app_secret: globalStore.config.feishuAppSecret,
      app_token: globalStore.config.feishuToken
    };
    const res = await axios.post('/api/homework/get_workspace_data', payload);
    if (res.data.status === 'success') {
      pendingList.value = res.data.pending_list || [];
      gradedList.value = res.data.graded_list || [];
    }
  } catch (e) {
    console.error("刷新工作区失败", e);
  } finally {
    loading.value = false;
  }
};

const executeGrade = async (item) => {
  if (!isWebTeacher.value && !globalStore.config.systemPrompt) {
    alert("⚠️ 请先前往「老师模板设置」提取并保存答案解析标尺！");
    return false;
  }
  if (!globalStore.config.apiKey) {
    alert("⚠️ 请先在右侧面板配置大模型的 API Key！");
    return false;
  }

  let finalPrompt = globalStore.config.systemPrompt || "";
  if (globalStore.config.customPrompt) {
    finalPrompt += `\n\n【附加特殊批改要求】：${globalStore.config.customPrompt}`;
  }
  try {
    await axios.post('/api/homework/grade_homework', {
      record_id: item.record_id,
      ai_model: globalStore.config.model,
      api_key: globalStore.config.apiKey,
      system_prompt: finalPrompt,
      feishu_app_id: globalStore.config.feishuAppId,
      feishu_app_secret: globalStore.config.feishuAppSecret,
      app_token: globalStore.config.feishuToken
    });
    return true;
  } catch (e) {
    console.error("批改失败", e);
    return false;
  }
};

const gradeSingle = async (item) => {
  isGrading.value = true;
  const success = await executeGrade(item);
  if (success) await fetchWorkspace();
  else alert(`❌ 批改 ${item.student_name} 的作业时发生错误`);
  isGrading.value = false;
};

const batchGrade = async () => {
  if (!isWebTeacher.value && !globalStore.config.systemPrompt) {
    alert("⚠️ 请先前往「老师模板设置」提取并保存答案解析标尺！");
    return;
  }
  isGrading.value = true;
  const concurrency = globalStore.config.concurrency || 1;
  const items = [...pendingList.value];
  for (let i = 0; i < items.length; i += concurrency) {
    const chunk = items.slice(i, i + concurrency);
    await Promise.all(chunk.map(item => executeGrade(item)));
    await fetchWorkspace();
  }
  isGrading.value = false;
  alert("🎉 队列内作业已全部批改完成！");
};

const openDetailReport = (item) => { activeDetail.value = item; };

// 🌟 核心修复：将三个反引号替换为正则表达式 `{3}` 量词写法，完美绕过 Vue 的编译断行错误！
const getProjectScore = (feedbackStr) => {
  if (!feedbackStr) return 0;
  try {
    const match = String(feedbackStr).match(/`{3}json([\s\S]*?)`{3}/);
    let jsonObj = match ? JSON.parse(match[1].trim()) : null;
    if (!jsonObj) {
      const start = String(feedbackStr).indexOf('{');
      const end = String(feedbackStr).lastIndexOf('}');
      if (start !== -1 && end !== -1) {
        const possibleJson = String(feedbackStr).substring(start, end + 1);
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

const getScoreClassNew = (score) => {
  if (score >= 90) return 'excellent';
  if (score >= 80) return 'good';
  if (score >= 60) return 'pass';
  return 'poor';
};

const getBriefEvaluation = (score, isWeb) => {
  if (isWeb) return '页面双端快照已获取，AI已生成 UX/UI 五维能力雷达图，请参考下方图表诊断。';
  if (score >= 85) return '✨ 卷面表现极为优秀！核心考点掌握扎实，推导步骤严谨完整，基本无常识性或逻辑性纰漏。';
  if (score >= 60) return '💡 成绩达标。基础题型能够稳妥拿下，但部分综合性或多步骤考点存在模糊概念与运算失误。';
  return '🚨 学情预警。当前作业存在明显的知识断层与底层思维陷阱，亟需查漏补缺。';
};

// 🌟 同理修复：替换提取图表数据时的反引号正则
const extractChartDataMini = (feedbackStr) => {
  if (!feedbackStr) return null;
  let cleanStr = feedbackStr.replace(/`{3}json_array[\s\S]*?`{3}/g, '').trim();
  const parsed = parseAIContent(cleanStr);

  if (parsed && parsed.echartsData) {
    const fullOption = parsed.echartsData;
    if (fullOption.radar && fullOption.radar.name) delete fullOption.radar.name;

    return {
      ...fullOption,
      backgroundColor: 'transparent',
      title: { show: false },
      legend: { show: false },
      tooltip: { show: false },
      grid: { top: '5%', bottom: '25%', left: '5%', right: '5%', containLabel: false },
      radar: {
        ...(fullOption.radar || {}),
        center: ['50%', '40%'],
        radius: '43%',
        splitNumber: 4,
        axisName: { color: '#475569', fontSize: 10, fontWeight: 'bold' }
      },
      series: fullOption.series.map(s => ({
        ...s, symbolSize: 4, lineStyle: { width: 2 }, areaStyle: { color: 'rgba(59, 130, 246, 0.35)' }
      }))
    };
  }
  return null;
};

watch(() => globalStore.config.feishuToken, (newVal) => { if (newVal) fetchWorkspace(); });
onMounted(() => { if (globalStore.config.feishuToken) fetchWorkspace(); });
onActivated(() => { if (globalStore.config.feishuToken) fetchWorkspace(true); });
</script>

<style scoped>
/* 旋转动画引擎保留 */
@keyframes spin { 100% { transform: rotate(360deg); } }
.is-spinning { animation: spin 1s linear infinite; }

.grading-manager { display: flex; flex-direction: column; gap: 20px; min-height: 100%; padding-bottom: 20px; position: relative;}
.dashboard-header { display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); padding: 20px 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #edf2f7; }
.title-area h3 { margin: 0 0 6px 0; font-size: 20px; color: #1a202c; font-weight: 700; }
.title-area p { margin: 0; font-size: 13px; color: #718096; }

.btn-fetch { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e2e8f0; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; color: #4a5568; transition: 0.2s; }
.btn-fetch:hover { background: #f8fafc; border-color: #cbd5e1; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; color: #a0aec0; text-align: center; }
.empty-icon { font-size: 50px; margin-bottom: 20px; }

.grading-content-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
.panel-left, .panel-right { background: #fff; border-radius: 12px; border: 1px solid #edf2f7; box-shadow: 0 4px 20px rgba(0,0,0,0.03); overflow: hidden; display: flex; flex-direction: column; max-height: 700px; }
.panel-title { padding: 16px 20px; background: rgba(248, 250, 252, 0.8); border-bottom: 1px solid #edf2f7; font-weight: 700; font-size: 15px; color: #1a202c; display: flex; justify-content: space-between; align-items: center; }
.flex-between { display: flex; justify-content: space-between; align-items: center; }

.btn-batch-grade { background: linear-gradient(135deg, #722ed1 0%, #531dab 100%); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; transition: 0.2s; }
.btn-batch-grade:hover:not(:disabled) { box-shadow: 0 4px 12px rgba(114, 46, 209, 0.3); transform: translateY(-1px); }
.btn-batch-grade:disabled { background: #d3adf7; cursor: not-allowed; }
.spin { display: inline-block; animation: spin 1s linear infinite; }

.list-wrapper { padding: 16px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 12px; }
.no-data { text-align: center; padding: 40px 0; color: #a0aec0; font-size: 14px; }

.task-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; display: flex; justify-content: space-between; align-items: center; transition: 0.2s; background: #fff; }
.task-card:not(.graded-card):hover { border-color: #cbd5e1; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
.task-info { display: flex; align-items: center; gap: 12px; }
.avatar { width: 32px; height: 32px; background: #f1f5f9; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.name { font-weight: 700; color: #1e293b; font-size: 15px; }

.status { font-size: 11px; padding: 4px 10px; border-radius: 20px; font-weight: 800; }
.status.pending { background: #fef3c7; color: #d97706; border: 1px solid #fde68a; }
.status.done { background: #dcfce3; color: #166534; border: 1px solid #bbf7d0; }

.btn-single-grade { background: #eff6ff; border: 1px solid #bfdbfe; color: #2563eb; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 12px; cursor: pointer; transition: 0.2s; }
.btn-single-grade:hover:not(:disabled) { background: #dbeafe; }
.btn-single-grade:disabled { opacity: 0.5; cursor: not-allowed; }

.graded-card { display: flex; flex-direction: column; gap: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
.graded-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.05); border-color: #cbd5e1; }
.task-top { display: flex; justify-content: space-between; align-items: center; }
.stu-meta { display: flex; flex-direction: column; gap: 4px; }

.score-ring { display: flex; align-items: baseline; padding: 6px 14px; border-radius: 20px; font-weight: 900; }
.score-ring.excellent { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
.score-ring.good { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.score-ring.pass { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.score-ring.poor { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.score-val { font-size: 20px; line-height: 1; }
.score-unit { font-size: 11px; margin-left: 2px; opacity: 0.8; font-weight: bold;}

.ai-brief-box { background: #f8fafc; border-radius: 8px; padding: 12px; border-left: 4px solid #94a3b8; }
.brief-title { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 4px; }
.brief-content { font-size: 13px; color: #334155; line-height: 1.5; margin: 0; }

.quick-chart-wrapper { width: 100%; height: 230px; margin-top: 10px; margin-bottom: 12px; background: transparent; display: flex; align-items: center; justify-content: center; pointer-events: none; }
.quick-chart-wrapper :deep(> div) { background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; margin: 0 !important; width: 100% !important; height: 100% !important; pointer-events: none; }
.quick-chart-wrapper :deep(.border-b) { display: none !important; }
.quick-chart-wrapper :deep([ref="chartRef"]), .quick-chart-wrapper :deep(.h-\\[350px\\]) { width: 100% !important; height: 230px !important; pointer-events: auto; }

.actionable-button { position: relative !important; z-index: 5 !important; pointer-events: auto !important; margin-top: 4px; }
.btn-view-report { width: 100%; background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; padding: 10px; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; transition: 0.2s; text-align: center; }
.btn-view-report:hover { background: #e0f2fe; color: #0369a1; border-color: #bae6fd; }

.no-data-pretty { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 250px; color: #94a3b8; font-size: 14px; gap: 6px; }
.no-data-icon { font-size: 40px; opacity: 0.6; }
.no-data-sub { font-size: 11px; color: #cbd5e1; }

.modal-backdrop { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.modal-content { background: #ffffff; width: 850px; max-width: 90%; max-height: 85vh; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); display: flex; flex-direction: column; overflow: hidden; }
.modal-header { padding: 20px 24px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #fff; }
.modal-title-box { display: flex; align-items: center; gap: 14px; }
.modal-avatar { font-size: 24px; background: #f1f5f9; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
.modal-title-box h4 { margin: 0 0 4px 0; font-size: 17px; color: #0f172a; font-weight: 800; }
.modal-title-box p { margin: 0; font-size: 12px; color: #94a3b8; }
.modal-close { background: none; border: none; font-size: 18px; color: #94a3b8; cursor: pointer; transition: 0.2s; padding: 4px; }
.modal-close:hover { color: #1e293b; transform: scale(1.1); }
.modal-body { padding: 24px; overflow-y: auto; background: #f8fafc; }

.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.25s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>