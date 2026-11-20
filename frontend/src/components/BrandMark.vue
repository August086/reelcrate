<script setup>
defineProps({
  markOnly: { type: Boolean, default: false },
  light: { type: Boolean, default: false },
})
</script>

<template>
  <span class="inline-flex items-center gap-2.5">
    <svg
      class="h-9 w-9 shrink-0 drop-shadow-[0_6px_14px_rgba(23,119,255,0.28)]"
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
    >
      <rect width="40" height="40" rx="12" fill="#1777FF" />
      <rect width="40" height="40" rx="12" fill="url(#brand-gloss)" />
      <path
        d="M11.5 12.5h17a3 3 0 0 1 3 3v9.4a3 3 0 0 1-3 3h-17a3 3 0 0 1-3-3v-9.4a3 3 0 0 1 3-3Z"
        stroke="white"
        stroke-width="1.6"
        stroke-opacity=".88"
      />
      <path d="M10 17.2h20M10 22.8h20" stroke="white" stroke-width="1.2" stroke-opacity=".38" />
      <path d="m17.8 17.2 6.8 3.8-6.8 3.8v-7.6Z" fill="white" />
      <circle cx="31.6" cy="9.2" r="2.1" fill="#F5B84B" />
      <defs>
        <linearGradient id="brand-gloss" x1="4" y1="0" x2="37" y2="40" gradientUnits="userSpaceOnUse">
          <stop stop-color="white" stop-opacity=".18" />
          <stop offset=".52" stop-color="white" stop-opacity="0" />
          <stop offset="1" stop-color="#052C83" stop-opacity=".25" />
        </linearGradient>
      </defs>
    </svg>
    <span v-if="!markOnly" class="flex flex-col leading-none">
      <span
        class="font-display text-[18px] font-black tracking-[-0.055em]"
        :class="light ? 'text-white' : 'text-ink'"
        >ReelCrate</span
      >
      <span
        class="mt-1 text-[7px] font-bold uppercase tracking-[0.22em]"
        :class="light ? 'text-white/45' : 'text-slate-400'"
        >Video Vault</span
      >
    </span>
  </span>
</template>
