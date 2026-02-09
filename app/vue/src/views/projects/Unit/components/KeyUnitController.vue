<script lang="ts" setup>
import { computed, reactive, ref } from 'vue'
import { useProjectData, type CreateKeyUnit } from '@/store/pinia/project_data'
import { AlertLight } from '@/utils/cssMixins'
import { write_project } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ project: { type: Number, default: null } })

const projReset = () => {
  form.unit_type = null
  form.unit_code = ''
}

defineExpose({ projReset })

const refConfirmModal = ref()
const refAlertModal = ref()

const form = reactive<{ unit_type: number | null; unit_code: string }>({
  unit_type: null,
  unit_code: '',
})

const projectDataStore = useProjectData()
const unitTypeList = computed(() => projectDataStore.unitTypeList)
const keyUnitList = computed(() => projectDataStore.keyUnitList)

const filteredKeyUnits = computed(() => {
  if (!form.unit_type) return keyUnitList.value
  return keyUnitList.value.filter(ku => ku.unit_type === form.unit_type)
})

const typeName = (typeId: number) => {
  const t = unitTypeList.value.find(ut => ut.pk === typeId)
  return t ? t.name : ''
}

const typeSelect = () => {
  if (props.project) {
    projectDataStore.fetchKeyUnitList(props.project, form.unit_type || undefined)
  }
}

const unitRegister = () => {
  if (write_project.value) {
    if (!form.unit_type || !form.unit_code) return
    refConfirmModal.value.callModal()
  } else {
    refAlertModal.value.callModal()
  }
}

const emit = defineEmits(['key-unit-created'])

const modalAction = () => {
  if (props.project && form.unit_type && form.unit_code) {
    const payload: CreateKeyUnit = {
      project: props.project,
      unit_type: form.unit_type,
      unit_code: form.unit_code,
    }
    projectDataStore.createKeyUnit(payload).then(() => emit('key-unit-created'))
    form.unit_code = ''
  }
  refConfirmModal.value.close()
}

const deleteUnit = (pk: number) => {
  if (props.project)
    projectDataStore.deleteKeyUnit(pk, props.project, form.unit_type || undefined)
}
</script>

<template>
  <CCallout color="info" class="pb-2">
    <CRow>
      <CCol md="4" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">타입 선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect
              v-model.number="form.unit_type"
              :disabled="!project"
              @change="typeSelect"
            >
              <option value="">전체</option>
              <option v-for="type in unitTypeList" :key="type.pk" :value="type.pk">
                {{ type.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>

  <CCallout v-if="write_project" color="danger" class="pb-2">
    <CRow>
      <CCol md="4" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">타입 선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect v-model.number="form.unit_type" :disabled="!project">
              <option value="">---------</option>
              <option v-for="type in unitTypeList" :key="type.pk" :value="type.pk">
                {{ type.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="4" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">유닛 코드</CFormLabel>
          <CCol sm="8">
            <CFormInput
              v-model="form.unit_code"
              placeholder="유닛 코드 입력"
              maxlength="8"
              :disabled="!form.unit_type"
              @keydown.enter="unitRegister"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol md="4" class="mb-2">
        <v-btn
          color="primary"
          :disabled="!project || !form.unit_type || !form.unit_code"
          @click="unitRegister"
        >
          유닛 등록
        </v-btn>
      </CCol>
    </CRow>
  </CCallout>

  <CAlert v-if="write_project" :color="AlertLight" variant="solid">
    <strong>유닛 목록</strong> (총 {{ filteredKeyUnits.length }}건)
  </CAlert>

  <v-table density="compact">
    <thead>
      <tr>
        <th class="text-center" style="width: 60px">No</th>
        <th class="text-center">유닛 코드</th>
        <th class="text-center">타입</th>
        <th class="text-center">계약 상태</th>
        <th v-if="write_project" class="text-center" style="width: 80px">삭제</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(ku, i) in filteredKeyUnits" :key="ku.pk">
        <td class="text-center">{{ i + 1 }}</td>
        <td class="text-center">{{ ku.unit_code }}</td>
        <td class="text-center">{{ typeName(ku.unit_type) }}</td>
        <td class="text-center">
          <v-chip v-if="ku.contract" color="primary" size="small">계약</v-chip>
          <v-chip v-else color="grey" size="small">미계약</v-chip>
        </td>
        <td v-if="write_project" class="text-center">
          <v-btn
            icon
            size="x-small"
            color="error"
            variant="text"
            :disabled="!!ku.contract"
            @click="deleteUnit(ku.pk)"
          >
            <v-icon icon="mdi-trash-can-outline" />
          </v-btn>
        </td>
      </tr>
      <tr v-if="filteredKeyUnits.length === 0">
        <td :colspan="write_project ? 5 : 4" class="text-center text-grey py-4">
          등록된 유닛이 없습니다.
        </td>
      </tr>
    </tbody>
  </v-table>

  <ConfirmModal ref="refConfirmModal">
    <template #header>유닛 등록</template>
    <template #default>
      <p class="text-primary">
        <strong>유닛 코드: {{ form.unit_code }}</strong>
      </p>
      <p>상기 유닛 등록을 진행하시겠습니까?</p>
    </template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">등록</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
