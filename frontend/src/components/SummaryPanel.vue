<script setup>
import { computed, ref, watch } from 'vue'
import {
  Captions,
  ListTree,
  LoaderCircle,
  MessageSquare,
  RefreshCw,
  Sparkles,
} from '@lucide/vue'
import ChatTab from './ChatTab.vue'
import MindmapView from './MindmapView.vue'
import SubtitleTab from './SubtitleTab.vue'
import SummaryTab from './SummaryTab.vue'

const props = defineProps({
  video: { type: Object, required: true },
  summary: { type: Object, required: true },
  chat: { type: Object, required: true },
  aiEnabled: { type: Boolean, default: false },
  canChat: { type: Boolean, default: false },
  asr: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['summarize', 'ask', 'asr'])

const activeTab = ref('summary')

const tabs = computed(() => [
  {
    id: 'summary',
    label: '总结',
    icon: Sparkles,
    badge: props.summary.text ? 'ready' : props.summary.status === 'running' ? 'live' : '',
  },
  {
    id: 'subtitle',
    label: '字幕',
    icon: Captions,
    badge: props.summary.segments.length ? String(props.summary.segments.length) : '',
  },
  {
    id: 'mindmap',
    label: '导图',
    icon: ListTree,
    badge: props.summary.mindmap ? 'ready' : '',
  },
  { id: 'chat', label: '问答', icon: MessageSquare, badge: '' },
])

const running = computed(() => props.summary.status === 'running')
const statusTone = computed(() => {
  if (running.value) return 'live'
  if (props.summary.error?.code === 'ai_not_configured') return 'setup'
  if (props.summary.error?.code === 'no_subtitles') return 'empty'
  if (props.summary.error) return 'error'
  if (props.summary.status === 'ready') return 'ready'
  return 'idle'
})

watch(
  () => props.video?.id,
  () => {
    activeTab.value = 'summary'
  },
)

function selectTab(id) {
  activeTab.value = id
}
</script>

<template>
  <div class="card flex min-h-[620px] flex-col overflow-hidden">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-4 sm:px-5">
      <div class="flex min-w-0 items-center gap-3">
        <span class="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#1777FF,#4A94FF)] text-white shadow-[0_12px_24px_-14px_rgba(23,119,255,.8)]">
          <Sparkles :size="18" />
          <span class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border-2 border-white bg-gold" />
        </span>
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <h2 class="text-[15px] font-black tracking-tight text-ink">AI 精读</h2>
            <span
              class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold"
              :class="{
                'bg-emerald-50 text-emerald-600': statusTone === 'ready',
                'bg-cobalt-50 text-cobalt-600': statusTone === 'live',
                'bg-amber-50 text-amber-700': statusTone === 'setup' || statusTone === 'empty',
                'bg-rose-50 text-rose-500': statusTone === 'error',
                'bg-slate-100 text-slate-400': statusTone === 'idle',
              }"
            >
              <span
                class="h-1.5 w-1.5 rounded-full"
                :class="{
                  'bg-emerald-500': statusTone === 'ready',
                  'animate-pulse bg-cobalt-500': statusTone === 'live',
                  'bg-amber-500': statusTone === 'setup' || statusTone === 'empty',
                  'bg-rose-500': statusTone === 'error',
                  'bg-slate-300': statusTone === 'idle',
                }"
              />
              {{ running ? 'READING' : statusTone === 'error' ? 'CHECK' : statusTone === 'setup' ? 'SETUP' : statusTone === 'empty' ? 'NO SUBS' : statusTone === 'ready' ? 'READY' : 'STANDBY' }}
            </span>
          </div>
          <p class="mt-0.5 truncate text-[10px] text-slate-400">
            字幕为底 · 总结 · 导图 · 追问
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <span class="hidden rounded-full border border-line bg-paper px-2.5 py-1 text-[9px] font-semibold text-slate-500 sm:inline-flex">
          {{ aiEnabled ? 'DeepSeek' : 'AI 未配置' }}
        </span>
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-full border border-line bg-white text-slate-500 transition hover:border-cobalt-200 hover:text-cobalt-600 disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="running"
          aria-label="重新生成总结"
          @click="emit('summarize')"
        >
          <LoaderCircle v-if="running" class="animate-spin" :size="14" />
          <RefreshCw v-else :size="14" />
        </button>
      </div>
    </div>

    <div class="border-b border-line px-3 py-2.5 sm:px-4">
      <div class="flex gap-1 overflow-x-auto rounded-full bg-paper p-1 no-scrollbar" role="tablist" aria-label="AI 精读功能">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.id"
          class="flex shrink-0 items-center gap-1.5 rounded-full px-3 py-2 text-[11px] font-bold transition"
          :class="activeTab === tab.id ? 'bg-white text-ink shadow-sm' : 'text-slate-500 hover:text-ink'"
          @click="selectTab(tab.id)"
        >
          <component :is="tab.icon" :size="13" :stroke-width="2.2" :class="activeTab === tab.id ? 'text-cobalt-600' : 'text-slate-400'" />
          {{ tab.label }}
          <span
            v-if="tab.badge === 'live'"
            class="h-1.5 w-1.5 animate-pulse rounded-full bg-cobalt-500"
          />
          <span
            v-else-if="tab.badge === 'ready'"
            class="h-1.5 w-1.5 rounded-full bg-emerald-500"
          />
          <span
            v-else-if="tab.badge"
            class="rounded-full bg-slate-100 px-1.5 py-0.5 text-[8px] font-bold text-slate-500"
          >
            {{ tab.badge }}
          </span>
        </button>
      </div>
    </div>

    <div class="flex-1 p-4 sm:p-5">
      <SummaryTab
        v-show="activeTab === 'summary'"
        :video="video"
        :summary="summary"
        :ai-enabled="aiEnabled"
        :asr="asr"
        @retry="emit('summarize')"
        @transcribe="emit('asr')"
      />
      <SubtitleTab
        v-show="activeTab === 'subtitle'"
        :video="video"
        :summary="summary"
        :asr="asr"
        @transcribe="emit('asr')"
        @retry="emit('summarize')"
      />
      <MindmapView
        v-if="activeTab === 'mindmap'"
        :markdown="summary.mindmap"
        :title="video.title"
        :running="running"
        :error="summary.error"
      />
      <ChatTab
        v-show="activeTab === 'chat'"
        :chat="chat"
        :summary="summary"
        :ai-enabled="aiEnabled"
        :can-chat="canChat"
        :video="video"
        @ask="emit('ask', $event)"
      />
    </div>

    <div class="flex flex-wrap items-center justify-between gap-2 border-t border-line px-4 py-2.5 text-[9px] text-slate-400 sm:px-5">
      <span class="inline-flex items-center gap-1"><Sparkles :size="10" class="text-cobalt-500" /> AI 可能会出错，请核对原视频</span>
      <span v-if="summary.languageName">{{ summary.languageName }} · {{ summary.segments.length }} 条字幕</span>
    </div>
  </div>
</template>
