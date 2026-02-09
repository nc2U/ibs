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
  form.startNum = null
  form.endNum = null
}

defineExpose({ projReset })

const refConfirmModal = ref()
const refAlertModal = ref()

const form = reactive<{
  unit_type: number | null
  startNum: number | null
  endNum: number | null
}>({
  unit_type: null,
  startNum: null,
  endNum: null,
})

const projectDataStore = useProjectData()
const unitTypeList = computed(() => projectDataStore.unitTypeList)
const keyUnitList = computed(() => projectDataStore.keyUnitList)

const selectedType = computed(() =>
  unitTypeList.value.find(t => t.pk === form.unit_type),
)

const filteredKeyUnits = computed(() => {
  if (!form.unit_type) return keyUnitList.value
  return keyUnitList.value.filter(ku => ku.unit_type === form.unit_type)
})

const bulkCount = computed(() => {
  if (!form.startNum || !form.endNum || form.endNum < form.startNum) return 0
  return form.endNum - form.startNum + 1
})

const typeName = (typeId: number) => {
  const t = unitTypeList.value.find(ut => ut.pk === typeId)
  return t ? t.name : ''
}

// unit_code 생성: 타입명(영숫자) + 0패딩 번호 (Index.vue의 getCode 패턴과 동일)
const generateUnitCode = (num: number) => {
  if (!selectedType.value) return ''
  const typeStr = selectedType.value.name.replace(/[^0-9a-zA-Z]/g, '')

  // 타입명 목록 중 가장 긴 영숫자 길이
  const maxTypeLen = Math.max(
    ...unitTypeList.value
      .map(t => t.name.replace(/[^0-9a-zA-Z]/g, ''))
      .map(s => s.length),
  )
  const typeDigit = maxTypeLen - typeStr.length
  const suffix = typeDigit >= 1 ? '0'.repeat(typeDigit - 1) + '1' : ''

  // num_unit 기준 자릿수 (최대 유닛 수 기반)
  const maxUnits = Math.max(
    ...unitTypeList.value.map(t => (t.num_unit as number) || 0),
  )
  const digitLen = `${maxUnits}`.length
  const prefix = '0'.repeat(Math.max(0, digitLen - `${num}`.length))

  return `${typeStr}${suffix}${prefix}${num}`
}

const typeSelect = () => {
  if (props.project) {
    projectDataStore.fetchKeyUnitList(props.project, form.unit_type || undefined)
  }
}

const bulkRegister = () => {
  if (write_project.value) {
    if (!form.unit_type || !form.startNum || !form.endNum) return
    if (form.endNum < form.startNum) return
    refConfirmModal.value.callModal()
  } else {
    refAlertModal.value.callModal()
  }
}

const emit = defineEmits(['key-unit-created'])

const modalAction = () => {
  if (props.project && form.unit_type && form.startNum && form.endNum) {
    const payloads: CreateKeyUnit[] = []
    for (let i = form.startNum; i <= form.endNum; i++) {
      payloads.push({
        project: props.project,
        unit_type: form.unit_type,
        unit_code: generateUnitCode(i),
      })
    }
    projectDataStore.createKeyUnitBulk(payloads).then(() => emit('key-unit-created'))
    form.startNum = null
    form.endNum = null
  }
  refConfirmModal.value.close()
}

const deleteUnit = (pk: number) => {
  if (props.project) projectDataStore.deleteKeyUnit(pk, props.project, form.unit_type || undefined)
}
</script>

<template>
  <CCallout color="info" class="pb-2">
    <CRow>
      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel class="col-sm-4 col-form-label">타입 선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect v-model.number="form.unit_type" :disabled="!project" @change="typeSelect">
              <option value="">전체</option>
              <option v-for="type in unitTypeList" :key="type.pk" :value="type.pk">
                {{ type.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <template v-if="write_project && form.unit_type">
        <CCol md="2" class="mb-2">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label">시작</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model.number="form.startNum"
                type="number"
                min="1"
                placeholder="시작 번호"
                @keydown.enter="bulkRegister"
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol md="2" class="mb-2">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label">종료</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model.number="form.endNum"
                type="number"
                min="1"
                placeholder="종료 번호"
                :disabled="!form.startNum"
                @keydown.enter="bulkRegister"
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol md="2" class="mb-2 pt-1">
          <v-btn
            color="primary"
            size="small"
            :disabled="!project || !form.unit_type || !form.startNum || !form.endNum || bulkCount <= 0"
            @click="bulkRegister"
          >
            일괄등록 ({{ bulkCount }}건)
          </v-btn>
        </CCol>

        <CCol v-if="form.startNum" md="3" class="mb-2 pt-2 text-medium-emphasis" style="font-size: 0.85em">
          미리보기: {{ generateUnitCode(form.startNum) }}
          <span v-if="form.endNum && form.endNum > form.startNum">
            ~ {{ generateUnitCode(form.endNum) }}
          </span>
        </CCol>
      </template>
    </CRow>
  </CCallout>

  <CAlert :color="AlertLight" variant="solid">
    <strong>유닛 목록</strong>
    <span v-if="form.unit_type"> - {{ typeName(form.unit_type) }}</span>
    (총 {{ filteredKeyUnits.length }}건)
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
    <template #header>유닛 일괄등록</template>
    <template #default>
      <p>
        <strong class="text-primary">{{ selectedType?.name }}</strong> 타입
      </p>
      <p>
        유닛 코드:
        <strong>{{ generateUnitCode(form.startNum || 0) }}</strong>
        ~
        <strong>{{ generateUnitCode(form.endNum || 0) }}</strong>
      </p>
      <p>
        총 <strong class="text-primary">{{ bulkCount }}건</strong>의 유닛을 등록하시겠습니까?
      </p>
    </template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">일괄등록</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
