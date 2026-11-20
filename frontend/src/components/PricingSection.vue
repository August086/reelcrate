<script setup>
import { ArrowRight, Check, Crown, Lock, Sparkles } from '@lucide/vue'

const emit = defineEmits(['search'])

const freeFeatures = [
  '全平台链接解析',
  '标准清晰度下载',
  '字幕提取与 SRT / VTT 导出',
  'AI 总结、导图与问答（需配置 Key）',
  '代理 / 直链双通道',
]

const proFeatures = [
  '4K / HDR 原画质',
  '批量链接与队列',
  '字幕翻译与双语对照',
  '更高 AI 精读频次',
  '优先下载通道',
]
</script>

<template>
  <section id="pricing" class="scroll-mt-24 py-16 sm:py-24">
    <div class="shell">
      <div class="mx-auto max-w-2xl text-center">
        <p class="section-label">SIMPLE PRICING</p>
        <h2 class="section-title mt-3">先把活干完，再谈升级。</h2>
        <p class="mt-3 text-[13px] leading-6 text-slate-500">
          当前版本全部功能免费开放。Pro 是为重度创作者准备的下一步，不会在你不知情时扣费。
        </p>
      </div>

      <div class="mx-auto mt-9 grid max-w-4xl gap-4 md:grid-cols-2">
        <article class="relative flex flex-col rounded-[26px] border border-line bg-white p-6 shadow-card">
          <div class="flex items-center justify-between">
            <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-cobalt-50 text-cobalt-600">
              <Sparkles :size="18" />
            </span>
            <span class="rounded-full bg-emerald-50 px-2.5 py-1 text-[9px] font-bold uppercase tracking-wider text-emerald-700">当前可用</span>
          </div>
          <h3 class="mt-5 text-[17px] font-black text-ink">片匣 Free</h3>
          <p class="mt-1 text-[11px] leading-5 text-slate-400">给每一次“想把好内容留下来”的冲动。</p>
          <div class="mt-5 flex items-end gap-1.5">
            <span class="font-display text-[44px] font-black leading-none tracking-[-0.06em] text-ink">¥0</span>
            <span class="mb-1 text-[11px] font-semibold text-slate-400">/ 永久</span>
          </div>
          <ul class="mt-5 space-y-2.5">
            <li v-for="item in freeFeatures" :key="item" class="flex items-start gap-2 text-[11px] leading-5 text-slate-600">
              <span class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                <Check :size="10" :stroke-width="3" />
              </span>
              {{ item }}
            </li>
          </ul>
          <button type="button" class="btn-primary mt-6 w-full !rounded-xl" @click="emit('search')">
            立即解析
            <ArrowRight :size="15" />
          </button>
        </article>

        <article class="relative flex flex-col overflow-hidden rounded-[26px] bg-ink p-6 text-white shadow-[0_40px_90px_-50px_rgba(10,16,32,.9)]">
          <div class="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-gold/20 blur-3xl" />
          <div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-gold/20 via-gold to-gold/20" />
          <div class="relative">
            <div class="flex items-center justify-between">
              <span class="flex h-10 w-10 items-center justify-center rounded-xl border border-gold/30 bg-gold/10 text-gold">
                <Crown :size="18" />
              </span>
              <span class="rounded-full border border-gold/30 bg-gold/10 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.16em] text-gold">
                Pro · 即将上线
              </span>
            </div>
            <h3 class="mt-5 text-[17px] font-black">片匣 Pro</h3>
            <p class="mt-1 text-[11px] leading-5 text-white/45">给需要批量、清晰度与翻译的重度创作者。</p>
            <div class="mt-5 flex items-end gap-1.5">
              <span class="font-display text-[44px] font-black leading-none tracking-[-0.06em] text-white">¥19</span>
              <span class="mb-1 text-[11px] font-semibold text-white/40">/ 月 · 规划价</span>
            </div>
            <ul class="mt-5 space-y-2.5">
              <li v-for="item in proFeatures" :key="item" class="flex items-start gap-2 text-[11px] leading-5 text-white/65">
                <span class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-gold/15 text-gold">
                  <Check :size="10" :stroke-width="3" />
                </span>
                {{ item }}
              </li>
            </ul>
            <button type="button" class="mt-6 flex w-full cursor-not-allowed items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/[0.06] px-4 py-3 text-[12px] font-bold text-white/45" disabled>
              <Lock :size="14" />
              即将开放
            </button>
            <p class="mt-2 text-center text-[9px] text-white/30">Pro 权益与价格以实际上线为准</p>
          </div>
        </article>
      </div>

      <p class="mt-5 text-center text-[10px] text-slate-400">
        本版本不收取任何费用；AI 能力由你自己的 DeepSeek Key 提供。
      </p>
    </div>
  </section>
</template>
