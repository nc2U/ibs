<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, watch, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms.ts'
import { type BuildingUnit } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  building: { type: Object as PropType<BuildingUnit>, required: true },
})
const emit = defineEmits<{
  (e: 'on-update', payload: { pk?: number; name: string }): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive({ name: '' })

// 빈 값이거나 변경되지 않은 경우 true (버튼 비활성화)
const formsCheck = computed(() => !form.name.trim() || form.name.trim() === props.building?.name)

const onUpdateBuilding = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    emit('on-update', { pk: props.building?.pk, name: form.name.trim() })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteBuilding = () => {
  if (isSuperAuth.value) {
    refConfirmModal.value.callModal()
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.building?.pk) {
    emit('on-delete', props.building.pk)
  }
  refConfirmModal.value.close()
}

const dataSetup = () => {
  form.name = props.building?.name ?? ''
}

onBeforeMount(() => dataSetup())
watch(
  () => props.building?.name,
  val => {
    form.name = val ?? ''
  },
)
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormInput
        v-model="form.name"
        maxlength="10"
        placeholder="동(건물)"
        :disabled="!canProjectUpdate"
        @keydown.enter="onUpdateBuilding"
      />
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateBuilding">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteBuilding"> 삭제 </v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 동(건물) 삭제</template>
    <template #default>
      이 동(건물)에 종속된 유니트(호수) 데이터가 있는 경우 해당 데이터를 모두 제거한 후
      삭제가능합니다. 해당 동(건물)을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
