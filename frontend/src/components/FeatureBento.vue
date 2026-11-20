<script setup>
import {
  ArrowDownToLine,
  Captions,
  Globe2,
  Layers,
  ListTree,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  Zap,
} from '@lucide/vue'

const platforms = ['B 站', 'YouTube', 'TED', '抖音', 'TikTok', 'X', 'Instagram', 'Vimeo', '微博']
</script>

<template>
  <section id="features" class="scroll-mt-24 py-16 sm:py-24">
    <div class="shell">
      <div class="max-w-2xl">
        <p class="section-label">THE FILM VAULT</p>
        <h2 class="section-title mt-3">
          不止下载，<span class="text-cobalt-600">更是一次精读。</span>
        </h2>
        <p class="mt-4 text-[14px] leading-7 text-slate-500">
          从链接到文件，从字幕到结构。片匣把一条视频的完整价值，收进同一个工作台。
        </p>
      </div>

      <div class="mt-9 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <article class="group relative overflow-hidden rounded-[24px] border border-line bg-white p-5 shadow-card transition duration-300 hover:-translate-y-1 hover:shadow-soft md:col-span-2">
          <div class="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-cobalt-100/60 blur-2xl" />
          <div class="relative">
            <div class="flex items-center justify-between">
              <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-cobalt-50 text-cobalt-600">
                <Globe2 :size="19" />
              </span>
              <span class="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">PLATFORMS</span>
            </div>
            <div class="mt-5 flex items-end gap-2">
              <span class="font-display text-[42px] font-black leading-none tracking-[-0.06em] text-ink">1800<span class="text-cobalt-500">+</span></span>
              <span class="mb-1 text-[11px] font-semibold text-slate-400">个站点</span>
            </div>
            <p class="mt-2 text-[12px] leading-5 text-slate-500">
              依托 yt-dlp 的解析能力，从 B 站、YouTube、TED 到抖音、TikTok、X。
            </p>
            <div class="mt-4 flex flex-wrap gap-1.5">
              <span v-for="platform in platforms" :key="platform" class="chip !px-2.5 !py-1 text-[10px]">
                {{ platform }}
              </span>
              <span class="inline-flex items-center rounded-full bg-cobalt-500 px-2.5 py-1 text-[10px] font-bold text-white">
                + 更多
              </span>
            </div>
            <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-line pt-3 text-[10px] font-medium text-slate-400">
              <span>社区规则持续更新</span>
              <span>无需安装插件</span>
              <span>解析失败可换代理通道</span>
            </div>
          </div>
        </article>

        <article id="ai" class="group relative overflow-hidden rounded-[24px] bg-ink p-5 text-white shadow-[0_34px_80px_-46px_rgba(0,0,0,.9)] transition duration-300 hover:-translate-y-1 md:col-span-2 scroll-mt-24">
          <div class="absolute -right-16 -top-20 h-64 w-64 rounded-full bg-cobalt-500/25 blur-3xl" />
          <div class="absolute bottom-0 left-1/3 h-28 w-28 rounded-full bg-gold/10 blur-2xl" />
          <div class="relative">
            <div class="flex items-center justify-between">
              <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 text-gold">
                <Sparkles :size="19" />
              </span>
              <span class="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.16em] text-white/55">
                DeepSeek · SSE
              </span>
            </div>
            <h3 class="mt-5 font-display text-[22px] font-black leading-[1.25] tracking-[-0.03em]">
              两小时的内容，<br /><span class="text-cobalt-300">五分钟读完。</span>
            </h3>
            <p class="mt-2 text-[12px] leading-5 text-white/50">
              自动提取字幕，生成结构化总结、可交互导图，并支持继续追问。
            </p>

            <div class="mt-4 rounded-2xl border border-white/10 bg-white/[0.07] p-3.5">
              <div class="flex items-center gap-2 text-[10px] font-semibold text-white/55">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                AI 精读完成
                <span class="ml-auto font-mono text-white/35">18:32 → 4 min</span>
              </div>
              <div class="mt-3 space-y-1.5">
                <span class="block h-1.5 w-[88%] rounded-full bg-white/25" />
                <span class="block h-1.5 w-full rounded-full bg-white/12" />
                <span class="block h-1.5 w-[72%] rounded-full bg-white/12" />
              </div>
              <div class="mt-3 flex flex-wrap gap-1.5">
                <span class="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1 text-[9px] font-semibold text-white/65"><MessageSquare :size="10" /> 总结</span>
                <span class="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1 text-[9px] font-semibold text-white/65"><ListTree :size="10" /> 导图</span>
                <span class="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1 text-[9px] font-semibold text-white/65"><Sparkles :size="10" /> 问答</span>
              </div>
            </div>
          </div>
        </article>

        <article class="group rounded-[22px] border border-line bg-white p-4 shadow-card transition duration-300 hover:-translate-y-1 hover:shadow-soft">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-gold/15 text-amber-700">
            <Layers :size="17" />
          </span>
          <h3 class="mt-4 text-[14px] font-bold text-ink">原画质落地</h3>
          <p class="mt-1 text-[11px] leading-5 text-slate-500">自动合并音视频，输出干净 MP4。</p>
          <div class="mt-3 space-y-1.5">
            <div class="flex items-center justify-between rounded-lg bg-paper px-2.5 py-1.5 text-[9px] font-bold text-slate-500">
              <span>1080P</span><span class="text-cobalt-600">H.264</span>
            </div>
            <div class="flex items-center justify-between rounded-lg bg-paper px-2.5 py-1.5 text-[9px] font-bold text-slate-500">
              <span>720P</span><span class="text-slate-400">MP4</span>
            </div>
          </div>
        </article>

        <article class="group rounded-[22px] border border-line bg-white p-4 shadow-card transition duration-300 hover:-translate-y-1 hover:shadow-soft">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-cobalt-50 text-cobalt-600">
            <Captions :size="17" />
          </span>
          <h3 class="mt-4 text-[14px] font-bold text-ink">字幕一起带走</h3>
          <p class="mt-1 text-[11px] leading-5 text-slate-500">带时间戳，一键导出三种格式。</p>
          <div class="mt-3 flex flex-wrap gap-1.5">
            <span v-for="format in ['SRT', 'VTT', 'TXT']" :key="format" class="rounded-lg border border-line bg-paper px-2 py-1 text-[9px] font-bold text-slate-500">
              {{ format }}
            </span>
          </div>
        </article>

        <article class="group rounded-[22px] border border-line bg-white p-4 shadow-card transition duration-300 hover:-translate-y-1 hover:shadow-soft">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
            <ShieldCheck :size="17" />
          </span>
          <h3 class="mt-4 text-[14px] font-bold text-ink">看完就忘</h3>
          <p class="mt-1 text-[11px] leading-5 text-slate-500">不存历史、不存视频，临时文件自动清理。</p>
          <div class="mt-3 flex items-center gap-2">
            <span class="rounded-lg bg-emerald-50 px-2 py-1 text-[9px] font-bold text-emerald-700">0 条历史</span>
            <span class="rounded-lg bg-paper px-2 py-1 text-[9px] font-bold text-slate-500">30 min 清理</span>
          </div>
        </article>

        <article class="group rounded-[22px] border border-line bg-white p-4 shadow-card transition duration-300 hover:-translate-y-1 hover:shadow-soft">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
            <Zap :size="17" />
          </span>
          <h3 class="mt-4 text-[14px] font-bold text-ink">双通道下载</h3>
          <p class="mt-1 text-[11px] leading-5 text-slate-500">代理更稳，直链更快。服务端自动判断可行性。</p>
          <div class="mt-3 flex items-center gap-1.5 text-[9px] font-bold">
            <span class="inline-flex items-center gap-1 rounded-lg bg-cobalt-50 px-2 py-1 text-cobalt-600"><ArrowDownToLine :size="10" /> 代理</span>
            <span class="inline-flex items-center gap-1 rounded-lg bg-paper px-2 py-1 text-slate-500"><Zap :size="10" /> 直链</span>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>
