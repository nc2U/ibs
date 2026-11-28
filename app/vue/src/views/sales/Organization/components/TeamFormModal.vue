<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SalesTeam } from '@/store/types/sales'
import { colorLight } from '@/utils/cssMixins'
import { isValidate } from '@/utils/helper'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  agencyId: { type: Number, default: null },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)
const validated = ref(false)

const agencyList = computed(() => salesStore.agencyList)
// 상위 본부 후보 (parent가 없는 본부급 팀 목록, 선택된 대행사 소속 한정)
const parentTeamOptions = computed(() =>
  salesStore.teamList.filter(
    t => !t.parent && t.id !== targetId.value && (!form.agency || t.agency === form.agency),
  ),
)

const form = reactive({
  agency: null as number | null,
  parent: null as number | null,
  name: '',
  order: 1,
  is_active: true,
})

// 대행사가 변경되면 상위 조직이 해당 대행사 소속인지 확인하고 다르면 초기화
watch(
  () => form.agency,
  newAgency => {
    if (form.parent) {
      const parentTeam = salesStore.teamList.find(t => t.id === form.parent)
      if (parentTeam && parentTeam.agency !== newAgency) {
        form.parent = null
      }
    }
  },
)

const parseNumberOrNull = (val: string | string[] | undefined): number | null =>
  val && !Array.isArray(val) ? Number(val) : null

const resetForm = () => {
  validated.value = false
  form.agency = props.agencyId || (agencyList.value[0]?.id ?? null)
  form.parent = null
  form.name = ''
  form.order = 1
  form.is_active = true
  targetId.value = null
  isEdit.value = false
}

const open = (team?: SalesTeam, defaultAgencyId?: number) => {
  resetForm()
  if (defaultAgencyId) {
    form.agency = defaultAgencyId
  }
  if (team) {
    isEdit.value = true
    targetId.value = team.id
    form.agency = team.agency
    form.parent = team.parent
    form.name = team.name
    form.order = team.order
    form.is_active = team.is_active
  }
  modalRef.value?.callModal()
}

const isSubmitting = ref(false)

const submit = async (event: Event) => {
  if (isSubmitting.value) return

  if (isValidate(event)) {
    validated.value = true
    return
  }

  if (!form.agency || !form.name.trim()) {
    validated.value = true
    return
  }

  isSubmitting.value = true
  try {
    const payload = {
      agency: form.agency,
      parent: form.parent,
      name: form.name.trim(),
      order: form.order,
      is_active: form.is_active,
    }

    const ok =
      isEdit.value && targetId.value
        ? await salesStore.updateTeam(targetId.value, payload)
        : await salesStore.createTeam(payload)

    if (!ok) return
    modalRef.value?.close()
    emit('saved')
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '영업 조직/팀 수정' : '신규 영업 조직/팀 등록' }}</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="submit">
        <CModalBody>
          <CRow class="g-3">
            <CCol md="6">
              <CFormLabel class="small required">소속 대행사</CFormLabel>
              <CFormSelect
                :model-value="form.agency ? String(form.agency) : ''"
                required
                @update:model-value="val => (form.agency = parseNumberOrNull(val))"
              >
                <option value="">대행사를 선택하세요</option>
                <option v-for="a in agencyList" :key="a.id" :value="String(a.id)">
                  {{ a.name }} {{ a.is_direct_managed ? '[직영]' : '' }}
                </option>
              </CFormSelect>
              <CFormFeedback invalid>소속 분양 대행사를 선택해주세요.</CFormFeedback>
            </CCol>

            <CCol md="6">
              <CFormLabel class="small">상위 조직 (본부)</CFormLabel>
              <CFormSelect
                :model-value="form.parent ? String(form.parent) : ''"
                @update:model-value="val => (form.parent = parseNumberOrNull(val))"
              >
                <option value="">최상위 본부 (없음)</option>
                <option v-for="p in parentTeamOptions" :key="p.id" :value="String(p.id)">
                  {{ p.name }}
                </option>
              </CFormSelect>
            </CCol>

            <CCol md="6">
              <CFormLabel class="small required">조직/팀명</CFormLabel>
              <CFormInput
                v-model="form.name"
                placeholder="예: 영업1본부 또는 1팀"
                required
              />
              <CFormFeedback invalid>조직/팀명을 입력해주세요.</CFormFeedback>
            </CCol>

            <CCol md="3">
              <CFormLabel class="small">정렬 순서</CFormLabel>
              <CFormInput v-model.number="form.order" type="number" min="1" />
            </CCol>

            <CCol md="3" class="d-flex align-items-center pt-4">
              <CFormCheck id="team_is_active" v-model="form.is_active" label="사용 여부 (활성화)" />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn
            type="submit"
            color="primary"
            size="small"
            :loading="isSubmitting"
            :disabled="isSubmitting"
          >
            {{ isEdit ? '수정 저장' : '등록하기' }}
          </v-btn>
          <v-btn
            :color="colorLight"
            size="small"
            flat
            :disabled="isSubmitting"
            @click="modalRef?.close()"
          >
            취소
          </v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>
</template>
