<template>
  <div class="profile-card">
    <!-- 头部：基本信息 + 综合评估 -->
    <div class="profile-head">
      <div class="avatar-block">
        <div class="avatar-big">🧑‍🎓</div>
        <div class="avatar-text">
          <h3>{{ cleanName }}</h3>
          <span class="role-line">{{ subject }} · 班级综合排名 {{ rankLabel }}</span>
        </div>
      </div>
      <div class="overall-score" :class="scoreLevel">
        <div class="score-ring">
          <span class="score-val">{{ student.score }}</span>
          <span class="score-unit">分</span>
        </div>
        <span class="score-label">{{ scoreLabel }}</span>
      </div>
    </div>

    <!-- AI 个性化建议条 -->
    <div class="ai-advice">
      <span class="advice-icon">💡</span>
      <div class="advice-text">
        <strong>个性化学情诊断：</strong>{{ aiAdvice }}
      </div>
    </div>

    <!-- 三栏统计 -->
    <div class="stat-row">
      <div class="stat-pill">
        <small>累计作答</small>
        <strong>{{ student.total }} 题</strong>
      </div>
      <div class="stat-pill ok">
        <small>稳妥做对</small>
        <strong>{{ student.correct }} 题</strong>
      </div>
      <div class="stat-pill bad">
        <small>薄弱失分</small>
        <strong>{{ student.wrong }} 题</strong>
      </div>
    </div>

    <!-- 知识点强弱条（普通学科才有） -->
    <div v-if="kpStats.length > 0" class="kp-section">
      <div class="section-title">📚 知识点掌握度</div>
      <div class="kp-list">
        <div v-for="kp in kpStats" :key="kp.name" class="kp-row">
          <div class="kp-name" :title="kp.name">{{ kp.name }}</div>
          <div class="kp-bar">
            <div class="kp-fill" :style="{ width: kp.rate + '%', backgroundColor: getBarColor(kp.rate) }"></div>
          </div>
          <div class="kp-pct" :style="{ color: getBarColor(kp.rate) }">{{ kp.rate }}%</div>
          <div class="kp-meta">{{ kp.correct }}/{{ kp.total }}</div>
        </div>
      </div>
    </div>

    <!-- 错因词云 -->
    <div v-if="errorTags.length > 0" class="cloud-section">
      <div class="section-title">🏷️ 高频错因词云</div>
      <div class="cloud-box">
        <span
          v-for="tag in errorTags" :key="tag.text"
          class="cloud-tag"
          :style="{
            fontSize: tag.size + 'px',
            color: tag.color,
            backgroundColor: tag.bg,
            borderColor: tag.color,
          }"
        >{{ tag.text }} · {{ tag.count }}</span>
      </div>
    </div>

    <!-- 优劣势总结 -->
    <div class="strength-grid">
      <div class="s-card pros">
        <div class="s-head">✨ 优势</div>
        <p>{{ prosText }}</p>
      </div>
      <div class="s-card cons">
        <div class="s-head">🚨 薄弱</div>
        <p>{{ consText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  student: { type: Object, required: true },
  subject: { type: String, default: '通用学科' },
  rank: { type: Number, default: 0 },
  totalStudents: { type: Number, default: 0 },
});

const cleanName = computed(() => String(props.student.name || '未知').replace('-UI评测', ''));
const rankLabel = computed(() => props.rank && props.totalStudents
  ? `第 ${props.rank} / ${props.totalStudents} 名`
  : '—');

const scoreLevel = computed(() => {
  const s = props.student.score;
  if (s >= 90) return 'excellent';
  if (s >= 80) return 'good';
  if (s >= 60) return 'pass';
  return 'poor';
});

const scoreLabel = computed(() => ({
  excellent: '优秀', good: '良好', pass: '及格', poor: '待优化'
}[scoreLevel.value]));

// 知识点掌握度：从该学生的 records 派生
const kpStats = computed(() => {
  const map = {};
  (props.student.records || []).forEach(r => {
    const kp = String(r.knowledge_point || '').trim();
    if (!kp || kp === '-' || kp === '未归类') return;
    if (!map[kp]) map[kp] = { name: kp, total: 0, correct: 0 };
    map[kp].total++;
    if (checkPass(r.is_correct)) map[kp].correct++;
  });
  return Object.values(map)
    .map(k => ({ ...k, rate: k.total > 0 ? Math.round((k.correct / k.total) * 100) : 0 }))
    .sort((a, b) => a.rate - b.rate)  // 薄弱优先
    .slice(0, 8);
});

