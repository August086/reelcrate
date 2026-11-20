<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  AlertCircle,
  Download,
  Image as ImageIcon,
  ListTree,
  LoaderCircle,
  Maximize2,
  Minimize2,
} from '@lucide/vue'
import { exportMindmapPng, exportMindmapSvg, safeExportName } from '../lib/export'
import { useToast } from '../composables/useToast'

const props = defineProps({
  markdown: { type: String, default: '' },
  title: { type: String, default: '' },
  running: { type: Boolean, default: false },
  error: { type: Object, default: null },
})
const toast = useToast()

const containerEl = ref(null)
const hostEl = ref(null)
const svgEl = ref(null)
const loading = ref(false)
const failed = ref(false)
const fullscreen = ref(false)
const exporting = ref('')

let markmap = null
let transformer = null
let resizeObserver = null

async function ensureLibs() {
  if (transformer && markmap) return true
  const [lib, view] = await Promise.all([import('markmap-lib'), import('markmap-view')])
  transformer = new lib.Transformer()
  const Markmap = view.Markmap
  if (!markmap && svgEl.value) {
    markmap = Markmap.create(
      svgEl.value,
      {
        autoFit: true,
        duration: 280,
        maxWidth: 220,
        colorFreezeLevel: 2,
        paddingX: 18,
        spacingVertical: 8,
        spacingHorizontal: 90,
      },
      undefined,
    )
  }
  return Boolean(markmap)
}

async function render() {
  if (!props.markdown || !svgEl.value) return
  loading.value = true
  failed.value = false
  try {
    await ensureLibs()
    if (!markmap) return
    const { root } = transformer.transform(props.markdown)
    await markmap.setData(root)
    await nextTick()
    markmap.fit()
    // Long Chinese labels can expand after the first layout pass.
    setTimeout(fit, 350)
    setTimeout(fit, 1000)
  } catch (exc) {
    failed.value = true
    console.error('markmap render failed', exc)
  } finally {
    loading.value = false
  }
}

function fit() {
  try {
    markmap?.fit()
  } catch {
    // ignore transient layout errors
  }
}

function onFullscreenChange() {
  fullscreen.value = Boolean(document.fullscreenElement)
  setTimeout(fit, 240)
}

async function toggleFullscreen() {
  try {
    if (!document.fullscreenElement) {
      await containerEl.value?.requestFullscreen()
    } else {
      await document.exitFullscreen()
    }
  } catch {
    toast.info('当前浏览器不支持全屏，已为你保留大画布。')
  }
}

async function exportPng() {
  if (!props.markdown || exporting.value) return
  exporting.value = 'png'
  try {
    await exportMindmapPng(hostEl.value, safeExportName(props.title, 'png'))
    toast.success('高清 PNG 已开始下载')
  } catch (exc) {
    console.error(exc)
    toast.error('PNG 导出失败，可以改用 SVG 矢量图。')
  } finally {
    exporting.value = ''
  }
}

async function exportSvg() {
  if (!props.markdown || exporting.value) return
  exporting.value = 'svg'
  try {
    exportMindmapSvg(svgEl.value, safeExportName(props.title, 'svg'))
    toast.success('SVG 矢量图已开始下载')
  } catch (exc) {
    console.error(exc)
    toast.error('SVG 导出失败，请稍后重试。')
  } finally {
    exporting.value = ''
  }
}

function onResize() {
  window.clearTimeout(onResize.timer)
  onResize.timer = window.setTimeout(fit, 160)
}

watch(
  () => props.markdown,
  async () => {
    await nextTick()
    render()
  },
)

onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  resizeObserver = new ResizeObserver(onResize)
  if (hostEl.value) resizeObserver.observe(hostEl.value)
  if (props.markdown) render()
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  resizeObserver?.disconnect()
  markmap?.destroy?.()
  markmap = null
})
</script>

