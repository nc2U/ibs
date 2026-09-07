<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SalesTeam } from '@/store/types/sales'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  agencyId: { type: Number, default: null },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)

const agencyList = computed(() => salesStore.agencyList)
// 상위 본부 후보 (parent가 없는 본부급 팀 목록)
const parentTeamOptions = computed(() =>
  salesStore.teamList.filter(t => !t.parent && t.id !== targetId.value),
)

const form = reactive({
  agency: null as number | null,
  parent: null as number | null,
  name: '',
  order: 1,
  is_active: true,
})

const resetForm = () => {
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
  modalRef.value.callModal()
}

const isSubmitting = ref(false)

const submit = async (e?: KeyboardEvent) => {
  if (e?.isComposing) return
  if (isSubmitting.value) return

  if (!form.agency) {
    alert('소속 분양 대행사를 선택해주세요.')
    return
  }
  if (!form.name.trim()) {
    alert('조직/팀명을 입력해주세요.')
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

    if (isEdit.value && targetId.value) {
      await salesStore.updateTeam(targetId.value, payload)
    } else {
      await salesStore.createTeam(payload)
    }
    modalRef.value.close()
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
      <CModalBody>
        <CRow class="g-3">
          <CCol md="6">
            <CFormLabel>소속 대행사 <span class="text-danger">*</span></CFormLabel>
            <CFormSelect v-model.number="form.agency" required>
              <option :value="null">대행사를 선택하세요</option>
              <option v-for="a in agencyList" :key="a.id" :value="a.id">
                {{ a.name }} {{ a.is_direct_managed ? '[직영]' : '' }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6">
            <CFormLabel>상위 조직 (본부)</CFormLabel>
            <CFormSelect v-model.number="form.parent">
              <option :value="null">최상위 본부 (없음)</option>
              <option v-for="p in parentTeamOptions" :key="p.id" :value="p.id">
                {{ p.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6">
            <CFormLabel>조직/팀명 <span class="text-danger">*</span></CFormLabel>
            <CFormInput
              v-model="form.name"
              placeholder="예: 영업1본부 또는 1팀"
              required
              @keydown.enter.prevent="submit"
            />
          </CCol>

          <CCol md="3">
            <CFormLabel>정렬 순서</CFormLabel>
            <CFormInput v-model.number="form.order" type="number" min="1" @keydown.enter.prevent="submit" />
          </CCol>

          <CCol md="3" class="d-flex align-items-center pt-4">
            <CFormCheck id="team_is_active" v-model="form.is_active" label="사용 여부" />
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <v-btn color="primary" size="small" :loading="isSubmitting" :disabled="isSubmitting" @click="submit">
          {{ isEdit ? '수정 저장' : '등록하기' }}
        </v-btn>
        <v-btn color="light" size="small" flat :disabled="isSubmitting" @click="modalRef.close()">취소</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>
