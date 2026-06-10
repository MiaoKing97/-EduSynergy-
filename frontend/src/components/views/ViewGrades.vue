<template>
  <div class="grades-manager">
    <div class="dashboard-header no-print">
      <div class="title-area">
        <h3>🧑‍🎓 学生成绩档案中心</h3>
        <p>动态调取全班学生历史成绩大盘，生成个性化多维诊断报告</p>
      </div>
      <div class="header-controls">
        <button class="btn-fetch" @click="exportClassExcel" :disabled="studentList.length === 0" title="导出班级 CSV（可用 Excel 打开）">
          📊 导出班级 CSV
        </button>
        <button class="btn-fetch" @click="fetchGradesData(true)" :disabled="loading || !globalStore.config.feishuToken">
          <span class="sync-icon" :class="{ 'is-spinning': loading }">🔄</span>
          {{ loading ? '云端同步中...' : '强制同步最新档案' }}
        </button>
      </div>
    </div>

    <div v-if="!globalStore.config.feishuToken" class="empty-state">
      <div class="empty-icon">🔑</div>
      <p>请先在右侧面板配置您的飞书多维表格 AppToken。</p>
    </div>
    <div v-else-if="loading && studentList.length === 0" class="loading-state">
      <div class="spinner"></div><p>正在穿透飞书多维云端数据库，进行归集精算...</p>
    </div>
    <div v-else-if="!loading && studentList.length === 0" class="empty-state">
      <div class="empty-icon">📭</div><p>未探测到有效的档案数据，请确认是否已完成 AI 判卷。</p>
    </div>

    <template v-else>
      <div class="grades-content-layout">
        <div class="panel-left no-print">
          <div class="panel-title">
            <span>📊 班级成绩大盘总览</span>
            <span class="student-count">共 <strong>{{ studentList.length }}</strong> 名档案</span>
          </div>
          <div class="table-wrapper">
            <table class="grades-table">
              <thead>
                <tr>
                  <th width="30%">学生姓名</th>
                  <th width="20%">{{ isWebTeacher ? '评审项目数' : '总答题量' }}</th>
                  <th width="35%">综合评分 / 进度</th>
                  <th width="15%">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="student in studentList" :key="student.name" :class="{ 'is-selected': selectedStudent && selectedStudent.name === student.name }" @click="selectStudent(student)">
                  <td class="stu-name"><div class="avatar-sm">🧑‍🎓</div>{{ student.name.replace('-UI评测','') }}</td>
                  <td class="text-neutral">{{ student.total }} {{ isWebTeacher ? '项' : '题' }}</td>
                  <td>
                    <div class="score-badge-container">
                      <div class="score-text-header">
                        <span class="score-text" :style="{ color: getScoreColor(student.score) }">
                          {{ getScoreLabel(student.score) }}
                        </span>
                        <span class="score-number">{{ student.score }} 分</span>
                      </div>
                      <div class="mini-progress-bar">
                        <div class="progress-fill" :style="{ width: student.score + '%', backgroundColor: getScoreColor(student.score) }"></div>
                      </div>
                    </div>
                  </td>
                  <td><button class="btn-view-detail" @click.stop="selectStudent(student)">学情 🔍</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="panel-right" id="printable-report">
          <div v-if="!selectedStudent" class="sub-empty-state">
            <div class="sub-empty-icon">👈</div>
            <p>请在左侧点击任意一位学生的行记录，调阅其独家学情诊断报告。</p>
          </div>

          <div v-else class="student-report-card">
            <!-- 🌟 导出工具条 -->
            <div class="export-toolbar no-print">
              <button class="export-btn" @click="exportPdf" title="弹出浏览器打印窗口，选择'另存为 PDF'">
                📄 导出学生 PDF
              </button>
              <button class="export-btn" @click="copyParentFeedback" title="复制家长反馈文案到剪贴板">
                💬 复制家长反馈
              </button>
              <span v-if="copyTip" class="copy-tip">{{ copyTip }}</span>
            </div>

            <!-- 🌟 普通学科：画像卡（替代旧的简略头部） -->
            <template v-if="!isWebTeacher">
              <StudentProfileCard
                ref="profileRef"
                :student="selectedStudent"
                :subject="globalStore.auth.subject || '通用学科'"
                :rank="getStudentRank(selectedStudent)"
                :total-students="studentList.length"
              />
              <GradesReportNormal :student="selectedStudent" />
            </template>

            <!-- 网页设计：保留原有视觉报告 -->
            <template v-else>
              <div class="report-header">
                <div class="report-user-info">
                  <h4>{{ selectedStudent.name.replace('-UI评测','') }} 的个性化学情报告</h4>
                  <span class="report-time">档案状态：飞书数据流云端实时对齐中</span>
                </div>
                <div class="web-score-badge">
                  <span class="badge-icon">✨</span>
                  <span class="badge-text">UI/UX 画像就绪</span>
                </div>
              </div>

              <div class="report-stats-grid">
                <div class="stat-card">
                  <div class="stat-label">全卷项目</div>
                  <div class="stat-num text-black">{{ selectedStudent.total }} 项</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">规范合格</div>
                  <div class="stat-num text-green">{{ selectedStudent.correct }} 项</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">待优化区</div>
                  <div class="stat-num text-orange">{{ selectedStudent.wrong }} 项</div>
                </div>
              </div>

              <GradesReportWeb :student="selectedStudent" />
            </template>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue';
