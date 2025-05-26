<script lang="ts" setup>
import { ref, onBeforeMount, inject, type ComputedRef, type PropType, computed } from 'vue'
import type { User } from '@/store/types/accounts'
import { colorLight } from '@/utils/cssMixins'
import { useRoute } from 'vue-router'
import { isValidate } from '@/utils/helper'
import { useWork } from '@/store/pinia/work_project.ts'

defineProps({
  memberList: { type: Array as PropType<{ pk: number; username: string }[]>, default: () => [] },
})

const emit = defineEmits(['category-submit'])

const userInfo = inject<ComputedRef<User>>('userInfo')

const validated = ref(false)

const form = ref({
  pk: null as null | number,
  project: '',
  name: '',
  assigned_to: null as number | null,
})

const formsCheck = computed(() => {
  if (category.value) {
    const a = category.value.name === form.value.name
    const b = category.value.assigned_to === form.value.assigned_to
    return a && b
  } else return false
})

const route = useRoute()

const categorySubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    emit('category-submit', { ...form.value })
    validated.value = false
  }
}

const workStore = useWork()
const category = computed(() => workStore.category)

onBeforeMount(async () => {
  if (route.params.cateId) await workStore.fetchCategory(Number(route.params.cateId))
  else workStore.category = null

  if (category.value) {
    form.value.pk = category.value.pk as number
    form.value.project = category.value.project.slug
    form.value.name = category.value.name
    form.value.assigned_to = category.value.assigned_to ?? null
  } else form.value.project = route.params.projId as string
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5><span v-if="!route.params.cateId">새</span> 업무 범주</h5>
    </CCol>
  </CRow>

  <CForm
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="categorySubmit"
  >
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow class="mb-3">
          <CFormLabel for="name" class="col-sm-2 col-form-label text-right required">
            이름
          </CFormLabel>

          <CCol sm="10" lg="6">
            <CFormInput v-model="form.name" placeholder="업무 범주 이름" required />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="category-name" class="col-sm-2 col-form-label text-right">
            담당자
          </CFormLabel>
          <CCol sm="10" lg="6">
            <CFormSelect v-model.number="form.assigned_to">
              <option value="">---------</option>
              <option :value="userInfo?.pk">&lt;&lt; 나 &gt;&gt;</option>
              <option v-for="user in memberList" :value="user.pk" :key="user.pk">
                {{ user.username }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <CRow>
      <CCol>
        <v-btn type="submit" :color="category ? 'success' : 'primary'" :disabled="formsCheck">
          저장
        </v-btn>
      </CCol>
    </CRow>
  </CForm>
</template>
