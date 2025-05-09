<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { type BuildingUnit } from '@/store/types/project'
import { AlertLight, btnLight } from '@/utils/cssMixins'
import { write_project } from '@/utils/pageAuth'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['bldg-select', 'dong-register', 'unit-register'])

const projReset = () => {
  form.building = null
  reset(1)
}

defineExpose({ projReset })

const validated = ref(false)

const refBuildForm = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const bldgName = ref('')
const typeName = ref('')

const form = reactive({
  building: null,
  line: null,
  type: null,
  minFloor: null,
  maxFloor: null,
})

const warning = computed(() => !!form.maxFloor)

const typeNameLength = computed(() => {
  const typeNames = unitTypeList.value
    .map((t: { name: string }) => t.name)
    .map((t: string) => t.replace(/[^0-9a-zA-Z]/g, ''))
    .map((t: string) => t.length)
  return Math.max.apply({}, typeNames)
})

const maxUnits = computed(() =>
  Math.max.apply(
    {},
    unitTypeList.value.map((t: { num_unit: number }) => t.num_unit),
  ),
)

const projectDataStore = useProjectData()
const unitTypeList = computed(() => projectDataStore.unitTypeList)
const buildingList = computed(() => projectDataStore.buildingList)
const simpleFloors = computed(() => projectDataStore.simpleFloors)

const fetchNumUnitByType = (projId: number, unit_type: number) =>
  projectDataStore.fetchNumUnitByType(projId, unit_type)

watch(form, val => {
  if (!val.building) reset(1)
  else if (!val.line) reset(2)
  else if (!val.type) reset(3)
  else if (!val.minFloor) reset(4)
})

const dong = ref('')

const onSubmit = (event: Event) => {
  if (write_project.value) {
    const e = event.currentTarget as HTMLSelectElement
    if (!e.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

      validated.value = true
    } else {
      emit('dong-register', dong.value)
      dong.value = ''
      refBuildForm.value.close()
    }
  }
}

const reset = (n: number) => {
  if (n == 1) {
    form.line = null
    form.type = null
    form.minFloor = null
    form.maxFloor = null
  } else if (n == 2) {
    form.type = null
    form.minFloor = null
    form.maxFloor = null
  } else if (n == 3) {
    form.minFloor = null
    form.maxFloor = null
  } else {
    form.maxFloor = null
  }
}

const bldgSelect = (event: Event) => {
  const bdName = (event.target as HTMLSelectElement).value
    ? buildingList.value.filter(
        (b: BuildingUnit) => b.pk.toString() == (event.target as HTMLSelectElement).value,
      )[0].name
    : ''
  bldgName.value = bdName
  const bldg = {
    pk: (event.target as HTMLSelectElement).value,
    name: bdName,
  }
  emit('bldg-select', bldg)
}

const typeSelect = (event: Event) => {
  typeName.value = (event.target as HTMLSelectElement).value
    ? unitTypeList.value.filter(
        (t: { pk: number }) => t.pk.toString() == (event.target as HTMLSelectElement).value,
      )[0].name
    : ''
  fetchNumUnitByType(props.project, Number((event.target as HTMLSelectElement).value))
}

const unitRegister = () => {
  if (write_project.value) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    reset(1)
  }
}

const modalAction = () => {
  if (!form.maxFloor) form.maxFloor = form.minFloor
  emit('unit-register', {
    ...form,
    ...{
      typeName: typeName.value,
      maxLength: typeNameLength.value,
      maxUnits: maxUnits.value,
    },
    ...{ floors: simpleFloors.value },
  })
  refConfirmModal.value.close()
  reset(1)
}
</script>

<template>
  <CCallout color="info" class="pb-2">
    <CRow>
      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label"> 동(건물)선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect v-model.number="form.building" :disabled="!project" @change="bldgSelect">
              <option value>---------</option>
              <option v-for="bldg in buildingList" :key="bldg.pk" :value="bldg.pk">
                {{ bldg.name }}동
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>
      <CCol v-if="write_project" class="pt-1">
        <v-icon
          icon="mdi mdi-plus-thick"
          size="16"
          color="success"
          class="pointer"
          @click="refBuildForm.callModal()"
        />
      </CCol>
    </CRow>
  </CCallout>

  <CCallout v-if="write_project" color="danger" class="pb-2">
    <CRow>
      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label"> 등록라인</CFormLabel>
          <CCol sm="8">
            <CFormInput
              v-model.number="form.line"
              type="number"
              min="0"
              placeholder="등록할 라인 숫자 입력"
              :disabled="!form.building"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label"> 타입선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect v-model.number="form.type" :disabled="!form.line" @change="typeSelect">
              <option value>---------</option>
              <option v-for="type in unitTypeList" :key="type.pk" :value="type.pk">
                {{ type.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label"> 시작층</CFormLabel>
          <CCol sm="8">
            <CFormInput
              v-model.number="form.minFloor"
              type="number"
              min="-10"
              placeholder="시작층(피로티 제외)"
              :disabled="!form.type"
              @keydown.enter="unitRegister"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label"> 종료층</CFormLabel>
          <CCol sm="8">
            <CFormInput
              v-model.number="form.maxFloor"
              type="number"
              min="-10"
              placeholder="입력 범위 종료층"
              :disabled="!form.minFloor"
              @keydown.enter="unitRegister"
            />
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>

  <CAlert v-if="warning" color="danger">
    <CIcon name="cilWarning" />
    <strong> 주의</strong> : 해당 라인에서 시작층부터 종료층까지 범위의 호수(유니트)가
    <strong>"일괄등록"</strong>됩니다. 해당 동, 타입과 층을 다시 한번 확인하고 불필요한 유니트가
    등록되지 않도록 신중하게 진행하여 주십시요.
  </CAlert>

  <CAlert v-if="write_project" :color="AlertLight" variant="solid" class="text-right">
    <v-btn color="primary" :disabled="!project || !form.minFloor" @click="unitRegister">
      호수(유니트) 일괄등록
    </v-btn>
  </CAlert>

  <FormModal ref="refBuildForm">
    <template #header>동 추가</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CModalBody class="text-body">
          <CRow class="p-2">
            <CFormLabel for="dong" class="col-sm-3 col-form-label">동(건물)</CFormLabel>
            <CCol sm="8">
              <CFormInput v-model="dong" required id="dong" placeholder="동(건물) 이름" />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn :color="btnLight" @click="refBuildForm.close()"> 닫기</v-btn>
          <v-btn type="submit" color="primary">저장</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 호수(유니트) 정보</template>
    <template #default>
      <p class="text-primary">
        <strong>
          [{{ bldgName }}동] ({{ form.type }} 타입) {{ form.line }}호 라인, 층<span
            v-if="form.maxFloor"
            >범위</span
          >
          : {{ form.minFloor }}층
          <span v-if="form.maxFloor">- {{ form.maxFloor }}층</span>
        </strong>
      </p>
      <p>상기 호수(유니트)정보의 일괄등록을 진행하시겠습니까?</p>
    </template>
    <template #footer>
      <v-btn color="primary" @click="modalAction">일괄등록</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
