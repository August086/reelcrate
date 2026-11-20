<template>
  <svg
    viewBox="0 0 640 360"
    preserveAspectRatio="xMidYMid slice"
    class="h-full w-full"
    aria-hidden="true"
  >
    <defs>
      <linearGradient id="still-sky" x1="320" y1="0" x2="380" y2="320" gradientUnits="userSpaceOnUse">
        <stop stop-color="#07112A" />
        <stop offset=".52" stop-color="#0C2A5B" />
        <stop offset="1" stop-color="#123F7A" />
      </linearGradient>
      <linearGradient id="still-haze" x1="60" y1="250" x2="600" y2="180" gradientUnits="userSpaceOnUse">
        <stop stop-color="#1777FF" stop-opacity=".05" />
        <stop offset=".5" stop-color="#4A94FF" stop-opacity=".35" />
        <stop offset="1" stop-color="#1777FF" stop-opacity=".02" />
      </linearGradient>
      <radialGradient id="still-sun" cx="0" cy="0" r="1" gradientTransform="translate(468 112) rotate(90) scale(88)">
        <stop stop-color="#FFD58A" stop-opacity=".95" />
        <stop offset=".44" stop-color="#F5B84B" stop-opacity=".38" />
        <stop offset="1" stop-color="#F5B84B" stop-opacity="0" />
      </radialGradient>
      <linearGradient id="still-mountain" x1="320" y1="190" x2="320" y2="360" gradientUnits="userSpaceOnUse">
        <stop stop-color="#0A1E3D" />
        <stop offset="1" stop-color="#060B18" />
      </linearGradient>
      <linearGradient id="still-foreground" x1="320" y1="286" x2="320" y2="360" gradientUnits="userSpaceOnUse">
        <stop stop-color="#040812" />
        <stop offset="1" stop-color="#02040A" />
      </linearGradient>
      <pattern id="still-grain" width="6" height="6" patternUnits="userSpaceOnUse">
        <circle cx="1" cy="2" r=".6" fill="#fff" fill-opacity=".16" />
        <circle cx="4" cy="5" r=".45" fill="#fff" fill-opacity=".1" />
      </pattern>
    </defs>

    <rect width="640" height="360" fill="url(#still-sky)" />
    <circle cx="468" cy="112" r="88" fill="url(#still-sun)" />
    <circle cx="468" cy="112" r="27" fill="#F8C96D" fill-opacity=".92" />
    <path
      d="M0 250c80-20 124-12 186 18 55 26 97 20 144-7 82-48 158-44 226-10 34 17 58 26 84 30v79H0v-110Z"
      fill="url(#still-haze)"
    />
    <path d="m0 254 108-67 53 37 72-51 98 65 91-52 96 58 74-44 48 29v131H0V254Z" fill="#0A2043" fill-opacity=".92" />
    <path d="m0 286 90-48 65 28 87-46 92 43 86-38 99 36 61-23 60 34v88H0v-74Z" fill="url(#still-mountain)" />
    <path d="M0 318c96-26 159-15 246 2 86 17 171 18 238-7 56-21 104-18 156-2v49H0v-42Z" fill="url(#still-foreground)" />
    <path d="M0 318c96-26 159-15 246 2 86 17 171 18 238-7 56-21 104-18 156-2" fill="none" stroke="#4A94FF" stroke-opacity=".18" />
    <rect width="640" height="360" fill="url(#still-grain)" opacity=".5" />
    <rect width="640" height="360" fill="none" stroke="white" stroke-opacity=".06" />
  </svg>
</template>
