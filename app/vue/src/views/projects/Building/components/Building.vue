<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { write_project } from '@/utils/pageAuth'
import { type BuildingUnit } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  building: { type: Object as PropType<BuildingUnit>, required: true },
})
const emit = defineEmits(['on-update', 'on-delete'])

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive({ name: '' })

const formsCheck = computed(() => form.name === props.building?.name)

const formCheck = (bool: boolean) => {
  if (bool) onUpdateBuilding()
  return
}

const onUpdateBuilding = () => {
  if (write_project.value) {
    const pk = props.building?.pk
    emit('on-update', { ...{ pk }, ...form })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteBuilding = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  emit('on-delete', props.building?.pk)
  refConfirmModal.value.close()
}

const dataSetup = () => (form.name = props.building?.name as string)

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormInput
        v-model="form.name"
        maxlength="10"
        placeholder="동(건물)"
        @keypress.enter="formCheck(form.name !== building.name)"
      />
    </CTableDataCell>
    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateBuilding">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" @click="onDeleteBuilding">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 동(건물) 삭제</template>
    <template #default>
      이 동(건물)에 종속된 유니트(호수) 데이터가 있는 경우 해당 데이터를 모두 제거한 후 삭제가능
      합니다. 해당 동(건물)을 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
