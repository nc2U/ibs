<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Executive } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import ExecutiveForm from './ExecutiveForm.vue'

defineProps({
  executive: { type: Object as PropType<Executive>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: Executive) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="executive" class="text-center">
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">{{ executive.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell>{{ executive.rank_name || '-' }}</CTableDataCell>
    <CTableDataCell>{{ executive.director_type_desc }}</CTableDataCell>
    <CTableDataCell>
      <CBadge :color="executive.is_registered ? 'primary' : 'secondary'">
        {{ executive.is_registered ? '등기' : '비등기' }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell>
      <CBadge :color="executive.is_standing ? 'success' : 'warning'">
        {{ executive.is_standing ? '상근' : '비상근' }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ executive.represent_type_desc }}</CTableDataCell>
    <CTableDataCell>{{ executive.term_start || '-' }}</CTableDataCell>
    <CTableDataCell>{{ executive.term_end || '-' }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ executive.note || '-' }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>임원 재임 정보 등록</template>
    <template #default>
      <ExecutiveForm
        :executive="executive"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
