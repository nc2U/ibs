<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { AlertLight } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms'
import type { BuildingUnit } from '@/store/types/project'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['bldg-select', 'dong-register', 'unit-register'])

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projReset = () => {
  form.building = null
  bldgName.value = ''
  typeName.value = ''
  reset(1)
}

defineExpose({ projReset })

const validated = ref(false)

const refBuildForm = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const bldgName = ref('')
const typeName = ref('')

const form = reactive<{
  building: number | null
  line: number | null
  type: number | null
  minFloor: number | null
  maxFloor: number | null
}>({
  building: null,
  line: null,
  type: null,
  minFloor: null,
  maxFloor: null,
})

const warning = computed(() => !!form.maxFloor)

const isRangeInvalid = computed(() => {
  if (form.minFloor === null || form.maxFloor === null) return false
  return form.minFloor > form.maxFloor
})

const typeNameLength = computed(() => {
  if (!unitTypeList.value.length) return 0
  const typeNames = unitTypeList.value.map(t => t.name.replace(/[^0-9a-zA-Z]/g, '').length)
  return Math.max(0, ...typeNames)
})

const maxUnits = computed(() => {
  if (!unitTypeList.value.length) return 0
  const counts = unitTypeList.value.map(t => Number(t.num_unit || 0))
  return Math.max(0, ...counts)
})

const projectDataStore = useProjectData()
const unitTypeList = computed(() => projectDataStore.unitTypeList)
const buildingList = computed(() => projectDataStore.buildingList)
const simpleFloors = computed(() => projectDataStore.simpleFloors)

const fetchNumUnitByType = (projId: number, unit_type: number) =>
  projectDataStore.fetchNumUnitByType(projId, unit_type)

watch(
  () => form.building,
  val => {
    if (!val) reset(1)
  },
)
watch(
  () => form.line,
  val => {
    if (!val) reset(2)
  },
)
watch(
  () => form.type,
  val => {
    if (!val) reset(3)
  },
)
watch(
  () => form.minFloor,
  val => {
    if (val === null) reset(4)
  },
)

const dong = ref('')

const onSubmit = (event: Event) => {
  if (canProjectUpdate.value) {
    const e = event.currentTarget as HTMLFormElement
    if (!e.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

      validated.value = true
    } else {
      emit('dong-register', dong.value.trim())
      dong.value = ''
      refBuildForm.value?.close()
    }
  }
}

const reset = (n: number) => {
  if (n === 1) {
    form.line = null
    form.type = null
    form.minFloor = null
    form.maxFloor = null
  } else if (n === 2) {
    form.type = null
    form.minFloor = null
    form.maxFloor = null
  } else if (n === 3) {
    form.minFloor = null
    form.maxFloor = null
  } else {
    form.maxFloor = null
  }
}

const bldgSelect = (event: Event) => {
  const targetVal = (event.target as HTMLSelectElement).value
  const targetPk = Number(targetVal) || 0
  const targetBldg = buildingList.value.find((b: BuildingUnit) => b.pk === targetPk)
  const bdName = targetBldg?.name ?? ''

  bldgName.value = bdName
  emit('bldg-select', {
    pk: targetPk,
    name: bdName,
  })
}

const typeSelect = (event: Event) => {
  const targetVal = (event.target as HTMLSelectElement).value
  const targetPk = Number(targetVal) || 0
  const targetType = unitTypeList.value.find(t => t.pk === targetPk)

  typeName.value = targetType?.name ?? ''
  if (targetPk && props.project) {
    fetchNumUnitByType(props.project, targetPk)
  }
}

const unitRegister = () => {
  if (isRangeInvalid.value || form.minFloor === null) return

  if (canProjectUpdate.value) refConfirmModal.value?.callModal()
  else {
    refAlertModal.value?.callModal()
    reset(1)
  }
}

const modalAction = () => {
  if (!form.maxFloor) form.maxFloor = form.minFloor
  emit('unit-register', {
    ...form,
    typeName: typeName.value,
    maxLength: typeNameLength.value,
    maxUnits: maxUnits.value,
    floors: simpleFloors.value,
  })
  refConfirmModal.value?.close()
  reset(1)
}
</script>

<template>
  <CCallout color="info" class="pb-2">
    <CRow>
      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">동(건물)선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect v-model.number="form.building" :disabled="!project" @change="bldgSelect">
              <option value="">---------</option>
              <option v-for="bldg in buildingList" :key="bldg.pk" :value="bldg.pk">
                {{ bldg.name }}동
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>
      <CCol v-if="canProjectUpdate" class="pt-1">
        <v-icon
          icon="mdi-plus-thick"
          size="16"
          color="success"
          class="pointer"
          @click="refBuildForm?.callModal()"
        />
      </CCol>
    </CRow>
  </CCallout>

  <CCallout v-if="canProjectUpdate" color="danger" class="pb-2">
    <CRow>
      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">등록라인</CFormLabel>
          <CCol sm="8">
            <CFormInput
              v-model.number="form.line"
              type="number"
              min="1"
              placeholder="등록할 라인 숫자 입력"
              :disabled="!form.building"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">타입선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect v-model.number="form.type" :disabled="!form.line" @change="typeSelect">
              <option value="">---------</option>
              <option v-for="type in unitTypeList" :key="type.pk" :value="type.pk">
                {{ type.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">시작층</CFormLabel>
          <CCol sm="8">
            <CFormInput
              v-model.number="form.minFloor"
              type="number"
              min="-10"
              placeholder="시작층(필로티 제외)"
              :disabled="!form.type"
              @keydown.enter="unitRegister"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">종료층</CFormLabel>
          <CCol sm="8">
            <CFormInput
              v-model.number="form.maxFloor"
              type="number"
              min="-10"
              placeholder="입력 범위 종료층"
              :disabled="!form.minFloor"
              :invalid="isRangeInvalid"
              @keydown.enter="unitRegister"
            />
            <div v-if="isRangeInvalid" class="text-danger small mt-1">
              ※ 종료층은 시작층 이상이어야 합니다.
            </div>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>

  <CAlert v-if="warning" color="danger">
    <CIcon name="cilWarning" />
    <strong> 주의</strong> : 해당 라인에서 시작층부터 종료층까지 범위의 호수(유니트)가
    <strong>"일괄등록"</strong>됩니다. 해당 동, 타입과 층을 다시 한번 확인하고 불필요한 유니트가
    등록되지 않도록 신중하게 진행하여 주십시오.
  </CAlert>

  <CAlert v-if="canProjectUpdate" :color="AlertLight" variant="solid" class="text-right">
    <v-btn
      color="primary"
      :disabled="!project || form.minFloor === null || isRangeInvalid"
      @click="unitRegister"
    >
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
          <v-btn type="submit" size="small" color="primary">저장</v-btn>
          <v-btn color="light" size="small" @click="refBuildForm?.close()" flat>닫기</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header>호수(유니트) 정보</template>
    <template #default>
      <p class="text-primary">
        <strong>
          [{{ bldgName }}동] ({{ typeName || form.type }} 타입) {{ form.line }}호 라인, 층<span
            v-if="form.maxFloor"
          >
            범위
          </span>
          : {{ form.minFloor }}층
          <span v-if="form.maxFloor">- {{ form.maxFloor }}층</span>
        </strong>
      </p>
      <p>상기 호수(유니트)정보의 일괄등록을 진행하시겠습니까?</p>
    </template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">일괄등록</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
