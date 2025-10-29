<template>
  <!-- 글로벌 다운로드 인디케이터 -->
  <Teleport to="body">
    <div
      v-if="downloadState.isDownloading"
      class="download-overlay"
      role="dialog"
      aria-labelledby="download-title"
      aria-describedby="download-description"
    >
      <div class="download-modal">
        <div class="download-content">
          <!-- 로딩 아이콘 -->
          <div class="loading-icon">
            <svg class="animate-spin" width="48" height="48" viewBox="0 0 24 24" fill="none">
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-dasharray="32"
                stroke-dashoffset="32"
                class="spinner-circle"
              />
            </svg>
          </div>

          <!-- 다운로드 메시지 -->
          <h3 id="download-title" class="download-title">
            PDF 다운로드 중...
          </h3>

          <p id="download-description" class="download-description">
            {{ downloadState.fileName || '파일' }}을 준비하고 있습니다.
          </p>

          <!-- 진행률 바 -->
          <div class="progress-container">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: downloadState.progress + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ downloadState.progress }}%</span>
          </div>

          <!-- 힌트 텍스트 -->
          <p class="download-hint">
            잠시만 기다려주세요. 파일이 자동으로 다운로드됩니다.
          </p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { useDownload } from '@/composables/useDownload'

const { downloadState } = useDownload()
</script>

<style scoped>
.download-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.download-modal {
  background: white;
  border-radius: 12px;
  padding: 32px;
  min-width: 320px;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

.download-content {
  text-align: center;
}

.loading-icon {
  color: #3b82f6;
  margin-bottom: 20px;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

.spinner-circle {
  animation: dash 1.5s ease-in-out infinite;
}

.download-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.download-description {
  margin: 0 0 24px 0;
  color: #6b7280;
  font-size: 14px;
}

.progress-container {
  margin-bottom: 16px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.download-hint {
  margin: 0;
  font-size: 12px;
  color: #9ca3af;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 0, 32;
  }
  50% {
    stroke-dasharray: 16, 16;
  }
  100% {
    stroke-dasharray: 32, 0;
  }
}
</style>