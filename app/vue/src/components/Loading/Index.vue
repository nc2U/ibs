<script lang="ts" setup>
defineProps({
  active: { type: Boolean, default: false },
  message: { type: String, default: '데이터를 불러오는 중입니다...' },
  isFullPage: { type: Boolean, default: true },
  size: { type: [Number, String], default: 60 },
  width: { type: [Number, String], default: 2 },
})
</script>

<template>
  <div v-if="active" :class="['loading-container', isFullPage ? 'full-page' : 'inline-page']">
    <div class="loading-content d-flex flex-column align-center justify-center">
      <v-progress-circular indeterminate color="primary" :size="size" :width="width" />
      <div class="mt-4 loading-text text-subtitle-2 font-weight-medium">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

/* 전체 화면 오버레이 스타일 (Glassmorphism 투명도 및 블러 강도 완화) */
.loading-container.full-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
}

:global(body.dark-theme) .loading-container.full-page {
  background-color: rgba(26, 29, 39, 0.25) !important;
}

/* 컨테이너 내부 로컬 오버레이 스타일 */
.loading-container.inline-page {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.25);
  min-height: 250px;
}

:global(body.dark-theme) .loading-container.inline-page {
  background-color: rgba(35, 39, 54, 0.35) !important;
}

.loading-content {
  text-align: center;
}

.loading-text {
  color: #cccccc;
}

:global(body.dark-theme) .loading-text {
  color: #a6b0cf !important;
}
</style>
