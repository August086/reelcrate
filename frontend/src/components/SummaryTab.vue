<script setup>
import { computed } from 'vue'
import { AlertCircle, AudioLines, Captions, Mic, RefreshCw, Sparkles, TriangleAlert } from '@lucide/vue'
import SetupNotice from './SetupNotice.vue'
import AsrFallbackCard from './AsrFallbackCard.vue'
import { renderMarkdown } from '../lib/markdown'

const props = defineProps({
  video: { type: Object, required: true },
  summary: { type: Object, required: true },
  aiEnabled: { type: Boolean, default: false },
  asr: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['retry', 'transcribe'])

const html = computed(() => renderMarkdown(props.summary.text))
const running = computed(() => props.summary.status === 'running')
const error = computed(() => props.summary.error)
const isSetupError = computed(() => error.value?.code === 'ai_not_configured')
const isNoSubtitles = computed(() => error.value?.code === 'no_subtitles')
const hasText = computed(() => Boolean(props.summary.text))
const asrInfo = computed(() => props.summary.asrInfo || null)
const asrRunning = computed(() => running.value && props.summary.asrStage === 'asr')
const canRetryAsr = computed(() => Boolean(asrInfo.value?.asr_available && props.asr?.enabled !== false))
</script>

<template>
  <div class="space-y-4">
    <SetupNotice v-if="isSetupError" />

    <template v-else-if="isNoSubtitles">
      <AsrFallbackCard
        v-if="asrInfo?.asr_available"
        :info="asrInfo"
        :asr="asr"
        @transcribe="emit('transcribe')"
        @retry="emit('retry')"
      />
      <div v-else class="rounded-2xl border border-dashed border-line bg-paper/60 px-5 py-8 text-center">
        <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
          <Captions :size="22" />
        </span>
        <p class="mt-3 text-sm font-bold text-ink">这个视频没有可用字幕</p>
        <p class="mx-auto mt-1.5 max-w-md text-[11px] leading-5 text-slate-400">
          {{ summary.error?.message || '没有字幕就无法生成可靠的 AI 总结。' }}
          可以试试 TED / YouTube 等自带字幕的视频；B 站 CC 字幕通常需要配置登录 Cookie。
        </p>
        <button type="button" class="btn-secondary mt-4 !px-4 !py-2 text-[11px]" @click="emit('retry')">
          <RefreshCw :size="13" />
          重新尝试
        </button>
      </div>
    </template>

    <div
      v-else-if="asrRunning && !hasText"
      class="rounded-2xl border border-cobalt-100 bg-[linear-gradient(135deg,#F3F8FF,#FFFFFF)] p-5"
    >
      <div class="flex items-center gap-2 text-[11px] font-bold text-cobalt-700">
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-cobalt-500 text-white">
          <AudioLines :size="14" />
        </span>
        正在本地听写
        <span class="ml-auto font-mono text-[10px] text-slate-400">{{ Math.round(summary.progress || 0) }}%</span>
      </div>
      <p class="mt-3 text-[12px] font-semibold text-ink">{{ summary.message || '准备音频…' }}</p>
      <div class="mt-3 h-2 overflow-hidden rounded-full bg-cobalt-100">
        <div class="h-full rounded-full bg-cobalt-500 transition-all duration-500" :style="{ width: `${Math.max(2, summary.progress || 0)}%` }" />
      </div>
      <div class="mt-2 flex justify-between text-[9px] text-slate-400">
        <span>下载音频</span><span>准备模型</span><span>Whisper 听写</span><span>生成字幕</span>
      </div>
      <p class="mt-4 flex items-start gap-1.5 rounded-xl bg-white/70 px-3 py-2 text-[10px] leading-4 text-slate-400 ring-1 ring-white">
        <Mic class="mt-0.5 shrink-0 text-cobalt-500" :size="12" />
        <span v-if="!asr.ready">
          首次使用需要下载约 {{ asr.model_size_mb || 486 }}MB 模型，请保持页面打开；音频不会上传。
        </span>
        <span v-else>音频在本机处理，不上传第三方。请保持页面打开。</span>
      </p>
    </div>

    <div
      v-else-if="running && !hasText"
      class="rounded-2xl border border-line bg-white p-5"
    >
      <div class="flex items-center gap-2 text-[11px] font-semibold text-cobalt-600">
        <span class="relative flex h-2 w-2">
          <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-cobalt-400 opacity-60" />
          <span class="relative inline-flex h-2 w-2 rounded-full bg-cobalt-500" />
        </span>
        {{ summary.message || (summary.segments.length ? '正在组织语言…' : '正在提取字幕…') }}
      </div>
      <div class="mt-5 space-y-3">
        <div class="skeleton h-3 w-32" />
        <div class="skeleton h-2.5 w-full" />
        <div class="skeleton h-2.5 w-[92%]" />
        <div class="skeleton h-2.5 w-[76%]" />
        <div class="skeleton mt-5 h-3 w-28" />
        <div class="skeleton h-2.5 w-full" />
        <div class="skeleton h-2.5 w-[84%]" />
        <div class="skeleton h-2.5 w-[66%]" />
      </div>
      <p class="mt-5 text-[10px] text-slate-400">
        {{ summary.segments.length ? `已读取 ${summary.segments.length} 条字幕，DeepSeek 正在生成结构化总结。` : '字幕优先，随后才会调用 AI。' }}
      </p>
    </div>

    <div
      v-else-if="!hasText && summary.status === 'idle'"
      class="rounded-2xl border border-dashed border-line bg-paper/60 px-5 py-10 text-center"
    >
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-cobalt-500 shadow-sm">
        <Sparkles :size="22" />
      </span>
      <p class="mt-3 text-sm font-bold text-ink">等待解析完成</p>
      <p class="mt-1 text-[11px] text-slate-400">解析成功后会从字幕开始，自动生成总结。</p>
    </div>

    <div
      v-else-if="!hasText"
      class="rounded-2xl border border-dashed border-line bg-paper/60 px-5 py-9 text-center"
    >
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-rose-400 shadow-sm">
        <AlertCircle :size="22" />
      </span>
      <p class="mt-3 text-sm font-bold text-ink">总结没有生成</p>
      <p class="mx-auto mt-1.5 max-w-md text-[11px] leading-5 text-slate-400">
        {{ error?.message || 'AI 返回了空内容，可以重新尝试。' }}
      </p>
      <div class="mt-4 flex flex-wrap justify-center gap-2">
        <button v-if="canRetryAsr" type="button" class="btn-primary !rounded-xl !px-4 !py-2 text-[11px]" @click="emit('transcribe')">
          <AudioLines :size="13" />
          重试语音转写
        </button>
        <button type="button" class="btn-secondary !px-4 !py-2 text-[11px]" @click="emit('retry')">
          <RefreshCw :size="13" />
          {{ canRetryAsr ? '重新提取平台字幕' : '重新尝试' }}
        </button>
      </div>
    </div>

    <div v-else>
      <div
        v-if="summary.asr"
        class="mb-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 px-3 py-2.5 text-[11px] leading-5 text-amber-800"
      >
        <TriangleAlert class="mt-0.5 shrink-0" :size="14" />
        <span>{{ summary.source }}：机器听写可能有错字、漏字，建议对照原视频。</span>
      </div>
      <div
        v-if="error && hasText"
        class="mb-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 px-3 py-2.5 text-[11px] leading-5 text-amber-800"
      >
        <TriangleAlert class="mt-0.5 shrink-0" :size="14" />
        <span>{{ error.message }} 已生成的部分仍可阅读。</span>
      </div>

      <div
        v-if="running"
        class="mb-3 flex items-center gap-2 text-[10px] font-semibold text-cobalt-600"
      >
        <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-cobalt-500" />
        {{ summary.message || '正在生成…' }}
      </div>

      <div class="prose prose-pianxia max-w-none" :class="{ 'stream-caret': running }" v-html="html" />

      <div class="mt-6 flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-line pt-3 text-[10px] text-slate-400">
        <span class="inline-flex items-center gap-1 font-semibold text-slate-500">
          <Sparkles :size="11" class="text-cobalt-500" />
          DeepSeek
        </span>
        <span v-if="summary.languageName">{{ summary.languageName }}</span>
        <span v-if="summary.segments.length">{{ summary.segments.length }} 条字幕</span>
        <span v-if="summary.asr" class="inline-flex items-center gap-1 text-amber-700">
          <Mic :size="10" />
          Whisper 转写
        </span>
        <span v-if="summary.truncated" class="text-amber-600">字幕过长，已首尾截取</span>
        <span class="ml-auto">AI 生成内容可能有误，请结合原视频判断</span>
      </div>

      <div v-if="error" class="mt-2 flex items-start gap-1.5 text-[10px] leading-4 text-rose-600">
        <AlertCircle class="mt-0.5 shrink-0" :size="12" />
        {{ error.message }}
      </div>
    </div>
  </div>
</template>
