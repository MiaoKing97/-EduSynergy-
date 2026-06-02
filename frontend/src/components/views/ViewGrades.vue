<template>
  <div class="grades-manager">
    <div class="dashboard-header">
      <div class="title-area">
        <h3>🧑‍🎓 学生成绩档案中心</h3>
        <p>动态调取全班学生历史成绩大盘，生成个性化多维诊断报告</p>
      </div>
      <div class="header-controls">
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
        <div class="panel-left">
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

        <div class="panel-right">
          <div v-if="!selectedStudent" class="sub-empty-state">
            <div class="sub-empty-icon">👈</div>
            <p>请在左侧点击任意一位学生的行记录，调阅其独家学情诊断报告。</p>
          </div>

          <div v-else class="student-report-card">

            <div class="report-header">
              <div class="report-user-info">
                <h4>{{ selectedStudent.name.replace('-UI评测','') }} 的个性化学情报告</h4>
                <span class="report-time">档案状态：飞书数据流云端实时对齐中</span>
              </div>

              <div v-if="isWebTeacher" class="web-score-badge">
                <span class="badge-icon">✨</span>
                <span class="badge-text">UI/UX 画像就绪</span>
              </div>
              <div v-else class="report-score-box" :style="{ borderColor: getScoreColor(selectedStudent.score) }">
                <div class="report-score-val" :style="{ color: getScoreColor(selectedStudent.score) }">{{ selectedStudent.score }}</div>
                <div class="report-score-label">综合得分</div>
              </div>
            </div>

            <div class="report-stats-grid">
              <div class="stat-card">
                <div class="stat-label">{{ isWebTeacher ? '全卷项目' : '全卷作答' }}</div>
                <div class="stat-num text-black">{{ selectedStudent.total }} {{ isWebTeacher ? '项' : '题' }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">{{ isWebTeacher ? '规范合格' : '稳妥做对' }}</div>
                <div class="stat-num text-green">{{ selectedStudent.correct }} {{ isWebTeacher ? '项' : '题' }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">{{ isWebTeacher ? '待优化区' : '薄弱做错' }}</div>
                <div class="stat-num" :class="isWebTeacher ? 'text-orange' : 'text-red'">
                  {{ selectedStudent.wrong }} {{ isWebTeacher ? '项' : '题' }}
                </div>
              </div>
            </div>

            <GradesReportWeb v-if="isWebTeacher" :student="selectedStudent" />
            <GradesReportNormal v-else :student="selectedStudent" />

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
import GradesReportNormal from '../GradesReportNormal.vue';
import GradesReportWeb from '../GradesReportWeb.vue';

const loading = ref(false);
const rawRecords = ref([]);
const workspaceGradedList = ref([]);
const selectedStudent = ref(null);

const isWebTeacher = computed(() => globalStore.auth.role === 'web_teacher');

const checkPass = (status) => {
  const s = String(status || '').trim();
  return s === '正确' || s.includes('部分正确') || s.includes('基本正确') || s.includes('合格') || s === 'true';
};

const sanitizeName = (name) => name ? String(name).normalize('NFC').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, '').trim() : '未知学生';

// 🌟 辅助提取器：专门提取单次网页作业的雷达图平均分
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

// 🌟 数据核心重构：精确计算网页平均分
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
      // 网页老师：雷达图综合得分平均值
      dynamicScore = stu.webCount > 0 ? Math.round(stu.sumWebScore / stu.webCount) : 0;
    } else {
      // 普通老师：基于正确题数的卷面分
      dynamicScore = stu.total > 0 ? Math.round((stu.correct / stu.total) * 100) : 0;
    }
    return { ...stu, score: dynamicScore };
  }).sort((a, b) => b.score - a.score);
});

// 🌟 四档位色彩与标签分发逻辑
const getScoreLabel = (score) => {
  if (score >= 90) return '优秀';
  if (score >= 80) return '良好';
  if (score >= 60) return '及格';
  return '待优化';
};

const getScoreColor = (score) => {
  if (score >= 90) return '#10b981'; // 绿
  if (score >= 80) return '#3b82f6'; // 蓝
  if (score >= 60) return '#f59e0b'; // 橙
  return '#ef4444'; // 红
};

const selectStudent = (student) => { selectedStudent.value = student; };

