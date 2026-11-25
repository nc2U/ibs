<script lang="ts" setup>
import { computed, type PropType, ref, watch } from 'vue'
import { colorLight } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
import { useIssue } from '@/store/pinia/work_issue'
import { useRoute, useRouter } from 'vue-router'
import { isValidate } from '@/utils/helper'

const props = defineProps({
  memberList: { type: Array as PropType<{ pk: number; username: string }[]>, default: () => [] },
})

const emit = defineEmits(['category-submit'])

const route = useRoute()
const router = useRouter()

const { can, PERM } = usePerms()
const canManageCategories = computed(() =>
  can(PERM.ISSUE_CATEGORY_MANAGE, route.params.projId as string),
)

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const filteredMemberList = computed(() => props.memberList.filter(u => u.pk !== userInfo.value?.pk))

const validated = ref(false)

const form = ref({
  pk: null as null | number,
  project: '',
  name: '',
  assigned_to: null as number | string | null,
})

const normalizedAssignedTo = computed<number | null>(() => {
  if (form.value.assigned_to === null || form.value.assigned_to === '') return null
  const num = Number(form.value.assigned_to)
  return Number.isNaN(num) || num <= 0 ? null : num
})

const formsCheck = computed(() => {
  if (!canManageCategories.value) return true
  if (category.value) {
    const a = category.value.name === form.value.name
    const b = (category.value.assigned_to ?? null) === normalizedAssignedTo.value
    return a && b
  } else return false
})

const categorySubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    emit('category-submit', {
      ...form.value,
      assigned_to: normalizedAssignedTo.value,
    })
    validated.value = false
  }
}

const issueStore = useIssue()
const category = computed(() => issueStore.category)

const loadCategory = async () => {
  validated.value = false
  if (route.params.cateId) await issueStore.fetchCategory(Number(route.params.cateId))
  else issueStore.removeCategory()

  if (category.value) {
    form.value.pk = category.value.pk as number
    form.value.project = category.value.project.slug
    form.value.name = category.value.name
    form.value.assigned_to = category.value.assigned_to ?? null
  } else {
    form.value.pk = null
    form.value.project = route.params.projId as string
    form.value.name = ''
    form.value.assigned_to = null
  }
}

watch(
  [() => route.params.projId, () => route.params.cateId],
  () => {
    loadCategory()
  },
  { immediate: true },
)
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
          <CFormLabel for="category-name" class="col-sm-2 col-form-label text-end required">
            이름
          </CFormLabel>

          <CCol sm="10" lg="6">
            <CFormInput
              id="category-name"
              v-model="form.name"
              placeholder="업무 범주 이름"
              required
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="category-assigned" class="col-sm-2 col-form-label text-end">
            담당자
          </CFormLabel>
          <CCol sm="10" lg="6">
            <CFormSelect id="category-assigned" v-model.number="form.assigned_to">
              <option value="">---------</option>
              <option v-if="userInfo?.pk" :value="userInfo.pk">&lt;&lt; 나 &gt;&gt;</option>
              <option v-for="user in filteredMemberList" :value="user.pk" :key="user.pk">
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
        <v-btn
          color="grey"
          variant="tonal"
          @click="
            router.push({
              name: '(설정)',
              params: { projId: route.params.projId },
              query: { menu: '업무범주' },
            })
          "
        >
          취소
        </v-btn>
      </CCol>
    </CRow>
  </CForm>
</template>
