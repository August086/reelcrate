<script setup>
import { ArrowLeft, Download, LoaderCircle, ShieldCheck, Sparkles } from '@lucide/vue'
import { computed } from 'vue'
import VideoPoster from './VideoPoster.vue'
import FormatPicker from './FormatPicker.vue'
import DownloadCard from './DownloadCard.vue'
import SummaryPanel from './SummaryPanel.vue'

const props = defineProps({
  video: { type: Object, required: true },
  selectedId: { type: String, default: '' },
  selectedFormat: { type: Object, default: null },
  summary: { type: Object, required: true },
  chat: { type: Object, required: true },
  download: { type: Object, required: true },
  direct: { type: Object, required: true },
  aiEnabled: { type: Boolean, default: false },
  canChat: { type: Boolean, default: false },
  asr: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['select', 'download', 'direct', 'summarize', 'ask', 'reset', 'asr'])

const downloadBusy = computed(() =>
  ['queued', 'preparing', 'downloading', 'merging'].includes(props.download.status),
)
</script>

<template>
  <section id="workbench" class="scroll-mt-24 pb-14 pt-2 sm:pb-20">
    <div class="shell">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-2.5">
          <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-700">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            解析成功
          </span>
          <span class="text-[11px] font-medium text-slate-400">
            {{ video.platform }} · 选择清晰度即可下载
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="selectedFormat"
            type="button"
            class="btn-primary !px-4 !py-2 text-[11px]"
            :disabled="downloadBusy"
            @click="emit('download')"
          >
            <LoaderCircle v-if="downloadBusy" class="animate-spin" :size="13" />
            <Download v-else :size="13" />
            {{ downloadBusy ? `${Math.round(download.progress)}%` : `下载 ${selectedFormat.label}` }}
          </button>
          <button type="button" class="btn-ghost !px-3 !py-1.5 text-[11px]" @click="emit('reset')">
            <ArrowLeft :size="13" />
            换一个链接
          </button>
        </div>
      </div>

      <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,0.83fr)_minmax(0,1.17fr)] lg:gap-6">
        <div class="min-w-0 space-y-4">
          <VideoPoster :video="video" />
          <FormatPicker
            :formats="video.formats"
            :model-value="selectedId"
            :notes="video.notes"
            @update:model-value="emit('select', $event)"
          />
          <DownloadCard
            :video="video"
            :format="selectedFormat"
            :download="download"
            :direct="direct"
            :summary="summary"
            :ai-enabled="aiEnabled"
            @download="emit('download')"
            @direct="emit('direct')"
            @summarize="emit('summarize')"
          />
          <p class="flex items-start gap-2 px-1 text-[10px] leading-4 text-slate-400">
            <ShieldCheck class="mt-0.5 shrink-0 text-cobalt-500" :size="12" />
            仅用于个人学习与内容备份。请遵守平台条款与版权规定，临时文件会在任务结束后清理。
          </p>
        </div>

        <div class="min-w-0">
          <div class="mb-3 flex items-center gap-2 px-1">
            <span class="flex h-6 w-6 items-center justify-center rounded-lg bg-cobalt-50 text-cobalt-600">
              <Sparkles :size="13" />
            </span>
            <p class="text-[11px] font-semibold text-slate-500">
              已自动开始 AI 精读
              <span class="text-slate-400">· 不用手动点</span>
            </p>
          </div>
          <SummaryPanel
            :video="video"
            :summary="summary"
            :chat="chat"
            :ai-enabled="aiEnabled"
            :can-chat="canChat"
            :asr="asr"
            @summarize="emit('summarize')"
            @ask="emit('ask', $event)"
            @asr="emit('asr')"
          />
        </div>
      </div>
    </div>
  </section>
</template>
