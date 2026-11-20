<script setup>
import { computed } from 'vue'
import {
  CheckCircle2,
  Copy,
  Download,
  Link2,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from '@lucide/vue'
import { formatBytes } from '../lib/format'

const props = defineProps({
  video: { type: Object, required: true },
  format: { type: Object, default: null },
  download: { type: Object, required: true },
  direct: { type: Object, required: true },
  summary: { type: Object, required: true },
  aiEnabled: { type: Boolean, default: false },
})
const emit = defineEmits(['download', 'direct', 'summarize'])

const busy = computed(() =>
  ['queued', 'preparing', 'downloading', 'merging'].includes(props.download.status),
)
const done = computed(() => props.download.status === 'done')
const failed = computed(() => props.download.status === 'error')
const progress = computed(() => Math.max(0, Math.min(100, Number(props.download.progress || 0))))
const summaryRunning = computed(() => props.summary.status === 'running')
const summaryLabel = computed(() => {
  if (summaryRunning.value) return 'AI 正在精读'
  if (props.summary.text) return '重新总结'
  return 'AI 精读'
})

const statusLabel = computed(() => {
  if (props.download.stage) return props.download.stage
  if (done.value) return '已交给浏览器下载'
  if (failed.value) return '下载失败'
  return '服务端准备完成后自动开始'
})
</script>

<template>
  <div class="card p-4 sm:p-5">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h3 class="text-[13px] font-bold text-ink">下载视频</h3>
        <p class="mt-1 text-[10px] leading-4 text-slate-400">
          {{ format ? `${format.label} · ${format.quality}` : '请选择一个清晰度' }}
        </p>
      </div>
      <span v-if="format?.filesize" class="rounded-full bg-paper px-2.5 py-1 text-[10px] font-bold text-slate-500">
        约 {{ formatBytes(format.filesize) }}
      </span>
    </div>

    <button
      type="button"
      class="btn-primary mt-4 w-full !rounded-2xl !py-3.5"
      :disabled="busy || !format"
      @click="emit('download')"
    >
      <LoaderCircle v-if="busy" class="animate-spin" :size="17" />
      <CheckCircle2 v-else-if="done" :size="17" />
      <Download v-else :size="17" :stroke-width="2.4" />
      <span v-if="busy">正在准备文件</span>
      <span v-else-if="done">再次下载</span>
      <span v-else>下载视频</span>
      <span v-if="busy" class="ml-auto font-mono text-[11px] text-white/75">{{ Math.round(progress) }}%</span>
    </button>

    <div v-if="busy || failed || done" class="mt-3">
      <div class="h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          class="h-full rounded-full bg-cobalt-500 transition-all duration-500"
          :class="failed ? '!bg-rose-500' : done ? '!bg-emerald-500' : ''"
          :style="{ width: `${failed ? 100 : progress}%` }"
        />
      </div>
      <p
        class="mt-2 flex items-center gap-1.5 text-[10px]"
        :class="failed ? 'text-rose-600' : done ? 'text-emerald-600' : 'text-slate-400'"
      >
        <TriangleAlert v-if="failed" :size="12" />
        <CheckCircle2 v-else-if="done" :size="12" />
        <span class="truncate">{{ download.error || statusLabel }}</span>
      </p>
    </div>

    <div class="mt-3 grid grid-cols-2 gap-2">
      <button
        type="button"
        class="btn-secondary !rounded-xl !px-3 !py-2.5 text-[11px]"
        :disabled="direct.status === 'loading'"
        @click="emit('direct')"
      >
        <LoaderCircle v-if="direct.status === 'loading'" class="animate-spin" :size="14" />
        <Link2 v-else :size="14" />
        复制直链
      </button>
      <button
        type="button"
        class="btn-secondary !rounded-xl !px-3 !py-2.5 text-[11px]"
        :disabled="summaryRunning"
        @click="emit('summarize')"
      >
        <LoaderCircle v-if="summaryRunning" class="animate-spin" :size="14" />
        <RefreshCw v-else-if="summary.text" :size="14" />
        <Sparkles v-else :size="14" />
        {{ summaryLabel }}
      </button>
    </div>

    <p v-if="direct.status === 'ready' && direct.url" class="mt-2 rounded-xl bg-paper p-2.5">
      <span class="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-wider text-emerald-600">
        <CheckCircle2 :size="11" />
        直链已生成，可直接复制
      </span>
      <span class="mt-1 flex items-center gap-1">
        <input
          class="min-w-0 flex-1 truncate bg-transparent font-mono text-[9px] text-slate-500 outline-none"
          :value="direct.url"
          readonly
          aria-label="视频直链"
          @focus="$event.target.select()"
        />
        <Copy :size="11" class="shrink-0 text-slate-400" />
      </span>
    </p>
    <p v-if="direct.error" class="mt-2 text-[10px] leading-4 text-rose-600">{{ direct.error }}</p>
    <p class="mt-2 text-[9px] leading-4 text-slate-400">
      直链仅对单文件格式开放；受平台防盗链影响时可能失效，请改用代理下载。
    </p>

    <div class="mt-4 flex items-start gap-2 border-t border-line pt-3 text-[10px] leading-4 text-slate-400">
      <ShieldCheck class="mt-0.5 shrink-0 text-cobalt-500" :size="13" />
      <span>
        文件由服务端临时中转，下载开始后自动清理；不保存观看记录。
        <span v-if="!aiEnabled" class="text-amber-600"> AI 需要配置 DeepSeek Key。</span>
      </span>
    </div>
  </div>
</template>
