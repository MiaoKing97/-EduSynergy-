<template>
  <div class="report-box">
    <div class="section-box">
      <div class="section-title">❌ 专属弱项错题本 (共 {{ student.wrong }} 题)</div>
      <div v-if="student.wrongRecords.length === 0" class="no-wrong-tips">
        🎉 太棒了！该学生在当前表格的所有诊断题目中全部回答正确！
      </div>
      <div v-else class="wrong-book-list">
        <div v-for="(record, index) in student.wrongRecords" :key="index" class="wrong-item-card">
          <div class="wrong-item-top">
            <span class="wrong-q-num">题号: {{ record.question_number || '未知' }}</span>
            <span class="wrong-kp-tag">💡 考点: {{ record.knowledge_point }}</span>
          </div>
          <div class="wrong-q-content"><strong>题目：</strong>{{ record.question }}</div>
          <div class="wrong-answers">
            <span>✍️ 作答：<code class="bad-ans">{{ record.student_answer }}</code></span>
          </div>
          <div class="wrong-analysis">
            <strong>🚨 智能诊断：</strong>
            <p class="cause-p">{{ record.error_cause }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ student: Object });
</script>

<style scoped>
.report-box { margin-top: 20px; }
.section-title { font-size: 16px; font-weight: 800; color: #1e293b; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.no-wrong-tips { padding: 30px; text-align: center; background: #f0fdf4; color: #16a34a; border-radius: 8px; font-weight: bold; }
.wrong-item-card { background: #fff; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(239, 68, 68, 0.05); }
.wrong-item-top { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13px; font-weight: 700; border-bottom: 1px dashed #fca5a5; padding-bottom: 8px; }
.wrong-q-num { color: #dc2626; }
.wrong-kp-tag { color: #4a5568; }
.wrong-q-content { font-size: 14px; color: #1e293b; margin-bottom: 12px; }
.wrong-answers { font-size: 13px; color: #475569; margin-bottom: 12px; background: #f8fafc; padding: 8px; border-radius: 6px; }
.bad-ans { color: #dc2626; font-weight: bold; background: #fef2f2; padding: 2px 6px; border-radius: 4px; }
.wrong-analysis { background: #fffbeb; padding: 12px; border-radius: 6px; border-left: 4px solid #f59e0b; }
.wrong-analysis strong { color: #b45309; display: block; margin-bottom: 4px; font-size: 13px; }
.cause-p { margin: 0; font-size: 13px; color: #78350f; line-height: 1.5; }
</style>