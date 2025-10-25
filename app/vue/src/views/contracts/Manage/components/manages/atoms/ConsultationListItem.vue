<script lang="ts" setup>
import { ref } from 'vue'
import { cutString } from '@/utils/baseMixins.ts'
import type { ConsultationLog } from '@/store/types/contract'
import ConsultationDetail from './ConsultationDetail.vue'
import ConsultationEditForm from './ConsultationEditForm.vue'

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

// 수정 시작
const startEdit = () => {
  editingLog.value = { ...props.log }
  isExpanded.value = true
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
  emit('delete', props.log.pk!)
}

// 상태별 색상
const getStatusColor = (status: string) => {
  switch (status) {
    case '1':
      return 'warning'
    case '2':
      return 'primary'
    case '3':
      return 'success'
    case '4':
      return 'secondary'
    default:
      return 'default'
  }
}
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
      <v-chip size="x-small">{{ log.channel_display }}</v-chip>
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <v-chip size="x-small">{{ log.category_display }}</v-chip>
    </CTableDataCell>
    <CTableDataCell>{{ cutString(log.title, 11) }}</CTableDataCell>
    <CTableDataCell class="text-center">
      <v-chip :color="getStatusColor(log.status)" size="small">
        {{ log.status_display }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <v-btn
        size="x-small"
        icon="mdi-pencil"
        variant="text"
        color="success"
        @click.stop="startEdit"
      />
      <v-btn
        size="x-small"
        icon="mdi-delete"
        variant="text"
        color="grey"
        @click.stop="handleDelete"
      />
    </CTableDataCell>
  </CTableRow>

  <!-- 확장 행 -->
  <CTableRow v-if="isExpanded">
    <CTableDataCell colspan="6" class="bg-yellow-lighten-5">
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

<style scoped>
.pointer {
  cursor: pointer;
}
</style>