import axios from 'axios';
import { globalStore } from '../../store';
import syncCenter from '../../services/syncCenter';
import GradesReportNormal from '../GradesReportNormal.vue';
import GradesReportWeb from '../GradesReportWeb.vue';
import StudentProfileCard from '../StudentProfileCard.vue';

const loading = ref(false);
const rawRecords = ref([]);
const workspaceGradedList = ref([]);
const selectedStudent = ref(null);
const profileRef = ref(null);
const copyTip = ref('');

const isWebTeacher = computed(() => globalStore.auth.role === 'web_teacher');

const checkPass = (status) => {
  const s = String(status || '').trim();
  return s === '正确' || s.includes('部分正确') || s.includes('基本正确') || s.includes('合格') || s === 'true';
};

const sanitizeName = (name) => name ? String(name).normalize('NFC').replace(/[​-‍﻿]/g, '').replace(/\s+/g, '').trim() : '未知学生';

const getWebScore = (errorCause) => {
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

const studentList = computed(() => {
  if (rawRecords.value.length === 0) return [];
  const map = {};
  rawRecords.value.forEach(record => {
    const sName = sanitizeName(record.student_name);
    if (!map[sName]) map[sName] = { name: sName, total: 0, correct: 0, wrong: 0, records: [], wrongRecords: [], sumWebScore: 0, webCount: 0 };
    map[sName].total++;
    map[sName].records.push(record);

    if (checkPass(record.is_correct)) {
      map[sName].correct++;
    } else {
      map[sName].wrong++;
      map[sName].wrongRecords.push(record);
    }

    if (isWebTeacher.value) {
      const score = getWebScore(record.error_cause);
      map[sName].sumWebScore += score;
      map[sName].webCount++;
    }
  });

  return Object.values(map).map(stu => {
    let dynamicScore = 0;
    if (isWebTeacher.value) {
      dynamicScore = stu.webCount > 0 ? Math.round(stu.sumWebScore / stu.webCount) : 0;
    } else {
      dynamicScore = stu.total > 0 ? Math.round((stu.correct / stu.total) * 100) : 0;
    }
    return { ...stu, score: dynamicScore };
  }).sort((a, b) => b.score - a.score);
});

const getStudentRank = (student) => {
  const idx = studentList.value.findIndex(s => s.name === student.name);
  return idx >= 0 ? idx + 1 : 0;
};

const getScoreLabel = (score) => {
  if (score >= 90) return '优秀';
  if (score >= 80) return '良好';
  if (score >= 60) return '及格';
  return '待优化';
};

const getScoreColor = (score) => {
  if (score >= 90) return '#10b981';
  if (score >= 80) return '#3b82f6';
  if (score >= 60) return '#f59e0b';
  return '#ef4444';
};

const selectStudent = (student) => { selectedStudent.value = student; };

const fetchGradesData = async (forceSync = false, isAutoSync = false) => {
  const token = globalStore.config.feishuToken;
  if (!token || loading.value) return;

  loading.value = true;
  try {
    if (isAutoSync) await new Promise(resolve => setTimeout(resolve, 800));
    const data = await syncCenter.loadGradesData(token, forceSync);
    if (data) {
      rawRecords.value = data.rawRecords || [];
      workspaceGradedList.value = data.workspace || [];
    }
    if (studentList.value.length > 0 && !selectedStudent.value) selectedStudent.value = studentList.value[0];
  } catch (e) {
    if (e.response && e.response.data && e.response.data.detail) {
      console.error("加载成绩数据失败:", e.response.data.detail);
      alert("❌ 加载数据失败: " + e.response.data.detail);
    } else {
      console.error("加载成绩数据失败:", e);
    }
  } finally { loading.value = false; }
};

// 🌟 导出：PDF 走浏览器打印对话框（@media print 已注入打印样式）
const exportPdf = () => {
  if (!selectedStudent.value) return;
  document.title = `${selectedStudent.value.name.replace('-UI评测','')}_学情报告_${new Date().toISOString().slice(0,10)}`;
  setTimeout(() => { window.print(); }, 100);
};

// 🌟 导出：班级 CSV
const exportClassExcel = () => {
  if (studentList.value.length === 0) return;
  const headers = ['排名', '姓名', '总题数', '答对', '答错', '正确率%', '综合得分', '等级'];
  const rows = studentList.value.map((s, i) => [
    i + 1,
    s.name.replace('-UI评测', ''),
    s.total,
    s.correct,
    s.wrong,
    s.total > 0 ? Math.round((s.correct / s.total) * 100) : 0,
    s.score,
    getScoreLabel(s.score),
  ]);
  const csv = '﻿' + [headers, ...rows].map(r =>
    r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')
  ).join('\r\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `班级成绩档案_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};

// 🌟 复制家长反馈
const copyParentFeedback = async () => {
  if (!selectedStudent.value) return;
  const s = selectedStudent.value;
  const cleanName = s.name.replace('-UI评测', '');
  const rate = s.total > 0 ? Math.round((s.correct / s.total) * 100) : 0;

  // 取画像卡里的 AI 建议（如果可用）
  let advice = '建议保持当前节奏，继续巩固基础。';
  if (profileRef.value?.aiAdvice) advice = profileRef.value.aiAdvice;

  // 取最薄弱知识点
  let weakKp = '';
  if (profileRef.value?.kpStats) {
    const weak = profileRef.value.kpStats.filter(k => k.rate < 60).slice(0, 2).map(k => k.name);
    if (weak.length) weakKp = `当前薄弱知识点：${weak.join('、')}。`;
  }

  const text = `家长您好：

${cleanName} 同学在本次作业中累计作答 ${s.total} 题，正确 ${s.correct} 题，正确率 ${rate}%，综合得分 ${s.score} 分（${getScoreLabel(s.score)}）。

${weakKp}${advice}

请家长配合关注孩子近期学习状态，如有疑问可随时联系老师。

—— ${globalStore.auth.subject || ''} 任课老师
${new Date().toLocaleDateString()}`;

  try {
    await navigator.clipboard.writeText(text);
    copyTip.value = '✅ 已复制到剪贴板';
  } catch (e) {
    // 降级：弹出 prompt 让用户手动复制
    window.prompt('请手动复制以下家长反馈：', text);
    copyTip.value = '';
    return;
  }
  setTimeout(() => { copyTip.value = ''; }, 3000);
};

onMounted(() => { if (globalStore.config.feishuToken) fetchGradesData(true); });
onActivated(() => { if (globalStore.config.feishuToken) fetchGradesData(true, true); });
</script>

<style scoped>
@keyframes spin { 100% { transform: rotate(360deg); } }
.is-spinning { animation: spin 1s linear infinite; }

.grades-manager { display: flex; flex-direction: column; gap: 20px; min-height: 100%; padding-bottom: 20px; position: relative;}
.dashboard-header { display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); padding: 20px 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #edf2f7; gap: 16px; flex-wrap: wrap;}
.title-area h3 { margin: 0 0 6px 0; font-size: 20px; color: #1a202c; font-weight: 700; }
.title-area p { margin: 0; font-size: 13px; color: #718096; }
.header-controls { display: flex; gap: 10px; flex-wrap: wrap; }
.btn-fetch { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e2e8f0; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; color: #4a5568; transition: 0.2s; }
.btn-fetch:hover:not(:disabled) { background: #f0f7ff; color: var(--edu-primary, #1890ff); border-color: var(--edu-primary, #1890ff); }
.btn-fetch:disabled { opacity: 0.5; cursor: not-allowed; }

.loading-state, .empty-state, .sub-empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 350px; color: #a0aec0; }
.empty-icon, .sub-empty-icon { font-size: 50px; margin-bottom: 20px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.05)); }
.spinner { width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }

.grades-content-layout { display: grid; grid-template-columns: 42% 58%; gap: 20px; align-items: start; }
.panel-left, .panel-right { background: #fff; border-radius: 12px; border: 1px solid #edf2f7; box-shadow: 0 4px 20px rgba(0,0,0,0.03); overflow: hidden; }
.panel-title { padding: 16px 20px; background: #f8fafc; border-bottom: 1px solid #edf2f7; font-weight: 700; display: flex; justify-content: space-between; font-size: 15px; color: #1e293b;}
.student-count strong { color: #3b82f6; font-size: 16px; }

.table-wrapper { overflow-y: auto; max-height: 700px; }
.grades-table { width: 100%; border-collapse: collapse; text-align: left; }
.grades-table th { background: #f8fafc; padding: 14px 16px; font-size: 13px; color: #718096; border-bottom: 1px solid #edf2f7;}
.grades-table td { padding: 14px 16px; border-bottom: 1px solid #edf2f7; font-size: 14px; cursor: pointer; transition: 0.2s;}
.grades-table tr:hover { background: #f8fafc; }
.grades-table tr.is-selected { background-color: #eff6ff !important; border-left: 3px solid #3b82f6; }

.stu-name { display: flex; align-items: center; gap: 8px; font-weight: bold; color: #1e293b;}
.avatar-sm { width: 28px; height: 28px; background: #e2e8f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px;}

.score-badge-container { display: flex; flex-direction: column; gap: 6px; }
.score-text-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 2px; }
.score-text { font-size: 13px; font-weight: 800; }
.score-number { font-size: 12px; font-weight: 700; color: #64748b; }
.mini-progress-bar { width: 100%; height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; transition: width 0.5s ease; }

.btn-view-detail { padding: 6px 12px; background: #fff; border: 1px solid #cbd5e1; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; color: #475569;}
.btn-view-detail:hover { background: #f8fafc; border-color: #94a3b8; color: #0f172a;}

.student-report-card { padding: 20px; display: flex; flex-direction: column; gap: 18px; max-height: 760px; overflow-y: auto; }

/* 🌟 导出工具条 */
.export-toolbar {
  display: flex; gap: 8px; align-items: center;
  padding: 10px 12px; border-radius: 10px;
  background: linear-gradient(135deg, #f0f9ff 0%, #fdf4ff 100%);
  border: 1px dashed #c4b5fd;
}
.export-btn {
  padding: 8px 14px; border-radius: 8px;
  border: 1px solid #e2e8f0; background: #fff; color: #475569;
  font-size: 12px; font-weight: 800; cursor: pointer; transition: 0.2s;
}
.export-btn:hover { border-color: #2563eb; color: #1d4ed8; background: #eff6ff; transform: translateY(-1px); }
.copy-tip { margin-left: auto; font-size: 12px; color: #047857; font-weight: 800; }

/* 网页设计旧版报告头 */
.report-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #edf2f7; padding-bottom: 20px; }
.report-user-info h4 { margin: 0 0 6px; font-size: 18px; color: #0f172a; font-weight: 800;}
.report-time { font-size: 12px; color: #64748b; }
.web-score-badge { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce3 100%); border: 1px solid #bbf7d0; padding: 10px 16px; border-radius: 50px; display: flex; align-items: center; gap: 8px;}
.badge-icon { font-size: 18px; }
.badge-text { color: #166534; font-weight: 800; font-size: 14px; }

.report-stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; background: #f8fafc; border-radius: 10px; padding: 16px; border: 1px solid #f1f5f9;}
.stat-card { display: flex; flex-direction: column; align-items: center; gap: 6px; border-right: 1px solid #e2e8f0;}
.stat-card:last-child { border-right: none; }
.stat-label { font-size: 13px; color: #64748b; font-weight: 600;}
.stat-num { font-size: 20px; font-weight: 900; }
.text-black { color: #1e293b; }
.text-green { color: #10b981; }
.text-red { color: #ef4444; }
.text-orange { color: #f59e0b; }

/* 🌟 打印样式：只导出右侧画像卡 */
@media print {
  @page { size: A4; margin: 12mm; }
  body * { visibility: hidden !important; }
  #printable-report, #printable-report * { visibility: visible !important; }
  #printable-report {
    position: absolute !important;
    left: 0 !important; top: 0 !important;
    width: 100% !important; max-height: none !important;
    overflow: visible !important;
    background: #fff !important;
    box-shadow: none !important; border: none !important;
  }
  .no-print, .no-print * { display: none !important; }
  .student-report-card { max-height: none !important; overflow: visible !important; padding: 0 !important; }
}
</style>
