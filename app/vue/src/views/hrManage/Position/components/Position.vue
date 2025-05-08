<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useCompany } from '@/store/pinia/company'
import { type Position } from '@/store/types/company'
import { write_human_resource } from '@/utils/pageAuth'
import FormModal from '@/components/Modals/FormModal.vue'
import PositionForm from './PositionForm.vue'

const props = defineProps({
  position: { type: Object as PropType<Position>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const updateFormModal = ref()

const comStore = useCompany()
const getPkGrades = computed(() => comStore.getPkGrades)

const grades = computed(() => {
  const ids = props.position.grades
  return getPkGrades.value
    .filter(g => ids.includes(g.value as number))
    .map(g => g.label)
    .join(', ')
})

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: Position) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow class="text-center">
    <CTableDataCell>{{ position.pk }}</CTableDataCell>
    <CTableDataCell>{{ position.name }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ grades }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ position.desc }}</CTableDataCell>
    <CTableDataCell v-if="write_human_resource">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>직급 정보 등록</template>
    <template #default>
      <PositionForm
        :position="position"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
