<script setup>
import { computed } from 'vue'
import { AudioLines, Download, RefreshCw, ShieldCheck, Sparkles, TriangleAlert } from '@lucide/vue'

const props = defineProps({
  info: { type: Object, default: () => ({}) },
  asr: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['transcribe', 'retry'])

const modelReady = computed(() => Boolean(props.info.asr_ready || props.asr.ready))
const modelSize = computed(() => props.info.asr_model_size_mb || props.asr.model_size_mb || 486)
const autoDownload = computed(() => props.info.asr_auto_download !== false)
const canStart = computed(() => props.info.asr_available !== false && (modelReady.value || autoDownload.value))
const estimate = computed(() => {
  const seconds = Number(props.info.asr_estimated_seconds || 0)
  if (!seconds) return '预计几分钟'
  if (seconds < 90) return '预计约 1-2 分钟'
  return `预计约 ${Math.ceil(seconds / 60)} 分钟`
})
const buttonLabel = computed(() => {
  if (!canStart.value) return '需先准备语音模型'
  if (!modelReady.value) return `下载模型并开始（${modelSize.value}MB）`
  return '开始语音转写'
})
</script>

<template>
  <div class="relative overflow-hidden rounded-2xl border border-cobalt-200/80 bg-[linear-gradient(135deg,#F2F7FF,#FFFFFF_58%,#FFFBF2)] p-4 sm:p-5">
    <div class="pointer-events-none absolute -right-8 -top-10 h-36 w-36 rounded-full bg-cobalt-200/30 blur-2xl" />
    <div class="relative flex items-start gap-3">
      <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cobalt-500 text-white shadow-[0_12px_26px_-12px_rgba(23,119,255,.8)]">
        <AudioLines :size="20" />
      </span>
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-2">
          <p class="text-[14px] font-black text-ink">平台没有字幕，让 AI 听一遍</p>
          <span class="rounded-full bg-white/80 px-2 py-0.5 text-[9px] font-bold text-cobalt-600 ring-1 ring-cobalt-100">
            LOCAL WHISPER
          </span>
        </div>
        <p class="mt-1 text-[11px] leading-5 text-slate-500">
          本地 Whisper 会把音频转成带时间戳的字幕，再交给 DeepSeek 总结、做导图和问答。
          音频不上传第三方。
        </p>
      </div>
    </div>

    <div class="relative mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-xl bg-white/75 px-3 py-2.5 text-[10px] font-medium text-slate-500 ring-1 ring-white">
      <span class="inline-flex items-center gap-1.5"><Sparkles :size="12" class="text-cobalt-500" /> {{ estimate }}</span>
      <span class="h-1 w-1 rounded-full bg-slate-300" />
      <span class="inline-flex items-center gap-1.5"><ShieldCheck :size="12" class="text-emerald-500" /> 本地处理</span>
      <span v-if="!modelReady" class="inline-flex items-center gap-1.5 text-amber-700">
        <Download :size="12" /> 首次需下载 {{ modelSize }}MB 模型
      </span>
    </div>

    <div class="relative mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
      <button type="button" class="btn-primary !rounded-xl !px-4 !py-2.5 text-[12px]" :disabled="!canStart" @click="emit('transcribe')">
        <Download v-if="!modelReady" :size="14" />
        <Sparkles v-else :size="14" />
        {{ buttonLabel }}
      </button>
      <button type="button" class="btn-ghost !px-3 !py-2 text-[10px] text-slate-500" @click="emit('retry')">
        <RefreshCw :size="12" />
        重新提取平台字幕
      </button>
    </div>

    <p class="relative mt-2 flex items-start gap-1.5 text-[9px] leading-4 text-slate-400">
      <TriangleAlert class="mt-0.5 shrink-0 text-amber-500" :size="11" />
      <span v-if="!modelReady && !autoDownload">
        自动下载已关闭，请先运行 <code class="rounded bg-white px-1 font-mono text-[8px]">backend/download_asr.py</code>。
      </span>
      <span v-else>
        机器听写可能有错字、漏字，建议对照原视频；<span v-if="!modelReady">首次转写会自动下载模型。</span>
      </span>
    </p>
  </div>
</template>
