<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { btnLight, TableSecondary } from '@/utils/cssMixins.ts'
import type { Repository } from '@/store/types/work.ts'
import NoData from '@/views/_Work/components/NoData.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  projId: { type: String, required: true },
  repoList: { type: Array as PropType<Repository[]>, default: () => [] },
})

const emit = defineEmits(['submit-repo', 'delete-repo'])

const refFormModal = ref()
const refDeleteCheck = ref()

const validated = ref(false)
const form = ref({
  pk: undefined as undefined | number,
  project: '' as '' | number,
  is_default: false,
  owner: '',
  slug: '',
  github_api_url: '',
  github_token: '',
  is_report: false,
})

const resetForm = () => {
  form.value.pk = undefined
  form.value.project = ''
  form.value.is_default = false
  form.value.owner = ''
  form.value.slug = ''
  form.value.github_api_url = ''
  form.value.github_token = ''
  form.value.is_report = false
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) validated.value = isValidate(event)
  else {
    emit('submit-repo', { ...form.value })
    validated.value = false
    resetForm()
    refFormModal.value.close()
  }
}

const toEditRepo = (repo: Repository) => {
  form.value.pk = repo.pk
  form.value.project = repo.project
  form.value.is_default = repo.is_default
  form.value.owner = repo.owner
  form.value.slug = repo.slug
  form.value.github_api_url = repo.github_api_url
  form.value.github_token = repo.github_token
  form.value.is_report = repo.is_report
  refFormModal.value.callModal()
}

const addRepoFunc = () => {
  resetForm()
  refFormModal.value.callModal()
}

const formModalClose = () => {
  resetForm()
  refFormModal.value.close()
}

// repository delete!
const delRepoPk = ref<number | null>(null)
const delRepository = (repo: number) => {
  delRepoPk.value = repo
  refDeleteCheck.value.callModal('저장소 삭제', '계속 진행 하시겠습니까?', null, 'amber')
}
const modalAction = () => {
  emit('delete-repo', delRepoPk.value)
  delRepoPk.value = null
  refDeleteCheck.value.close()
}
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link to="" @click="addRepoFunc" class="ml-1">저장소 추가</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!repoList.length" />

  <CRow v-else>
    <CCol class="pt-4">
      <CTable hover striped small>
        <CTableHead>
          <CTableRow :color="TableSecondary" class="text-center">
            <CTableHeaderCell>식별자</CTableHeaderCell>
            <CTableHeaderCell>주 저쟝소</CTableHeaderCell>
            <CTableHeaderCell>형상관리시스템</CTableHeaderCell>
            <CTableHeaderCell>저장소(api)</CTableHeaderCell>
            <CTableHeaderCell>비고</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="repo in repoList" :key="repo.pk" class="text-center">
            <CTableDataCell class="text-left pl-3">
              <router-link :to="{ name: '(저장소)', params: { projId } }">
                {{ repo.slug }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <v-icon v-if="repo.is_default" icon="mdi-check-bold" size="16" color="success" />
            </CTableDataCell>
            <CTableDataCell>Git</CTableDataCell>
            <CTableDataCell>
              <router-link :to="{ name: '(저장소)', params: { projId } }">
                {{ repo.github_api_url }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <span class="mr-2">
                <v-icon icon="mdi-account-multiple" color="info" size="16" />
                <router-link to="">사용자</router-link>
              </span>
              <span class="mr-2">
                <v-icon icon="mdi-pencil" color="success" size="16" />
                <router-link to="#" @click="toEditRepo(repo)">편집</router-link>
              </span>
              <span>
                <v-icon icon="mdi-trash-can-outline" color="warning" size="16" />
                <router-link to="#" @click="delRepository(repo?.pk as number)"> 삭제 </router-link>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>

  <FormModal ref="refFormModal">
    <template #header>저장소 {{ form.pk ? '수정' : '추가' }}</template>
    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
      <template #default>
        <CModalBody class="text-body">
          <CRow class="mb-3">
            <CFormLabel for="isDefaultForm" class="col-sm-3 col-form-label"></CFormLabel>
            <CCol sm="9" class="pt-2">
              <CFormCheck v-model="form.is_default" id="isDefaultForm" label="주 저장소" />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="slugForm" class="col-sm-3 col-form-label required">소유자</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.owner"
                id="ownerForm"
                placeholder="github 아이디"
                maxlength="50"
                required
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="slugForm" class="col-sm-3 col-form-label required">식별자</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.slug"
                id="slugForm"
                placeholder="github 레파지토리 이름"
                maxlength="255"
                required
              />
            </CCol>
          </CRow>
          <!--          <CRow class="mb-3">-->
          <!--            <CFormLabel for="githubApiForm" class="col-sm-3 col-form-label required">-->
          <!--              깃허브 API-->
          <!--            </CFormLabel>-->
          <!--            <CCol sm="9">-->
          <!--              <CFormInput-->
          <!--                v-model="form.github_api_url"-->
          <!--                id="githubApiForm"-->
          <!--                required-->
          <!--                placeholder="Github API"-->
          <!--              />-->
          <!--            </CCol>-->
          <!--          </CRow>-->

          <CRow class="mb-3 required">
            <CFormLabel for="githubTokenForm" class="col-sm-3 col-form-label required">
              깃허브 토큰
            </CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.github_token"
                id="githubTokenForm"
                maxlength="255"
                required
                placeholder="Github Token"
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="isReportForm" class="col-sm-3 col-form-label"></CFormLabel>
            <CCol sm="9" class="pt-2">
              <CFormCheck
                v-model="form.is_report"
                id="isReportForm"
                label="파일이나 폴더의 마지막 커밋을 보고"
              />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn :color="btnLight" size="small" @click="formModalClose"> 닫기</v-btn>
          <v-btn type="submit" :color="form.pk ? 'success' : 'primary'" size="small">확인</v-btn>
        </CModalFooter>
      </template>
    </CForm>
  </FormModal>

  <ConfirmModal ref="refDeleteCheck">
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