const fetchGradesData = async (forceSync = false, isAutoSync = false) => {
  const token = globalStore.config.feishuToken;
  if (!token || loading.value) return;

  if (globalStore.tableDataCache[token + '_grades'] && !forceSync) {
    rawRecords.value = globalStore.tableDataCache[token + '_grades'].rawRecords;
    workspaceGradedList.value = globalStore.tableDataCache[token + '_grades'].workspace;
  }

  loading.value = true;
  try {
    if (isAutoSync) await new Promise(resolve => setTimeout(resolve, 800));

    const payload = { feishu_app_id: globalStore.config.feishuAppId, feishu_app_secret: globalStore.config.feishuAppSecret, app_token: token };
    const [dashRes, workRes] = await Promise.all([
      axios.post('/api/homework/get_dashboard_stats', payload),
      axios.post('/api/homework/get_workspace_data', payload)
    ]);
    if (dashRes.data.status === 'success') rawRecords.value = dashRes.data.stats.raw_records || [];
    if (workRes.data.status === 'success') workspaceGradedList.value = workRes.data.graded_list || [];
    globalStore.tableDataCache[token + '_grades'] = { rawRecords: rawRecords.value, workspace: workspaceGradedList.value };

    if (studentList.value.length > 0 && !selectedStudent.value) selectedStudent.value = studentList.value[0];
  } catch (e) { console.error(e); } finally { loading.value = false; }
};

onMounted(() => { if (globalStore.config.feishuToken) fetchGradesData(true); });
onActivated(() => { if (globalStore.config.feishuToken) fetchGradesData(true, true); });
</script>

<style scoped>
/* 旋转动画引擎保留 */
@keyframes spin { 100% { transform: rotate(360deg); } }
.is-spinning { animation: spin 1s linear infinite; }

.grades-manager { display: flex; flex-direction: column; gap: 20px; min-height: 100%; padding-bottom: 20px; position: relative;}
.dashboard-header { display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); padding: 20px 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #edf2f7; }
.title-area h3 { margin: 0 0 6px 0; font-size: 20px; color: #1a202c; font-weight: 700; }
.title-area p { margin: 0; font-size: 13px; color: #718096; }
.btn-fetch { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e2e8f0; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; color: #4a5568; transition: 0.2s; }
.btn-fetch:hover:not(:disabled) { background: #f0f7ff; color: #1890ff; border-color: #1890ff; }

.loading-state, .empty-state, .sub-empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 350px; color: #a0aec0; }
.empty-icon, .sub-empty-icon { font-size: 50px; margin-bottom: 20px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.05)); }
.spinner { width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }

.grades-content-layout { display: grid; grid-template-columns: 45% 55%; gap: 20px; align-items: start; }
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

/* 🌟 分数条样式深度优化 */
.score-badge-container { display: flex; flex-direction: column; gap: 6px; }
.score-text-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 2px; }
.score-text { font-size: 13px; font-weight: 800; }
.score-number { font-size: 12px; font-weight: 700; color: #64748b; }
.mini-progress-bar { width: 100%; height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; transition: width 0.5s ease; }

.btn-view-detail { padding: 6px 12px; background: #fff; border: 1px solid #cbd5e1; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; color: #475569;}
.btn-view-detail:hover { background: #f8fafc; border-color: #94a3b8; color: #0f172a;}

.student-report-card { padding: 24px; display: flex; flex-direction: column; gap: 20px; max-height: 750px; overflow-y: auto; }
.report-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #edf2f7; padding-bottom: 20px; }
.report-user-info h4 { margin: 0 0 6px; font-size: 18px; color: #0f172a; font-weight: 800;}
.report-time { font-size: 12px; color: #64748b; }

.web-score-badge { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce3 100%); border: 1px solid #bbf7d0; padding: 10px 16px; border-radius: 50px; display: flex; align-items: center; gap: 8px;}
.badge-icon { font-size: 18px; }
.badge-text { color: #166534; font-weight: 800; font-size: 14px; }

.report-score-box { border: 3px solid #edf2f7; width: 70px; height: 70px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.report-score-val { font-size: 22px; font-weight: 900; }
.report-score-label { font-size: 10px; color: #64748b; font-weight: bold;}

.report-stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; background: #f8fafc; border-radius: 10px; padding: 16px; border: 1px solid #f1f5f9;}
.stat-card { display: flex; flex-direction: column; align-items: center; gap: 6px; border-right: 1px solid #e2e8f0;}
.stat-card:last-child { border-right: none; }
.stat-label { font-size: 13px; color: #64748b; font-weight: 600;}
.stat-num { font-size: 20px; font-weight: 900; }
.text-black { color: #1e293b; }
.text-green { color: #10b981; }
.text-red { color: #ef4444; }
.text-orange { color: #f59e0b; }
</style>