<template>
  <div>
    <div
      v-if="markdown"
      ref="containerEl"
      class="mindmap-shell relative overflow-hidden rounded-2xl border border-line bg-white"
      :class="fullscreen ? 'flex h-screen flex-col rounded-none border-0' : ''"
    >
      <div class="flex shrink-0 items-center justify-between gap-2 border-b border-line bg-white px-3 py-2">
        <div class="flex items-center gap-2">
          <ListTree :size="14" class="text-cobalt-500" />
          <span class="text-[10px] font-bold text-slate-600">内容导图</span>
        </div>
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="flex h-7 w-7 items-center justify-center rounded-full text-slate-500 transition hover:bg-cobalt-50 hover:text-cobalt-600"
            :aria-label="fullscreen ? '退出全屏' : '全屏查看'"
            @click="toggleFullscreen"
          >
            <Minimize2 v-if="fullscreen" :size="14" />
            <Maximize2 v-else :size="14" />
          </button>
          <button
            type="button"
            class="flex h-7 items-center gap-1 rounded-full px-2 text-[10px] font-semibold text-slate-500 transition hover:bg-cobalt-50 hover:text-cobalt-600 disabled:opacity-50"
            :disabled="Boolean(exporting)"
            aria-label="下载 PNG"
            @click="exportPng"
          >
            <LoaderCircle v-if="exporting === 'png'" class="animate-spin" :size="12" />
            <ImageIcon v-else :size="12" />
            PNG
          </button>
          <button
            type="button"
            class="flex h-7 items-center gap-1 rounded-full px-2 text-[10px] font-semibold text-slate-500 transition hover:bg-cobalt-50 hover:text-cobalt-600 disabled:opacity-50"
            :disabled="Boolean(exporting)"
            aria-label="下载 SVG"
            @click="exportSvg"
          >
            <LoaderCircle v-if="exporting === 'svg'" class="animate-spin" :size="12" />
            <Download v-else :size="12" />
            SVG
          </button>
        </div>
      </div>

      <div class="relative flex-1" :class="fullscreen ? 'min-h-0' : 'h-[500px]'">
        <div ref="hostEl" class="markmap-host absolute inset-0">
          <svg ref="svgEl" class="h-full w-full" aria-label="视频内容思维导图" />
        </div>

        <div
          v-if="loading"
          class="absolute inset-0 z-[5] flex items-center justify-center bg-white/80 backdrop-blur-sm"
        >
          <div class="flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2 text-[11px] font-semibold text-cobalt-600 shadow-sm">
            <LoaderCircle class="animate-spin" :size="14" />
            正在绘制导图…
          </div>
        </div>

        <div
          v-if="failed"
          class="absolute inset-0 z-[6] flex flex-col items-center justify-center bg-white px-6 text-center"
        >
          <span class="flex h-11 w-11 items-center justify-center rounded-2xl bg-rose-50 text-rose-500">
            <AlertCircle :size="20" />
          </span>
          <p class="mt-3 text-sm font-bold text-ink">导图渲染失败</p>
          <p class="mt-1 max-w-xs text-[11px] leading-5 text-slate-400">可以切换 Tab 后重试，或使用左侧「重新总结」重新生成。</p>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-line px-3 py-2 text-[9px] text-slate-400">
        <span>滚轮缩放 · 拖拽平移 · 双击节点折叠</span>
        <span class="font-semibold text-slate-500">ReelCrate AI 导图</span>
      </div>
    </div>

    <div v-else-if="running" class="rounded-2xl border border-line bg-white p-5">
      <div class="flex items-center gap-2 text-[11px] font-semibold text-cobalt-600">
        <LoaderCircle class="animate-spin" :size="14" />
        正在把总结折叠成一张图…
      </div>
      <div class="relative mt-5 h-56 overflow-hidden rounded-xl bg-paper">
        <svg viewBox="0 0 520 220" class="h-full w-full" aria-hidden="true">
          <path d="M72 110h75M147 110h80M227 110h80M307 110h80" stroke="#C9D8F0" stroke-width="1.5" stroke-dasharray="4 5" />
          <path d="M147 110v-54M147 110v54M307 110v-54M307 110v54" stroke="#C9D8F0" stroke-width="1.5" stroke-dasharray="4 5" />
          <circle cx="72" cy="110" r="18" fill="#1777FF" fill-opacity=".16" />
          <circle cx="147" cy="56" r="11" fill="#1777FF" fill-opacity=".12" />
          <circle cx="147" cy="164" r="11" fill="#1777FF" fill-opacity=".12" />
          <circle cx="227" cy="110" r="13" fill="#F5B84B" fill-opacity=".2" />
          <circle cx="307" cy="56" r="9" fill="#1777FF" fill-opacity=".12" />
          <circle cx="307" cy="164" r="9" fill="#1777FF" fill-opacity=".12" />
          <circle cx="307" cy="110" r="16" fill="#1777FF" fill-opacity=".14" />
          <rect x="360" y="80" width="90" height="10" rx="5" fill="#E6ECF5" />
          <rect x="360" y="100" width="70" height="10" rx="5" fill="#E6ECF5" />
          <rect x="360" y="120" width="104" height="10" rx="5" fill="#E6ECF5" />
        </svg>
        <div class="absolute inset-0 animate-pulse bg-gradient-to-r from-transparent via-white/40 to-transparent" />
      </div>
      <p class="mt-3 text-[10px] text-slate-400">总结完成后自动生成，不需要重复请求。</p>
    </div>

    <div v-else class="rounded-2xl border border-dashed border-line bg-paper/60 px-5 py-10 text-center">
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
        <ListTree :size="22" />
      </span>
      <p class="mt-3 text-sm font-bold text-ink">导图还没有生成</p>
      <p class="mt-1 text-[11px] text-slate-400">
        {{ error?.message || '先让 AI 读完字幕，这里就会出现可交互的结构图。' }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.mindmap-shell:fullscreen {
  background: #fff;
}
</style>
