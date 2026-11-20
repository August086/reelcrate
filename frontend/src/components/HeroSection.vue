<script setup>
import { ref, watch } from 'vue'
import {
  AlertCircle,
  ArrowRight,
  Captions,
  Clipboard,
  Clock3,
  Download,
  LoaderCircle,
  Play,
  Search,
  ShieldCheck,
  Sparkles,
  Wand2,
  Zap,
} from '@lucide/vue'
import CinemaStill from './CinemaStill.vue'
import { useToast } from '../composables/useToast'

const props = defineProps({
  compact: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
  initialUrl: { type: String, default: '' },
})
const emit = defineEmits(['parse'])

const toast = useToast()
const query = ref(props.initialUrl || '')
const inputEl = ref(null)

const SAMPLES = {
  bilibili: 'https://www.bilibili.com/video/BV1GJ411x7h7/',
  ted: 'https://www.ted.com/talks/chimamanda_ngozi_adichie_the_danger_of_a_single_story',
}

watch(
  () => props.initialUrl,
  (value) => {
    if ((value || '') !== query.value) query.value = value || ''
  },
)

function focus() {
  inputEl.value?.focus()
  document.getElementById('hero')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

defineExpose({ focus })

function submit() {
  emit('parse', query.value)
}

function sample(key) {
  query.value = SAMPLES[key]
  emit('parse', SAMPLES[key])
}

async function paste() {
  try {
    const text = await navigator.clipboard.readText()
    if (text?.trim()) {
      query.value = text.trim()
      inputEl.value?.focus()
    }
  } catch {
    toast.info('浏览器没有授予剪贴板权限，请手动粘贴链接。')
  }
}
</script>

<template>
  <section
    id="hero"
    class="relative overflow-hidden transition-all duration-500"
    :class="compact ? 'pb-8 pt-6 sm:pt-8' : 'pb-16 pt-10 sm:pt-14 lg:pb-24 lg:pt-20'"
  >
    <div class="pointer-events-none absolute inset-0 -z-10 bg-hero-glow" />
    <div
      class="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[560px] dot-grid opacity-40 [mask-image:linear-gradient(to_bottom,black,transparent)]"
    />
    <div class="pointer-events-none absolute -right-24 top-24 -z-10 h-72 w-72 rounded-full border border-cobalt-200/40 sm:h-96 sm:w-96" />
    <div class="pointer-events-none absolute -right-8 top-40 -z-10 h-40 w-40 rounded-full border border-gold/20 sm:h-56 sm:w-56" />

    <div class="shell">
      <div
        class="grid items-center gap-12 transition-all duration-500"
        :class="compact ? 'grid-cols-1' : 'lg:grid-cols-[1.04fr_.96fr]'"
      >
        <div :class="compact ? 'mx-auto w-full max-w-4xl' : ''">
          <div v-if="!compact" class="flex flex-wrap items-center gap-3">
            <span class="eyebrow">
              <span class="relative flex h-2 w-2">
                <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              在线解析 · 无需登录
            </span>
            <span class="text-[11px] font-semibold tracking-[0.16em] text-slate-400">1800+ 平台 · POWERED BY YT-DLP</span>
          </div>

          <div v-if="compact" class="mb-4 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-cobalt-600">
            <span class="h-px w-6 bg-cobalt-300" />
            再解析一个视频
          </div>

          <h1
            v-if="!compact"
            class="mt-6 max-w-[760px] font-display font-black tracking-[-0.055em] text-ink"
          >
            <span class="block text-[42px] leading-[1.08] sm:text-[56px] lg:text-[66px]">把全网好视频，</span>
            <span class="relative mt-1 inline-block text-[42px] leading-[1.08] sm:text-[56px] lg:text-[66px]">
              <span class="relative z-10 text-cobalt-600">一键收进匣子</span>
              <span class="absolute -inset-x-2 bottom-1 z-0 h-4 -rotate-1 rounded-full bg-gold/25 sm:h-5" />
            </span><span class="text-ink">。</span>
          </h1>
          <p
            v-if="!compact"
            class="mt-5 max-w-xl text-[15px] leading-7 text-slate-500 sm:text-base"
          >
            粘贴链接，提取原画质视频与字幕，再用 AI 把两小时的内容读成五分钟。
            干净、直接、不留痕。
          </p>

          <form
            class="relative mt-7 flex items-center gap-2 rounded-full border border-line bg-white p-2 pl-4 shadow-soft transition duration-300 focus-within:border-cobalt-300 focus-within:shadow-glow sm:pl-5"
            role="search"
            @submit.prevent="submit"
          >
            <Search class="ml-0.5 shrink-0 text-slate-400" :size="20" :stroke-width="2" />
            <input
              ref="inputEl"
              v-model="query"
              type="text"
              class="h-11 min-w-0 flex-1 bg-transparent text-[14px] text-ink outline-none placeholder:text-slate-400 sm:text-[15px]"
              placeholder="粘贴视频链接，支持 1800+ 平台"
              autocomplete="off"
              autocapitalize="off"
              spellcheck="false"
              aria-label="视频链接"
            />
            <button
              type="button"
              class="hidden h-10 shrink-0 items-center gap-1.5 rounded-full px-3 text-xs font-semibold text-slate-500 transition hover:bg-paper hover:text-ink sm:inline-flex"
              @click="paste"
            >
              <Clipboard :size="15" />
              粘贴
            </button>
            <button
              type="submit"
              class="btn-primary h-11 shrink-0 !px-4 text-[13px] sm:!px-5 sm:text-sm"
              :disabled="busy"
            >
              <LoaderCircle v-if="busy" class="animate-spin" :size="16" />
              <Wand2 v-else :size="16" :stroke-width="2.2" />
              <span class="hidden sm:inline">{{ busy ? '正在解析' : '解析视频' }}</span>
              <span class="sm:hidden">{{ busy ? '解析中' : '解析' }}</span>
              <ArrowRight v-if="!busy" :size="15" :stroke-width="2.4" />
            </button>
          </form>

          <div v-if="!compact" class="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 pl-1 text-[12px] text-slate-400">
            <span class="font-medium text-slate-400">试试</span>
            <button type="button" class="font-semibold text-slate-600 underline decoration-slate-200 underline-offset-4 transition hover:text-cobalt-600 hover:decoration-cobalt-300" @click="sample('bilibili')">
              B 站视频
            </button>
            <span class="h-1 w-1 rounded-full bg-slate-300" />
            <button type="button" class="font-semibold text-slate-600 underline decoration-slate-200 underline-offset-4 transition hover:text-cobalt-600 hover:decoration-cobalt-300" @click="sample('ted')">
              TED 演讲（带字幕）
            </button>
            <span class="hidden sm:inline">· 不需要登录，直接看结果</span>
          </div>

          <div v-if="error" class="mt-4 flex items-start gap-2 rounded-2xl border border-rose-100 bg-rose-50/80 px-4 py-3 text-[13px] leading-5 text-rose-700">
            <AlertCircle class="mt-0.5 shrink-0" :size="16" />
            <span>{{ error }}</span>
          </div>

          <div v-if="!compact" class="mt-8 flex flex-wrap gap-x-5 gap-y-3 text-[12px] font-medium text-slate-500">
            <span class="inline-flex items-center gap-1.5"><ShieldCheck :size="15" class="text-cobalt-500" /> 不保存视频</span>
            <span class="inline-flex items-center gap-1.5"><Zap :size="15" class="text-cobalt-500" /> 代理 / 直链双通道</span>
            <span class="inline-flex items-center gap-1.5"><Captions :size="15" class="text-cobalt-500" /> 字幕可导出</span>
            <span class="inline-flex items-center gap-1.5"><Sparkles :size="15" class="text-cobalt-500" /> AI 总结 · 导图 · 问答</span>
          </div>
        </div>

        <div v-if="!compact" class="relative hidden lg:block" aria-hidden="true">
          <div class="absolute left-1/2 top-1/2 h-[420px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cobalt-400/10 blur-3xl" />

          <div class="relative mx-auto h-[520px] w-[530px]">
            <div class="absolute left-3 top-24 w-[430px] -rotate-6 rounded-[24px] border border-line bg-white/60 p-2 shadow-soft backdrop-blur">
              <div class="aspect-[16/10] rounded-[18px] bg-[linear-gradient(135deg,#dce9ff,#f4f8ff)]" />
            </div>

            <div class="absolute -top-2 right-0 z-20 w-[214px] rotate-3 rounded-[22px] border border-line bg-white/95 p-4 shadow-invoice backdrop-blur">
              <div class="flex items-center gap-2">
                <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-cobalt-50 text-cobalt-600">
                  <Sparkles :size="14" />
                </span>
                <span class="text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">AI 精读</span>
                <span class="ml-auto flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
              </div>
              <p class="mt-3 text-[13px] font-bold leading-5 text-ink">把 2 小时访谈，读成 5 分钟</p>
              <div class="mt-3 space-y-1.5">
                <span class="block h-1.5 w-full rounded-full bg-slate-100" />
                <span class="block h-1.5 w-[86%] rounded-full bg-slate-100" />
                <span class="block h-1.5 w-[64%] rounded-full bg-cobalt-100" />
              </div>
              <div class="mt-3 flex items-center justify-between text-[10px] font-semibold text-slate-400">
                <span>3 个核心观点</span>
                <span>1 张导图</span>
              </div>
            </div>

            <div class="absolute left-1/2 top-1/2 z-10 w-[456px] -translate-x-1/2 -translate-y-1/2 rotate-[1.6deg]">
              <div class="rounded-[26px] border border-white/70 bg-white/90 p-2 shadow-[0_50px_100px_-46px_rgba(10,16,32,.65)] backdrop-blur">
                <div class="relative overflow-hidden rounded-[20px] bg-ink">
                  <div class="absolute inset-y-0 left-0 z-10 w-2 bg-ink film-perf opacity-80" />
                  <div class="absolute inset-y-0 right-0 z-10 w-2 bg-ink film-perf opacity-80" />
                  <div class="relative aspect-[16/10]">
                    <CinemaStill />
                    <div class="absolute inset-0 bg-gradient-to-t from-ink via-ink/10 to-transparent" />
                    <div class="absolute left-4 top-4 flex items-center gap-2">
                      <span class="inline-flex items-center gap-1.5 rounded-full bg-black/35 px-2.5 py-1 text-[10px] font-semibold text-white/85 backdrop-blur">
                        <span class="h-1.5 w-1.5 rounded-full bg-rose-400" /> PREVIEW
                      </span>
                      <span class="rounded-full bg-black/35 px-2.5 py-1 font-mono text-[10px] text-white/80 backdrop-blur">18:32</span>
                    </div>
                    <div class="absolute bottom-4 left-4 right-4">
                      <p class="text-[17px] font-bold leading-6 text-white">如何把碎片时间，变成自己的知识体系</p>
                      <p class="mt-1 text-[11px] text-white/55">ReelCrate · 每日精选</p>
                    </div>
                    <span class="absolute left-1/2 top-[42%] flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/30 bg-white/15 text-white backdrop-blur-md">
                      <Play :size="22" class="ml-1" fill="currentColor" />
                    </span>
                  </div>
                  <div class="flex items-center justify-between gap-3 border-t border-white/10 px-4 py-3">
                    <div class="flex items-center gap-2 text-[10px] font-semibold text-white/65">
                      <span class="rounded-full bg-white/10 px-2 py-1 text-white">1080P</span>
                      <span class="rounded-full bg-white/10 px-2 py-1">MP4</span>
                      <span class="rounded-full bg-white/10 px-2 py-1">字幕</span>
                    </div>
                    <span class="inline-flex items-center gap-1.5 rounded-full bg-cobalt-500 px-3 py-1.5 text-[10px] font-bold text-white">
                      <Download :size="12" /> 下载
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="absolute -bottom-2 left-0 z-20 animate-float rounded-2xl border border-line bg-white/95 p-3.5 shadow-invoice backdrop-blur [animation-delay:-2s]">
              <div class="flex items-center gap-2.5">
                <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-gold/15 text-amber-600">
                  <Clock3 :size="17" />
                </span>
                <div>
                  <p class="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400">已为你读薄</p>
                  <p class="text-[13px] font-bold text-ink">18:32 → 4 min</p>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </section>
</template>
