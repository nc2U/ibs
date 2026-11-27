<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useStore } from '@/store'
import { usePerms } from '@/composables/usePerms.ts'
import { cutString } from '@/utils/baseMixins.ts'
import type { ConsultationLog } from '@/store/types/contract'
import ConsultationDetail from './ConsultationDetail.vue'
import ConsultationEditForm from './ConsultationEditForm.vue'

const store = useStore()
const isDark = computed(() => store.theme === 'dark')
const { can, PERM } = usePerms()
const canContractUpdate = computed(() => can(PERM.CONTRACT_UPDATE))

// Props
const props = defineProps<{
  log: ConsultationLog
}>()

// Events
const emit = defineEmits<{
  edit: [log: ConsultationLog]
  delete: [pk: number]
}>()

// 확장 상태
const isExpanded = ref(false)

// 수정 모드
const editingLog = ref<ConsultationLog | null>(null)

// 확장 토글
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
  if (!isExpanded.value) {
    editingLog.value = null
  }
}

// 수정 토글
const toggleEdit = () => {
  if (editingLog.value) {
    cancelEdit()
  } else {
    editingLog.value = { ...props.log }
    isExpanded.value = true
  }
}

// 수정 취소
const cancelEdit = () => {
  editingLog.value = null
  isExpanded.value = false
}

// 수정 저장
const saveEdit = (log: ConsultationLog) => {
  emit('edit', log)
  editingLog.value = null
  isExpanded.value = false
}

// 삭제
const handleDelete = () => {
  if (props.log.pk) emit('delete', props.log.pk)
}

// 중요도별 색상
const priorityColorMap: Record<string, string> = {
  low: 'info',
  normal: 'success',
  high: 'warning',
  urgent: 'danger',
}
const getPriorityColor = (priority: string) => priorityColorMap[priority] || 'default'

// 상태별 색상
const statusColorMap: Record<string, string> = {
  '1': 'warning',
  '2': 'primary',
  '3': 'success',
  '4': 'secondary',
}
const getStatusColor = (status: string) => statusColorMap[status] || 'default'
</script>

<template>
  <!-- 메인 행 -->
  <CTableRow @click="toggleExpand" class="pointer">
    <CTableDataCell class="text-center">
      <div class="d-flex align-items-center justify-content-center gap-1">
        <v-icon v-if="log.is_important" icon="mdi-star" color="warning" size="18" />
        {{ log.consultation_date }}
      </div>
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <v-chip size="x-small" :rounded="0">{{ log.channel_display }}</v-chip>
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <v-chip size="x-small" :rounded="0">{{ log.category_display }}</v-chip>
    </CTableDataCell>
    <CTableDataCell>
      {{ cutString(log.title, 11) }}
      <v-chip :color="getPriorityColor(log.priority)" size="x-small">
        {{ log.priority_display }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <v-chip :color="getStatusColor(log.status)" size="x-small" :rounded="0">
        {{ log.status_display }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell class="text-end py-0">
      <v-btn
        v-if="canContractUpdate"
        size="x-small"
        icon="mdi-pencil"
        variant="text"
        color="success"
        @click.stop="toggleEdit"
      />
      <v-btn
        v-if="canContractUpdate"
        size="x-small"
        icon="mdi-trash-can-outline"
        variant="text"
        color="grey"
        @click.stop="handleDelete"
      />
    </CTableDataCell>
  </CTableRow>

  <!-- 확장 행 -->
  <CTableRow v-if="isExpanded">
    <CTableDataCell colspan="6" :class="isDark ? 'bg-dark' : 'bg-yellow-lighten-5'">
      <!-- 수정 모드 -->
      <ConsultationEditForm
        v-if="editingLog"
        :log="editingLog"
        @save="saveEdit"
        @cancel="cancelEdit"
      />

      <!-- 상세보기 모드 -->
      <ConsultationDetail v-else :log="log" />
    </CTableDataCell>
  </CTableRow>
</template>