const checkPass = (status) => {
  const s = String(status || '').trim();
  return s === '正确' || s.includes('部分正确') || s.includes('基本正确') || s.includes('合格') || s === 'true';
};

// 高频错因聚合
const errorTags = computed(() => {
  const counts = {};
  (props.student.wrongRecords || []).forEach(r => {
    let cause = String(r.error_cause || '')
      .replace(/`{3}[\s\S]*?`{3}/g, '')
      .replace(/[#*]/g, '')
      .trim();
    if (!cause || cause === '无') return;
    if (cause.length > 14) cause = cause.slice(0, 14) + '…';
    counts[cause] = (counts[cause] || 0) + 1;
  });
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 12);
  if (entries.length === 0) return [];
  const max = entries[0][1];
  const palette = [
    { color: '#dc2626', bg: '#fef2f2' },
    { color: '#b45309', bg: '#fffbeb' },
    { color: '#7c3aed', bg: '#f5f3ff' },
    { color: '#0891b2', bg: '#ecfeff' },
    { color: '#15803d', bg: '#f0fdf4' },
  ];
  return entries.map(([text, count], i) => {
    const ratio = count / max;
    return {
      text, count,
      size: Math.round(12 + ratio * 12),
      ...palette[i % palette.length],
    };
  });
});

// 优劣势汇总
const prosText = computed(() => {
  const tops = kpStats.value.filter(k => k.rate >= 80).slice(-3).map(k => k.name);
  if (props.student.score >= 90 && tops.length === 0) return '整体表现优秀，作答稳定，思路严谨';
  if (tops.length === 0) return '暂未识别到明显优势项，建议夯实基础';
  return `${tops.join(' / ')} 等知识点掌握扎实，正确率均 ≥ 80%`;
});

const consText = computed(() => {
  const weak = kpStats.value.filter(k => k.rate < 60).slice(0, 3).map(k => k.name);
  if (weak.length === 0 && props.student.wrong === 0) return '🎉 当前无明显薄弱项';
  if (weak.length === 0) return `仍有 ${props.student.wrong} 题失分，建议针对错题进行查漏补缺`;
  return `${weak.join(' / ')} 正确率偏低，需要专项练习`;
});

// AI 个性化建议（基于分数 + 错题模式启发式生成；不调用接口，离线可用）
const aiAdvice = computed(() => {
  const s = props.student.score;
  const wrongRate = props.student.total > 0 ? props.student.wrong / props.student.total : 0;
  const hasWeakKp = kpStats.value.some(k => k.rate < 60);

  if (s >= 90) {
    return '综合表现优秀。建议保持当前学习节奏，可尝试综合性更强的拓展题型，进一步打磨思维深度。';
  }
  if (s >= 80) {
    return hasWeakKp
      ? '整体良好，但仍存在少量薄弱知识点。建议针对薄弱项做 5~10 道变式训练，巩固迁移能力。'
      : '良好水平稳定。建议提速练习并加强综合应用题训练。';
  }
  if (s >= 60) {
    return `已达及格线，错题率约 ${Math.round(wrongRate * 100)}%。建议从最薄弱的知识点入手，每天专项练习 20 分钟，2 周内可见明显提升。`;
  }
  return `当前学情预警。错题率达 ${Math.round(wrongRate * 100)}%，存在明显的知识断层。建议优先回归基础概念，由老师 1 对 1 答疑后再做巩固训练。`;
});

const getBarColor = (rate) => {
  if (rate >= 85) return '#10b981';
  if (rate >= 70) return '#3b82f6';
  if (rate >= 50) return '#f59e0b';
  return '#ef4444';
};

defineExpose({ aiAdvice, kpStats, errorTags });
</script>

<style scoped>
.profile-card {
  display: flex; flex-direction: column; gap: 18px;
  padding: 22px;
  background: #fff;
  border-radius: 18px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

/* 头部 */
.profile-head {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 16px; border-bottom: 1px dashed #e2e8f0;
  gap: 16px; flex-wrap: wrap;
}
.avatar-block { display: flex; align-items: center; gap: 14px; }
.avatar-big {
  width: 56px; height: 56px;
  display: grid; place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
  font-size: 28px;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.12);
}
.avatar-text h3 { margin: 0; font-size: 19px; color: #0f172a; font-weight: 900; }
.role-line { font-size: 12px; color: #64748b; margin-top: 4px; display: block; font-weight: 700; letter-spacing: 0.3px; }

.overall-score { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.score-ring {
  width: 76px; height: 76px;
  border-radius: 50%; border: 4px solid #e2e8f0;
  display: flex; align-items: baseline; justify-content: center;
  background: #f8fafc;
}
.score-val { font-size: 26px; font-weight: 900; line-height: 1; }
.score-unit { font-size: 11px; font-weight: 700; opacity: 0.7; margin-left: 2px; }
.score-label { font-size: 12px; font-weight: 800; }
.overall-score.excellent .score-ring { border-color: #34d399; background: #ecfdf5; }
.overall-score.excellent .score-val, .overall-score.excellent .score-label { color: #059669; }
.overall-score.good .score-ring { border-color: #60a5fa; background: #eff6ff; }
.overall-score.good .score-val, .overall-score.good .score-label { color: #2563eb; }
.overall-score.pass .score-ring { border-color: #fbbf24; background: #fffbeb; }
.overall-score.pass .score-val, .overall-score.pass .score-label { color: #d97706; }
.overall-score.poor .score-ring { border-color: #f87171; background: #fef2f2; }
.overall-score.poor .score-val, .overall-score.poor .score-label { color: #dc2626; }

/* AI 建议条 */
.ai-advice {
  display: flex; gap: 12px;
  padding: 14px 16px; border-radius: 12px;
  background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
  border: 1px solid #fcd34d;
}
.advice-icon { font-size: 20px; flex-shrink: 0; }
.advice-text { font-size: 13px; color: #78350f; line-height: 1.7; }
.advice-text strong { color: #92400e; }

/* 统计三栏 */
.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.stat-pill {
  display: flex; flex-direction: column; gap: 4px;
  padding: 14px; border-radius: 12px;
  background: #f8fafc; border: 1px solid #e2e8f0;
}
.stat-pill small { font-size: 11px; color: #64748b; font-weight: 700; }
.stat-pill strong { font-size: 18px; color: #0f172a; font-weight: 900; }
.stat-pill.ok { background: #f0fdf4; border-color: #bbf7d0; }
.stat-pill.ok strong { color: #047857; }
.stat-pill.bad { background: #fef2f2; border-color: #fecaca; }
.stat-pill.bad strong { color: #dc2626; }

/* 知识点强弱条 */
.section-title { font-size: 14px; font-weight: 800; color: #1e293b; margin-bottom: 12px; }
.kp-list { display: flex; flex-direction: column; gap: 8px; }
.kp-row {
  display: grid;
  grid-template-columns: 110px 1fr 50px 60px;
  gap: 10px; align-items: center;
  font-size: 12px;
}
.kp-name {
  color: #334155; font-weight: 700;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.kp-bar {
  height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden;
}
.kp-fill { height: 100%; transition: width 0.4s; border-radius: 4px; }
.kp-pct { font-weight: 900; text-align: right; }
.kp-meta { font-size: 11px; color: #94a3b8; font-weight: 600; }

/* 错因词云 */
.cloud-box {
  display: flex; flex-wrap: wrap; gap: 8px;
  padding: 14px; border-radius: 12px;
  background: #f8fafc; border: 1px dashed #cbd5e1;
  min-height: 60px; align-items: center;
}
.cloud-tag {
  display: inline-flex; align-items: center;
  padding: 4px 10px; border-radius: 999px;
  border: 1px solid; font-weight: 700;
  transition: 0.2s;
}
.cloud-tag:hover { transform: translateY(-2px) scale(1.05); }

/* 优劣势 */
.strength-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.s-card { padding: 14px; border-radius: 12px; }
.s-card.pros { background: #f0fdf4; border: 1px solid #bbf7d0; }
.s-card.cons { background: #fef2f2; border: 1px solid #fecaca; }
.s-head { font-size: 13px; font-weight: 800; margin-bottom: 6px; }
.s-card.pros .s-head { color: #15803d; }
.s-card.cons .s-head { color: #b91c1c; }
.s-card p { margin: 0; font-size: 13px; line-height: 1.65; }
.s-card.pros p { color: #14532d; }
.s-card.cons p { color: #7f1d1d; }

@media (max-width: 720px) {
  .stat-row, .strength-grid { grid-template-columns: 1fr; }
  .kp-row { grid-template-columns: 80px 1fr 40px 50px; }
}

/* 🌟 打印样式：通过 window.print 触发"另存为 PDF" */
@media print {
  .profile-card {
    box-shadow: none !important;
    border: 1px solid #cbd5e1 !important;
  }
}
</style>
