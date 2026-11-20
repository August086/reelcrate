<script setup>
import { nextTick, ref, watch } from 'vue'
import {
  AlertCircle,
  Captions,
  CornerDownLeft,
  LoaderCircle,
  MessageSquare,
  Send,
  Sparkles,
} from '@lucide/vue'
import SetupNotice from './SetupNotice.vue'
import { renderMarkdown } from '../lib/markdown'

const props = defineProps({
  chat: { type: Object, required: true },
  summary: { type: Object, required: true },
  aiEnabled: { type: Boolean, default: false },
  canChat: { type: Boolean, default: false },
  video: { type: Object, default: null },
})
const emit = defineEmits(['ask'])

const question = ref('')
const inputEl = ref(null)
const scrollEl = ref(null)

const suggestions = [
  '用三句话概括这个视频',
  '列出最重要的 3 个观点',
  '这个视频适合谁看？',
]

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  })
}

watch(
  () => props.chat.messages.map((message) => `${message.role}:${message.content.length}`).join('|'),
  scrollToBottom,
)

function resize() {
  if (!inputEl.value) return
  inputEl.value.style.height = 'auto'
  inputEl.value.style.height = `${Math.min(112, inputEl.value.scrollHeight)}px`
}

function send() {
  const value = question.value.trim()
  if (!value || props.chat.streaming || !props.canChat) return
  emit('ask', value)
  question.value = ''
  nextTick(resize)
}

function useSuggestion(text) {
  question.value = text
  nextTick(() => {
    inputEl.value?.focus()
    resize()
  })
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

function rendered(content) {
  return renderMarkdown(content)
}
</script>

<template>
  <div class="flex h-[540px] flex-col">
    <SetupNotice v-if="!aiEnabled" class="shrink-0" />

    <div v-else-if="!canChat" class="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-line bg-paper/50 px-6 text-center">
      <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
        <Captions :size="22" />
      </span>
      <p class="mt-3 text-sm font-bold text-ink">先等字幕就位</p>
      <p class="mt-1 max-w-xs text-[11px] leading-5 text-slate-400">
        问答只会基于视频字幕回答。字幕提取完成后，这里会自动解锁。
      </p>
    </div>

    <template v-else>
      <div ref="scrollEl" class="no-scrollbar min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        <div v-if="!chat.messages.length" class="flex h-full flex-col items-center justify-center px-3 py-6 text-center">
          <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#1777FF,#84B8FF)] text-white shadow-[0_12px_28px_-12px_rgba(23,119,255,.7)]">
            <MessageSquare :size="21" />
          </span>
          <p class="mt-3 text-[14px] font-black text-ink">和这个视频聊一聊</p>
          <p class="mt-1 max-w-xs text-[11px] leading-5 text-slate-400">
            基于已提取的字幕回答，不会编造字幕之外的内容。
          </p>
          <div class="mt-4 flex flex-wrap justify-center gap-1.5">
            <button
              v-for="item in suggestions"
              :key="item"
              type="button"
              class="chip !px-2.5 !py-1.5 text-[10px]"
              @click="useSuggestion(item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <template v-for="(message, index) in chat.messages" :key="`${message.role}-${index}`">
          <div v-if="message.role === 'user'" class="flex justify-end">
            <div class="max-w-[86%] rounded-2xl rounded-br-md bg-cobalt-500 px-3.5 py-2.5 text-[12px] leading-5 text-white shadow-[0_10px_24px_-14px_rgba(23,119,255,.8)]">
              {{ message.content }}
            </div>
          </div>

          <div v-else class="flex gap-2.5">
            <span class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cobalt-50 text-cobalt-600">
              <Sparkles :size="13" />
            </span>
            <div class="min-w-0 flex-1">
              <div
                v-if="message.content"
                class="prose prose-reelcrate max-w-none !text-[12.5px] !leading-[1.75]"
                :class="{ 'stream-caret': message.pending }"
                v-html="rendered(message.content)"
              />
              <div v-else-if="message.pending" class="flex items-center gap-2 rounded-xl bg-paper px-3 py-2.5 text-[11px] text-slate-400">
                <LoaderCircle class="animate-spin" :size="13" />
                正在阅读字幕并组织回答…
              </div>
            </div>
          </div>
        </template>

        <div v-if="chat.error" class="flex items-start gap-2 rounded-xl border border-rose-100 bg-rose-50 px-3 py-2.5 text-[11px] leading-5 text-rose-700">
          <AlertCircle class="mt-0.5 shrink-0" :size="14" />
          {{ chat.error }}
        </div>
      </div>

      <form class="mt-3 shrink-0" @submit.prevent="send">
        <div class="flex items-end gap-2 rounded-2xl border border-line bg-white p-1.5 pl-3 shadow-sm transition focus-within:border-cobalt-300 focus-within:shadow-[0_0_0_4px_rgba(23,119,255,.06)]">
          <textarea
            ref="inputEl"
            v-model="question"
            rows="1"
            class="max-h-28 min-h-[36px] flex-1 resize-none bg-transparent py-2 text-[12px] leading-5 text-ink outline-none placeholder:text-slate-400"
            placeholder="问点什么，比如：这个视频的核心观点是什么？"
            :disabled="chat.streaming"
            @input="resize"
            @keydown="handleKeydown"
          />
          <button
            type="submit"
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cobalt-500 text-white transition hover:bg-cobalt-600 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!question.trim() || chat.streaming"
            aria-label="发送问题"
          >
            <LoaderCircle v-if="chat.streaming" class="animate-spin" :size="16" />
            <Send v-else :size="15" />
          </button>
        </div>
        <p class="mt-1.5 flex items-center justify-between px-1 text-[9px] text-slate-400">
          <span class="inline-flex items-center gap-1"><CornerDownLeft :size="10" /> Enter 发送 · Shift+Enter 换行</span>
          <span>仅依据字幕回答</span>
        </p>
      </form>
    </template>
  </div>
</template>
