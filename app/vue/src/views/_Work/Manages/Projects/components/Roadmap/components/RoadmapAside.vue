<script lang="ts" setup>
import { ref, type PropType, watch } from 'vue'
import type { Version } from '@/store/types/work_project.ts'
import type { Tracker } from '@/store/types/work_issue.ts'

const props = defineProps({
  trackers: {
    type: Array as PropType<Tracker[] | { pk: number; name: string; description?: string }[]>,
    default: () => [],
  },
  versionList: { type: Array as PropType<Version[]>, default: () => [] },
  completed: { type: Boolean, default: false },
  selectedTrackers: { type: Array as PropType<number[]>, default: () => [] },
  selectedVersionId: { type: Number as PropType<number | null>, default: null },
})

const emit = defineEmits(['apply-filter', 'select-version'])

const isCompleted = ref(props.completed)
const selectedTrackerIds = ref<number[]>([...props.selectedTrackers])

watch(
  () => props.completed,
  val => {
    isCompleted.value = val
  },
)

watch(
  () => props.selectedTrackers,
  val => {
    selectedTrackerIds.value = [...val]
  },
)

const toggleTracker = (trackerId: number) => {
  const idx = selectedTrackerIds.value.indexOf(trackerId)
  if (idx > -1) {
    selectedTrackerIds.value.splice(idx, 1)
  } else {
    selectedTrackerIds.value.push(trackerId)
  }
}

const applyFilter = () => {
  emit('apply-filter', {
    completed: isCompleted.value,
    trackerIds: [...selectedTrackerIds.value],
  })
}

const scrollToVersion = (verId?: number) => {
  if (!verId) return
  emit('select-version', verId)
  const el = document.getElementById(`version-${verId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<template>
  <div class="roadmap-aside pr-2">
    <!-- 1. 필터 및 옵션 영역 -->
    <div class="mb-4">
      <h6 class="text-subtitle-1 font-weight-bold mb-2">
        <v-icon icon="mdi-filter-variant" size="small" class="mr-1" />
        로드맵 설정
      </h6>

      <!-- 유형별 필터 -->
      <div v-if="trackers.length" class="mb-3">
        <div class="text-caption font-weight-bold text-grey-darken-2 mb-1">유형</div>
        <div v-for="tracker in trackers" :key="tracker.pk" class="form-check mb-1">
          <input
            :id="`tracker-filter-${tracker.pk}`"
            class="form-check-input"
            type="checkbox"
            :checked="selectedTrackerIds.includes(tracker.pk)"
            @change="toggleTracker(tracker.pk)"
          />
          <label :for="`tracker-filter-${tracker.pk}`" class="form-check-label text-caption pointer">
            {{ tracker.name }}
          </label>
        </div>
      </div>

      <!-- 완료된 단계 보기 토글 -->
      <div class="mb-3">
        <div class="form-check">
          <input
            id="completed-versions-toggle"
            v-model="isCompleted"
            class="form-check-input"
            type="checkbox"
          />
          <label for="completed-versions-toggle" class="form-check-label text-caption pointer">
            완료된 단계 포함
          </label>
        </div>
      </div>

      <div class="mb-4">
        <v-btn color="blue-grey-darken-1" size="small" variant="flat" @click="applyFilter">
          적용
        </v-btn>
      </div>
    </div>

    <v-divider class="my-3" />

    <!-- 2. 단계(버전) 색인 / 바로가기 목차 -->
    <div v-if="versionList.length">
      <h6 class="text-subtitle-1 font-weight-bold mb-2">
        <v-icon icon="mdi-format-list-bulleted" size="small" class="mr-1" />
        단계 색인
      </h6>
      <ul class="list-unstyled version-index-list pl-1">
        <li v-for="ver in versionList" :key="ver.pk" class="mb-1">
          <a
            href="javascript:void(0)"
            class="text-decoration-none text-body-2 version-link d-flex align-items-center justify-content-between px-2 py-1 rounded"
            :class="{ 'active-version': selectedVersionId === ver.pk }"
            @click="scrollToVersion(ver.pk)"
          >
            <span class="text-truncate mr-1">
              <v-icon
                :icon="ver.status === '3' ? 'mdi-checkbox-marked-circle' : 'mdi-target'"
                :color="ver.status === '3' ? 'grey' : 'green-darken-1'"
                size="x-small"
                class="mr-1"
              />
              {{ ver.name }}
            </span>
            <span class="text-caption text-grey text-no-wrap">
              {{ ver.done_ratio?.toFixed(0) ?? 0 }}%
            </span>
          </a>
        </li>
      </ul>
    </div>
    <div v-else class="text-caption text-grey">표시할 단계가 없습니다.</div>
  </div>
</template>

<style scoped>
.pointer {
  cursor: pointer;
}
.version-link {
  transition: background-color 0.2s;
}
.version-link:hover {
  text-decoration: underline !important;
  color: var(--v-theme-primary, #1976d2) !important;
  background-color: rgba(0, 0, 0, 0.04);
}
.version-link.active-version {
  background-color: #e3f2fd;
  color: #0d47a1 !important;
  font-weight: bold;
}
:global(body.dark-theme) .version-link:hover {
  background-color: rgba(255, 255, 255, 0.08);
}
:global(body.dark-theme) .version-link.active-version {
  background-color: rgba(13, 110, 253, 0.25) !important;
  color: #90caf9 !important;
}
.version-index-list {
  padding-left: 0;
  list-style: none;
}
</style>
