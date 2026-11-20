<script setup>
const platforms = [
  { name: '哔哩哔哩', mark: 'B', color: '#00A1D6', kind: '弹幕视频' },
  { name: 'YouTube', mark: 'Y', color: '#FF0033', kind: '全球视频' },
  { name: 'TED', mark: 'T', color: '#E62B1E', kind: '演讲 · 字幕' },
  { name: '抖音', mark: 'D', color: '#111111', kind: '短视频' },
  { name: 'TikTok', mark: 'T', color: '#00F2EA', kind: '短视频', dark: true },
  { name: 'X / Twitter', mark: 'X', color: '#111111', kind: '社交视频' },
  { name: 'Instagram', mark: 'I', color: '#E1306C', kind: 'Reels' },
  { name: 'Vimeo', mark: 'V', color: '#1AB7EA', kind: '创作者视频' },
  { name: '微博', mark: '微', color: '#E6162D', kind: '社交视频' },
  { name: '小红书', mark: '小', color: '#FF2442', kind: '生活方式' },
  { name: '腾讯视频', mark: '腾', color: '#FF7F00', kind: '长视频' },
  { name: '优酷', mark: '优', color: '#1BA5E0', kind: '长视频' },
]
</script>

<template>
  <section id="platforms" class="scroll-mt-24 border-y border-line bg-white py-14 sm:py-20">
    <div class="shell">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p class="section-label">ONE LINK, MANY SCREENS</p>
          <h2 class="mt-2 font-display text-2xl font-black tracking-[-0.03em] text-ink sm:text-3xl">
            一条链接，覆盖你常用的平台
          </h2>
        </div>
        <p class="max-w-sm text-[12px] leading-5 text-slate-400">
          yt-dlp 社区持续维护 1800+ 站点解析规则。
          页面展示的是最常用的平台，不构成对特定站点的版权授权。
        </p>
      </div>

      <div class="relative mt-7 overflow-hidden">
        <div class="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-white to-transparent" />
        <div class="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-white to-transparent" />
        <div class="marquee-track flex w-max animate-marquee gap-2.5">
          <div v-for="group in 2" :key="group" class="flex shrink-0 gap-2.5" :aria-hidden="group === 2">
            <div
              v-for="platform in platforms"
              :key="`${group}-${platform.name}`"
              class="flex items-center gap-2.5 rounded-full border border-line bg-white px-3.5 py-2 shadow-[0_4px_16px_-12px_rgba(10,16,32,.2)]"
            >
              <span
                class="flex h-6 w-6 items-center justify-center rounded-lg text-[10px] font-black"
                :class="platform.dark ? 'text-ink' : 'text-white'"
                :style="{ background: platform.color }"
              >
                {{ platform.mark }}
              </span>
              <span class="whitespace-nowrap text-[11px] font-bold text-ink">{{ platform.name }}</span>
              <span class="whitespace-nowrap text-[9px] font-medium text-slate-400">{{ platform.kind }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-6 flex flex-wrap items-center justify-center gap-3 text-[11px] text-slate-400">
        <span class="inline-flex items-center gap-1.5">
          <span class="h-1.5 w-1.5 rounded-full bg-cobalt-500" />
          解析规则由社区持续更新
        </span>
        <span class="h-1 w-1 rounded-full bg-slate-300" />
        <span>实际可用性取决于平台与网络环境</span>
      </div>
    </div>
  </section>
</template>
