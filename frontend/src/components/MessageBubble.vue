<template>
  <div class="flex w-full flex-col">
    <div v-if="role === 'user'" class="flex justify-end items-start gap-3 w-full">
      <div class="max-w-[85%] flex flex-col items-end gap-1">
        <div class="bg-blue-600 text-white px-5 py-3.5 rounded-2xl rounded-tr-none shadow-md">
          <div v-if="images && images.length > 0" class="flex flex-wrap gap-2 mb-3">
            <img v-for="(img, idx) in images" :key="idx" :src="img" class="h-28 rounded-lg border border-blue-400 object-cover hover:scale-105 transition-transform" />
          </div>
          <p class="whitespace-pre-wrap text-[15px] leading-relaxed">{{ content }}</p>
        </div>
      </div>
      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white shadow-md shrink-0 border-2 border-white ring-2 ring-blue-50">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
      </div>
    </div>

    <div v-else class="flex flex-col gap-2 w-full">
      <div class="flex items-center gap-2 font-bold text-blue-700">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center text-white shadow-md text-[11px] tracking-wider">AI</div>
        <span>{{ moduleName.replace(/【.*?】/, '') }}助理</span>
      </div>
      <div class="pl-10 text-slate-800 leading-relaxed text-[15px] w-full">
        <div class="bg-white p-5 rounded-2xl rounded-tl-none shadow-sm border border-slate-100">

          <div v-if="content === '' && isGenerating" class="flex items-center gap-2 text-blue-500 italic text-sm mb-2">
            <div class="w-4 h-4 border-2 border-t-transparent border-blue-500 rounded-full animate-spin"></div> 研判数据并生成可视化视图...
          </div>

          <div class="prose max-w-none whitespace-pre-wrap" ref="textRef">
            <span v-html="parsedMarkdown"></span>
            <span v-if="isGenerating" class="inline-block w-1.5 h-4 bg-blue-400 animate-pulse ml-1 align-middle"></span>
          </div>

          <ChartBase v-if="parsedResult.echartsData" :data="parsedResult.echartsData" />
          <MermaidDiagram v-if="parsedResult.mermaidCode" :code="parsedResult.mermaidCode" />
          <ChartWordCloud v-if="parsedResult.wordCloudData" :data="parsedResult.wordCloudData" />
          <ChartGraph v-if="parsedResult.graphData" :data="parsedResult.graphData" />

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import MarkdownIt from 'markdown-it';
import renderMathInElement from 'katex/dist/contrib/auto-render.mjs';
import { parseAIContent } from '../utils/aiDataParser';

// 引入拆分后的独立渲染器组件
import ChartBase from './renderers/ChartBase.vue';
import ChartWordCloud from './renderers/ChartWordCloud.vue';
import MermaidDiagram from './renderers/MermaidDiagram.vue';
import ChartGraph from './renderers/ChartGraph.vue';

const props = defineProps({
  role: String,
  content: String,
  images: Array,
  isGenerating: Boolean,
  moduleName: { type: String, default: 'AI' }
});

const textRef = ref(null);
const md = new MarkdownIt({ html: true, breaks: true });

// 核心数据解析统一经过 util 工具库处理
const parsedResult = computed(() => parseAIContent(props.content));
const parsedMarkdown = computed(() => md.render(parsedResult.value.text));

const renderTextVisuals = async () => {
  await nextTick();
  if (textRef.value) {
    renderMathInElement(textRef.value, {
      delimiters: [
        {left: '$$', right: '$$', display: true}, {left: '$', right: '$', display: false},
        {left: '\\(', right: '\\)', display: false}, {left: '\\[', right: '\\]', display: true}
      ], throwOnError: false
    });
  }
};

watch([() => props.content, () => props.isGenerating], () => {
  if (!props.isGenerating) renderTextVisuals();
});

onMounted(() => {
  if (!props.isGenerating) renderTextVisuals();
});
</script>