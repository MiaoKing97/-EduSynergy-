<template>
  <div class="w-full mt-6 bg-white rounded-xl border border-slate-200 shadow-sm p-4 relative">
    <div class="text-xs text-slate-400 font-bold mb-2 uppercase tracking-widest border-b pb-2 flex justify-between">
      <span>🧩 结构导图视图</span><span class="text-blue-500 bg-blue-50 px-2 py-0.5 rounded cursor-help">🖱️ 滚轮缩放 / 左键拖拽</span>
    </div>
    <div class="mermaid transition-all overflow-hidden h-[400px]" ref="mermaidRef"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import mermaid from 'mermaid';
import svgPanZoom from 'svg-pan-zoom';

const props = defineProps({ code: String });
const mermaidRef = ref(null);

const renderMermaid = async () => {
  if (!mermaidRef.value || !props.code) return;
  try {
    mermaidRef.value.removeAttribute('data-processed');
    mermaidRef.value.innerHTML = props.code;
    await mermaid.run({ nodes: [mermaidRef.value] });
    setTimeout(() => {
      const svg = mermaidRef.value?.querySelector('svg');
      if (svg && !svg.getAttribute('data-zoom-applied')) {
        svg.setAttribute('data-zoom-applied', 'true');
        svg.style.maxWidth = 'none'; svg.style.width = '100%'; svg.style.height = '100%';
        svgPanZoom(svg, { zoomEnabled: true, controlIconsEnabled: true, fit: true, center: true, minZoom: 0.5, maxZoom: 10 });
      }
    }, 200);
  } catch (e) { console.error("Mermaid Render Error:", e); }
};

onMounted(() => {
  mermaid.initialize({ startOnLoad: false, theme: 'neutral' });
  renderMermaid();
});
watch(() => props.code, renderMermaid);
</script>