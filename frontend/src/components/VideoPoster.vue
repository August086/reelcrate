<script setup>
import { ref, watch } from 'vue'
import { Calendar, Clock3, ExternalLink, Eye, Play, UserRound } from '@lucide/vue'
import CinemaStill from './CinemaStill.vue'
import { formatCount, formatDuration, shortDate } from '../lib/format'

const props = defineProps({
  video: { type: Object, required: true },
})
const thumbFailed = ref(false)

watch(
  () => props.video?.thumbnail,
  () => {
    thumbFailed.value = false
  },
)
</script>

<template>
  <div>
    <div class="relative overflow-hidden rounded-[24px] border border-white/10 bg-ink p-1.5 shadow-[0_36px_80px_-46px_rgba(10,16,32,.9)]">
      <div class="relative aspect-[16/9] overflow-hidden rounded-[19px] bg-night">
        <img
          v-if="video.thumbnail && !thumbFailed"
          :src="video.thumbnail"
          :alt="`${video.title} 封面`"
          class="h-full w-full object-cover"
          loading="lazy"
          referrerpolicy="no-referrer"
          @error="thumbFailed = true"
        />
        <CinemaStill v-else />
        <div class="absolute inset-0 bg-gradient-to-t from-black/78 via-black/6 to-black/16" />

        <div class="absolute inset-y-0 left-0 w-2 bg-black/45 film-perf opacity-70" />
        <div class="absolute inset-y-0 right-0 w-2 bg-black/45 film-perf opacity-70" />

        <div class="absolute left-4 top-4 flex flex-wrap items-center gap-2">
          <span class="inline-flex items-center gap-1.5 rounded-full bg-black/45 px-2.5 py-1 text-[10px] font-bold tracking-wide text-white/90 backdrop-blur">
            <span class="h-1.5 w-1.5 rounded-full bg-cobalt-400" />
            {{ video.platform }}
          </span>
          <span
            v-if="video.duration"
            class="inline-flex items-center gap-1 rounded-full bg-black/45 px-2.5 py-1 font-mono text-[10px] font-semibold text-white/80 backdrop-blur"
          >
            <Clock3 :size="11" />
            {{ formatDuration(video.duration) }}
          </span>
        </div>

        <a
          :href="video.webpage_url"
          target="_blank"
          rel="noopener noreferrer"
          class="group absolute inset-0 flex items-center justify-center"
          :aria-label="`在 ${video.platform} 查看原视频`"
        >
          <span class="flex h-16 w-16 items-center justify-center rounded-full border border-white/25 bg-white/12 text-white shadow-xl backdrop-blur-md transition duration-300 group-hover:scale-105 group-hover:bg-cobalt-500 group-hover:bg-opacity-90">
            <Play :size="24" class="ml-1" fill="currentColor" />
          </span>
        </a>

        <div class="absolute bottom-4 left-4 right-4 flex items-end justify-between gap-3">
          <div class="min-w-0">
            <p class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/45">
              <span class="h-px w-4 bg-white/30" />
              已解析
            </p>
            <p class="mt-1 truncate text-[12px] font-semibold text-white/75">{{ video.uploader || '未知作者' }}</p>
          </div>
          <a
            :href="video.webpage_url"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex shrink-0 items-center gap-1 rounded-full border border-white/15 bg-black/30 px-2.5 py-1.5 text-[10px] font-semibold text-white/75 backdrop-blur transition hover:bg-black/50 hover:text-white"
          >
            原视频
            <ExternalLink :size="11" />
          </a>
        </div>
      </div>
    </div>

    <div class="mt-4 px-1">
      <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] font-medium text-slate-400">
        <span class="inline-flex items-center gap-1 text-cobalt-600">
          <span class="h-1.5 w-1.5 rounded-full bg-cobalt-500" />
          {{ video.platform }}
        </span>
        <span v-if="video.upload_date" class="inline-flex items-center gap-1">
          <Calendar :size="12" />
          {{ shortDate(video.upload_date) }}
        </span>
        <span v-if="video.view_count" class="inline-flex items-center gap-1">
          <Eye :size="12" />
          {{ formatCount(video.view_count) }} 播放
        </span>
      </div>

      <h2 class="mt-2 line-clamp-3 font-display text-[20px] font-black leading-[1.42] tracking-[-0.03em] text-ink">
        {{ video.title }}
      </h2>

      <p v-if="video.uploader" class="mt-2 inline-flex items-center gap-1.5 text-[12px] text-slate-400">
        <UserRound :size="13" />
        {{ video.uploader }}
      </p>
    </div>
  </div>
</template>
