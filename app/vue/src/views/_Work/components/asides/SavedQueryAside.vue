<script lang="ts" setup>
import { computed, onMounted, type PropType, ref, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useInform } from '@/store/pinia/work_inform'
import type { CustomQuery } from '@/store/types/work_inform'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

type TargetType = 'project' | 'meeting' | 'issue' | 'calendar'

const SYSTEM_QUERY_PKS = [1, 2, 3, 4, 5, 6]

const props = defineProps({
  targetType: { type: String as PropType<TargetType>, required: true },
  activeQueryId: { type: Number as PropType<number | null>, default: null },
  canProjectPubQuery: { type: Boolean, default: false },
})

const emit = defineEmits(['on-query-click', 'on-reset-query'])

const refConfirmDelete = ref<InstanceType<typeof ConfirmModal> | null>(null)

const accStore = useAccount()
const informStore = useInform()

const myQueries = computed(() =>
  informStore.myQueries.filter(q => q.target_type === props.targetType),
)
const pubQueries = computed(() =>
  informStore.pubQueries.filter(q => q.target_type === props.targetType),
)

const canDeletePublicQuery = (q: CustomQuery) =>
  !SYSTEM_QUERY_PKS.includes(q.pk) && (props.canProjectPubQuery || q.user === accStore.userInfo?.pk)

const delPk = ref<number | null>(null)
const delName = ref('')
const onDeleteQuery = (query: CustomQuery, event: Event) => {
  event.stopPropagation()
  delPk.value = query.pk
  delName.value = query.name
  refConfirmDelete.value?.callModal()
}

const onDeleteConfirm = async () => {
  if (delPk.value === null) return
  const targetPk = delPk.value
  const deleted = await informStore.deleteQuery(targetPk)
  if (!deleted) return
  await informStore.fetchQueries({ targetType: props.targetType })
  refConfirmDelete.value?.close()
  delPk.value = null
  delName.value = ''
  if (props.activeQueryId === targetPk) {
    emit('on-reset-query')
  }
}

watch(
  () => props.targetType,
  async newType => {
    if (newType) {
      await informStore.fetchQueries({ targetType: newType })
    }
  },
)

onMounted(async () => {
  await informStore.fetchQueries({ targetType: props.targetType })
})
</script>

<template>
  <div class="mb-4 pe-4">
    <div v-if="myQueries.length" class="mb-4">
      <h6 class="text-subtitle-1 mb-2">내 검색 양식</h6>
      <v-list density="compact" nav class="pa-0 bg-transparent">
        <v-list-item
          v-for="q in myQueries"
          :key="q.pk"
          link
          @click="emit('on-query-click', q)"
          :active="activeQueryId === q.pk"
          active-color="blue-grey-lighten-2"
          class="rounded-lg mb-1 px-2 query-item pe-3"
        >
          <template v-slot:prepend>
            <v-icon icon="mdi-filter-variant" size="small" class="me-0" color="indigo" />
          </template>
          <v-list-item-title class="text-primary">{{ q.name }}</v-list-item-title>
          <template v-slot:append v-if="!SYSTEM_QUERY_PKS.includes(q.pk)">
            <v-btn
              icon="mdi-close-circle"
              size="small"
              variant="text"
              color="grey"
              class="delete-btn"
              @click="onDeleteQuery(q, $event)"
            />
          </template>
        </v-list-item>
      </v-list>
    </div>

    <v-divider v-if="myQueries.length" class="my-3" />

    <div class="mb-4">
      <h6 class="text-subtitle-1 mb-2">검색 양식</h6>
      <v-list density="compact" nav class="pa-0 bg-transparent">
        <v-list-item
          v-for="q in pubQueries"
          :key="q.pk"
          link
          @click="emit('on-query-click', q)"
          :active="activeQueryId === q.pk"
          active-color="blue-grey-lighten-2"
          class="rounded-lg mb-1 px-2 query-item pe-3"
        >
          <template v-slot:prepend>
            <v-icon icon="mdi-filter-variant" size="small" class="me-0" color="amber-darken-2" />
          </template>
          <v-list-item-title class="text-primary">{{ q.name }}</v-list-item-title>
          <template v-slot:append v-if="canDeletePublicQuery(q)">
            <v-btn
              icon="mdi-close-circle"
              size="small"
              variant="text"
              color="grey"
              class="delete-btn"
              @click="onDeleteQuery(q, $event)"
            />
          </template>
        </v-list-item>
        <div
          v-if="!pubQueries.length"
          class="text-caption text-grey ps-2 py-1"
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
      color="grey"
      min-height="38"
      size="small"
      class="mt-5"
      prepend-icon="mdi-filter-off"
      @click="emit('on-reset-query')"
    >
      검색 해제 (초기화)
    </v-btn>
  </div>

  <ConfirmModal ref="refConfirmDelete">
    <template #header>검색양식 삭제 확인</template>
    <template #default>
      <strong>{{ delName }}</strong> 검색양식을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="onDeleteConfirm">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
.query-item {
  min-height: 32px !important;
  height: 32px !important;
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
