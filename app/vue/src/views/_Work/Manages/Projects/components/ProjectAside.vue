<script lang="ts" setup>
import type { PropType } from 'vue'
import type { CustomQuery } from '@/store/types/work_inform.ts'

defineProps({
  myQueries: { type: Array as PropType<CustomQuery[]>, default: () => [] },
  publicQueries: { type: Array as PropType<CustomQuery[]>, default: () => [] },
  activeQueryId: { type: Number, default: null },
  canProjectPubQuery: { type: Boolean, default: false },
})

const emit = defineEmits(['on-query-click', 'on-delete-query', 'on-reset-query'])
</script>

<template>
  <div class="mb-4">
    <div class="mb-4">
      <h6 class="text-subtitle-1 mb-2 strong">내 검색 양식</h6>
      <v-list density="compact" nav class="pa-0 bg-transparent">
        <v-list-item
          v-for="q in myQueries"
          :key="q.pk"
          link
          @click="emit('on-query-click', q)"
          :active="activeQueryId === q.pk"
          active-color="indigo"
          class="rounded-lg mb-1 px-2 query-item pr-3"
        >
          <template v-slot:prepend>
            <v-icon icon="mdi-filter-variant" size="small" class="mr-1" color="indigo" />
          </template>
          <v-list-item-title style="font-size: 1em">{{ q.name }}</v-list-item-title>
          <template v-slot:append v-if="![1, 2].includes(q.pk)">
            <v-btn
              icon="mdi-close-circle"
              size="small"
              variant="text"
              color="grey"
              class="delete-btn"
              @click="emit('on-delete-query', q, $event)"
            />
          </template>
        </v-list-item>
        <div
          v-if="!myQueries.length"
          class="text-caption text-grey pl-2 py-1"
          style="font-size: 0.9rem"
        >
          저장된 개인 검색 양식이 없습니다.
        </div>
      </v-list>
    </div>

    <v-divider class="my-3" />

    <div class="mb-4">
      <h6 class="text-subtitle-1 mb-2 strong">공용 검색양식</h6>
      <v-list density="compact" nav class="pa-0 bg-transparent">
        <v-list-item
          v-for="q in publicQueries"
          :key="q.pk"
          link
          @click="emit('on-query-click', q)"
          :active="activeQueryId === q.pk"
          active-color="brown-darken-4"
          class="rounded-lg mb-1 px-2 query-item pr-3"
        >
          <template v-slot:prepend>
            <v-icon icon="mdi-filter-variant" size="small" class="mr-2" color="brown-darken-4" />
          </template>
          <v-list-item-title style="font-size: 1em">{{ q.name }}</v-list-item-title>
          <template v-slot:append v-if="canProjectPubQuery && ![1, 2].includes(q.pk)">
            <v-btn
              icon="mdi-close-circle"
              size="small"
              variant="text"
              color="grey"
              class="delete-btn"
              @click="emit('on-delete-query', q, $event)"
            />
          </template>
        </v-list-item>
        <div
          v-if="!publicQueries.length"
          class="text-caption text-grey pl-2 py-1"
          style="font-size: 0.9rem"
        >
          저장된 공용 검색 양식이 없습니다.
        </div>
      </v-list>
    </div>

    <v-btn
      v-if="activeQueryId !== null"
      block
      variant="tonal"
      color="blue-grey"
      min-height="36"
      size="small"
      class="mt-5"
      prepend-icon="mdi-filter-off"
      @click="emit('on-reset-query')"
    >
      필터 해제 (초기화)
    </v-btn>
  </div>
</template>

<style lang="scss" scoped>
.query-item {
  min-height: 36px !important;
  height: 36px !important;
  margin-bottom: 2px !important;

  :deep(.v-list-item__content) {
    align-self: center;
  }

  :deep(.v-list-item-title) {
    font-size: 1em !important;
    line-height: 1.2 !important;
  }

  :deep(.v-icon) {
    font-size: 16px !important;
  }

  .delete-btn {
    opacity: 0;
    transition: opacity 0.2s;
    width: 20px !important;
    height: 20px !important;
    min-width: auto !important;

    :deep(.v-btn__content) {
      font-size: 14px !important;
    }
  }

  &:hover {
    .delete-btn {
      opacity: 1;
    }
  }
}
</style>
