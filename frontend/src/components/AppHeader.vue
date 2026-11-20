<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowUpRight, Code2, Menu, X } from '@lucide/vue'
import BrandMark from './BrandMark.vue'

const emit = defineEmits(['search'])
const scrolled = ref(false)
const menuOpen = ref(false)

const links = [
  { label: '能力', href: '#features' },
  { label: 'AI 精读', href: '#ai' },
  { label: '支持平台', href: '#platforms' },
  { label: '定价', href: '#pricing' },
]

function onScroll() {
  scrolled.value = window.scrollY > 12
}

function goSearch() {
  menuOpen.value = false
  emit('search')
}

function closeMenu() {
  menuOpen.value = false
}

watch(menuOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  document.body.style.overflow = ''
})
</script>

<template>
  <header
    class="sticky top-0 z-50 border-b transition duration-300"
    :class="scrolled || menuOpen ? 'border-line/90 bg-white/85 shadow-[0_8px_30px_-24px_rgba(10,16,32,.4)] backdrop-blur-xl' : 'border-transparent bg-paper/70 backdrop-blur-md'"
  >
    <div class="shell flex h-16 items-center justify-between gap-4">
      <a href="#" class="shrink-0" aria-label="片匣首页" @click.prevent="emit('search')">
        <BrandMark />
      </a>

      <nav class="hidden items-center gap-1 lg:flex" aria-label="主导航">
        <a
          v-for="link in links"
          :key="link.href"
          :href="link.href"
          class="rounded-full px-3.5 py-2 text-[13px] font-medium text-slate-500 transition hover:bg-white hover:text-ink"
        >
          {{ link.label }}
        </a>
      </nav>

      <div class="hidden items-center gap-2 lg:flex">
        <a
          href="/api/docs"
          target="_blank"
          rel="noopener noreferrer"
          class="btn-ghost text-[13px]"
          title="API 文档"
        >
          <Code2 :size="15" />
          API
        </a>
        <button type="button" class="btn-primary !px-4 !py-2.5 text-[13px]" @click="goSearch">
          免费解析
          <ArrowUpRight :size="15" :stroke-width="2.4" />
        </button>
      </div>

      <button
        type="button"
        class="flex h-10 w-10 items-center justify-center rounded-full border border-line bg-white text-ink lg:hidden"
        :aria-expanded="menuOpen"
        :aria-label="menuOpen ? '关闭菜单' : '打开菜单'"
        @click="menuOpen = !menuOpen"
      >
        <X v-if="menuOpen" :size="19" />
        <Menu v-else :size="19" />
      </button>
    </div>

    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="-translate-y-2 opacity-0"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="-translate-y-2 opacity-0"
    >
      <div v-if="menuOpen" class="border-t border-line bg-white/95 px-5 pb-5 pt-3 backdrop-blur-xl lg:hidden">
        <nav class="grid gap-1" aria-label="移动端导航">
          <a
            v-for="link in links"
            :key="link.href"
            :href="link.href"
            class="rounded-xl px-3 py-3 text-sm font-semibold text-slate-700 transition hover:bg-paper"
            @click="closeMenu"
          >
            {{ link.label }}
          </a>
          <a
            href="/api/docs"
            target="_blank"
            rel="noopener noreferrer"
            class="rounded-xl px-3 py-3 text-sm font-semibold text-slate-700 transition hover:bg-paper"
          >
            API 文档
          </a>
        </nav>
        <button type="button" class="btn-primary mt-4 w-full" @click="goSearch">
          免费解析
          <ArrowUpRight :size="16" />
        </button>
      </div>
    </Transition>
  </header>
</template>
