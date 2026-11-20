<script setup>
import { computed, ref } from 'vue'
import { Captions, ChevronDown, ChevronUp, Copy, Download, LoaderCircle, TriangleAlert } from '@lucide/vue'
import AsrFallbackCard from './AsrFallbackCard.vue'
import { formatClock } from '../lib/format'
import { exportSubtitles, toTxt } from '../lib/subtitle'
import { useToast } from '../composables/useToast'

const props = defineProps({
  video: { type: Object, required: true },
  summary: { type: Object, required: true },
  asr: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['transcribe', 'retry'])
const toast = useToast()
const expanded = ref(false)

const segments = computed(() => props.summary.segments || [])
const running = computed(() => props.summary.status === 'running')
const visible = computed(() => (expanded.value ? segments.value : segments.value.slice(0, 12)))
const canExpand = computed(() => segments.value.length > 12)
const asrInfo = computed(() => props.summary.asrInfo || null)
const asrRunning = computed(() => running.value && props.summary.asrStage === 'asr')
const noSubtitles = computed(
  () => props.summary.error?.code === 'no_subtitles' && !segments.value.length,
)

function download(format) {
  if (!segments.value.length) return
  exportSubtitles(segments.value, format, props.video.title)
  toast.success(`${format.toUpperCase()} 字幕已开始下载`)
}

async function copyLine(segment) {
  const text = `[${formatClock(segment.start)}] ${segment.text}`
  try {
    await navigator.clipboard.writeText(text)
    toast.success('这一句已复制')
  } catch {
    toast.info('浏览器未授予剪贴板权限')
  }
}

async function copyAll() {
  if (!segments.value.length) return
  const text = toTxt(segments.value, true)
  try {
    await navigator.clipboard.writeText(text)
    toast.success('字幕文本已复制')
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    textarea.remove()
    toast.success('字幕文本已复制')
  }
}
</script>

<template>
  <div>
    <div v-if="segments.length">
      <div v-if="summary.asr" class="mb-3 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 px-3 py-2 text-[10px] leading-4 text-amber-800">
        <TriangleAlert class="mt-0.5 shrink-0" :size="12" />
        <span>本字幕由本地 Whisper 转写，可能有错字、漏字；建议对照原视频。可正常导出 SRT / VTT / TXT。</span>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span class="inline-flex items-center gap-1.5 rounded-full bg-cobalt-50 px-2.5 py-1 text-[10px] font-bold text-cobalt-700">
          <Captions :size="12" />
          {{ summary.languageName || summary.language }}
        </span>
        <span class="rounded-full bg-paper px-2.5 py-1 text-[10px] font-semibold text-slate-500">
          {{ summary.source }}
        </span>
        <span class="text-[10px] text-slate-400">{{ segments.length }} 条</span>
        <span v-if="summary.truncated" class="text-[10px] text-amber-600">AI 只读取首尾部分</span>
        <div class="ml-auto flex items-center gap-1">
          <button type="button" class="btn-ghost !px-2 !py-1.5 text-[10px]" @click="copyAll">
            <Copy :size="12" />
            复制
          </button>
          <span class="mx-1 h-3 w-px bg-line" />
          <button
            v-for="format in ['srt', 'vtt', 'txt']"
            :key="format"
            type="button"
            class="rounded-lg border border-line bg-white px-2 py-1.5 text-[9px] font-bold uppercase tracking-wide text-slate-500 transition hover:border-cobalt-200 hover:text-cobalt-600"
            :aria-label="`导出 ${format.toUpperCase()} 字幕`"
            @click="download(format)"
          >
            {{ format }}
          </button>
        </div>
      </div>

      <div class="mt-4 overflow-hidden rounded-2xl border border-line">
        <div
          v-for="(segment, index) in visible"
          :key="`${segment.start}-${index}`"
          class="flex gap-3 border-b border-line/70 px-3 py-2.5 text-[12px] leading-5 transition last:border-b-0 hover:bg-paper/70 sm:px-4"
        >
          <button
            type="button"
            class="mt-0.5 h-5 shrink-0 rounded bg-cobalt-50 px-1.5 font-mono text-[9px] font-semibold text-cobalt-600"
            :title="`复制这一句（${formatClock(segment.start)}）`"
            @click="copyLine(segment)"
          >
            {{ formatClock(segment.start) }}
          </button>
          <p class="min-w-0 flex-1 text-slate-600">{{ segment.text }}</p>
        </div>
      </div>

      <div class="mt-3 flex items-center justify-between">
        <button
          v-if="canExpand"
          type="button"
          class="btn-ghost text-[11px]"
          @click="expanded = !expanded"
        >
          <ChevronUp v-if="expanded" :size="14" />
          <ChevronDown v-else :size="14" />
          {{ expanded ? '收起字幕' : `展开全部 ${segments.length} 条` }}
        </button>
        <span v-else class="text-[10px] text-slate-400">已显示全部字幕</span>
        <span class="inline-flex items-center gap-1 text-[10px] text-slate-400">
          <Download :size="11" />
          可导出 SRT / VTT / TXT
        </span>
      </div>
    </div>

    <div v-else-if="running" class="space-y-3 rounded-2xl border border-line bg-white p-4">
      <div class="flex items-center gap-2 text-[11px] font-semibold text-cobalt-600">
        <LoaderCircle v-if="!asrRunning" class="animate-spin" :size="14" />
        <span v-else class="h-1.5 w-1.5 animate-pulse rounded-full bg-cobalt-500" />
        {{ summary.message || (asrRunning ? '正在本地听写…' : '正在提取字幕…') }}
        <span v-if="asrRunning" class="ml-auto font-mono text-[10px] text-slate-400">{{ Math.round(summary.progress || 0) }}%</span>
      </div>
      <div v-if="asrRunning" class="h-2 overflow-hidden rounded-full bg-cobalt-100">
        <div class="h-full rounded-full bg-cobalt-500 transition-all duration-500" :style="{ width: `${Math.max(2, summary.progress || 0)}%` }" />
      </div>
      <template v-if="!asrRunning">
        <div v-for="index in 6" :key="index" class="flex gap-3">
          <div class="skeleton h-5 w-10 shrink-0" />
          <div class="skeleton h-4 flex-1" :style="{ width: `${96 - index * 7}%` }" />
        </div>
      </template>
      <p v-if="asrRunning" class="text-[10px] leading-4 text-slate-400">
        平台没有字幕，正在用本地 Whisper 生成可导出的时间轴字幕。首次使用会下载模型。
      </p>
    </div>

    <template v-else-if="noSubtitles">
      <AsrFallbackCard
        v-if="asrInfo?.asr_available"
        :info="asrInfo"
        :asr="asr"
        @transcribe="emit('transcribe')"
        @retry="emit('retry')"
      />
      <div v-else class="rounded-2xl border border-dashed border-line bg-paper/60 px-5 py-9 text-center">
        <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
          <Captions :size="22" />
        </span>
        <p class="mt-3 text-sm font-bold text-ink">没有抓到字幕</p>
        <p class="mx-auto mt-1.5 max-w-md text-[11px] leading-5 text-slate-400">
          {{ summary.error?.message }}
          字幕依赖平台提供：TED / YouTube 通常有，B 站 CC 需要登录 Cookie。
        </p>
      </div>
    </template>

    <div v-else class="rounded-2xl border border-dashed border-line bg-paper/60 px-5 py-9 text-center">
      <span class="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
        <TriangleAlert :size="19" />
      </span>
      <p class="mt-3 text-sm font-bold text-ink">字幕还没有准备好</p>
      <p class="mt-1 text-[11px] text-slate-400">{{ summary.error?.message || '解析完成后会自动尝试提取。' }}</p>
      <button
        v-if="asrInfo?.asr_available && asr?.enabled !== false"
        type="button"
        class="btn-secondary mt-4 !px-4 !py-2 text-[11px]"
        @click="emit('transcribe')"
      >
        <LoaderCircle :size="12" />
        重试语音转写
      </button>
    </div>
  </div>
</template>
