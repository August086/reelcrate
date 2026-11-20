<script setup>
import { ArrowUpRight, Code2 } from '@lucide/vue'
import BrandMark from './BrandMark.vue'
</script>

<template>
  <footer class="relative overflow-hidden bg-ink text-white">
    <div class="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cobalt-400/50 to-transparent" />
    <div class="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full bg-cobalt-500/10 blur-3xl" />
    <div class="shell relative py-12 sm:py-16">
      <div class="grid gap-10 md:grid-cols-[1.4fr_.8fr_.8fr_.8fr]">
        <div>
          <BrandMark light />
          <p class="mt-4 max-w-xs text-[12px] leading-6 text-white/45">
            把好视频收进匣子。下载、字幕、AI 精读，一条链接完成。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[9px] font-semibold text-white/45">FastAPI</span>
            <span class="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[9px] font-semibold text-white/45">yt-dlp</span>
            <span class="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[9px] font-semibold text-white/45">Vue 3</span>
            <span class="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[9px] font-semibold text-white/45">DeepSeek</span>
          </div>
        </div>

        <div>
          <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-white/35">产品</p>
          <div class="mt-3 space-y-2 text-[11px] text-white/55">
            <a href="#features" class="block transition hover:text-white">能力</a>
            <a href="#ai" class="block transition hover:text-white">AI 精读</a>
            <a href="#pricing" class="block transition hover:text-white">定价</a>
            <a href="/api/docs" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 transition hover:text-white">
              API 文档 <ArrowUpRight :size="10" />
            </a>
          </div>
        </div>

        <div>
          <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-white/35">平台</p>
          <div class="mt-3 space-y-2 text-[11px] text-white/55">
            <a href="#platforms" class="block transition hover:text-white">哔哩哔哩</a>
            <a href="#platforms" class="block transition hover:text-white">YouTube</a>
            <a href="#platforms" class="block transition hover:text-white">TED</a>
            <a href="#platforms" class="block transition hover:text-white">1800+ 站点</a>
          </div>
        </div>

        <div>
          <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-white/35">说明</p>
          <div class="mt-3 space-y-2 text-[11px] leading-5 text-white/55">
            <p>不存储视频与观看记录</p>
            <p>临时文件自动清理</p>
            <p>AI 需要自备 DeepSeek Key</p>
            <p class="text-white/35">请遵守平台条款与版权规定</p>
          </div>
        </div>
      </div>

      <div class="mt-10 flex flex-col gap-4 border-t border-white/10 pt-5 text-[10px] text-white/30 sm:flex-row sm:items-center sm:justify-between">
        <p>© 2026 片匣 PIANXIA · 仅用于个人学习与内容备份</p>
        <p class="inline-flex items-center gap-1.5">
          <Code2 :size="11" />
          Built with yt-dlp · FastAPI · Vue 3
        </p>
      </div>
    </div>
  </footer>
</template>
