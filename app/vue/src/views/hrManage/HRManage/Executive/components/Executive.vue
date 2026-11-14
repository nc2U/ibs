<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { type Executive } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import ExecutiveForm from './ExecutiveForm.vue'

defineProps<{ executive: Executive }>()
const emit = defineEmits<{
  (e: 'multi-submit', payload: Executive): void
  (e: 'on-delete', pk: number): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const showDetail = () => updateFormModal.value?.callModal()
const multiSubmit = (payload: Executive) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="executive" class="text-center">
    <CTableDataCell>
      <a href="#" role="button" @click.prevent="showDetail">{{
        executive.full_name
      }}</a>
    </CTableDataCell>
    <CTableDataCell>{{ executive.rank_name || '-' }}</CTableDataCell>
    <CTableDataCell>{{ executive.executive_type_desc }}</CTableDataCell>
    <CTableDataCell>
      <v-chip :color="executive.is_registered ? 'info' : 'secondary'" variant="flat" size="x-small">
        {{ executive.is_registered ? '등기' : '비등기' }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell>
      <v-chip :color="executive.is_standing ? 'success' : 'warning'" variant="flat" size="x-small">
        {{ executive.is_standing ? '상근' : '비상근' }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell>{{ executive.represent_type_desc }}</CTableDataCell>
    <CTableDataCell>{{ executive.term_start || '-' }}</CTableDataCell>
    <CTableDataCell>{{ executive.term_end || '-' }}</CTableDataCell>
    <CTableDataCell class="text-start">{{ executive.note || '-' }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>임원 재임 정보 상세 및 수정</template>
    <template #default>
      <ExecutiveForm
        :executive="executive"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
