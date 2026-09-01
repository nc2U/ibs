<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type ExecutiveRank } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import ExecutiveRankForm from './ExecutiveRankForm.vue'

defineProps({ executiveRank: { type: Object as PropType<ExecutiveRank>, required: true } })

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: ExecutiveRank) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="executiveRank" class="text-center">
    <CTableDataCell>{{ executiveRank.rank_order }}</CTableDataCell>
    <CTableDataCell>{{ executiveRank.code }}</CTableDataCell>
    <CTableDataCell>{{ executiveRank.name }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ executiveRank.role_desc }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>임원 직위 정보 등록</template>
    <template #default>
      <ExecutiveRankForm
        :executive-rank="executiveRank"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
