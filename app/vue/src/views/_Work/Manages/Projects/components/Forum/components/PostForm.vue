<script lang="ts" setup>
import { computed, type PropType, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { isValidate } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account'
import { useForum } from '@/store/pinia/forum'
import { useWork } from '@/store/pinia/work_project'
import { colorLight } from '@/utils/cssMixins'
import type { Post, PostCategory, PostFile } from '@/store/types/forum'
import QuillEditor from '@/components/QuillEditor/index.vue'
import FileForms from '@/components/OtherParts/FileForms.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  post: { type: Object as PropType<Post | null>, default: null },
  forumId: { type: Number, required: true },
  categories: { type: Array as PropType<PostCategory[]>, default: () => [] },
})

const categoryForm = ref<InstanceType<typeof FormModal> | null>(null)

const [route, router] = [useRoute(), useRouter()]

const projId = computed(() => route.params.projId as string)

const accStore = useAccount()
const frmStore = useForum()
const workStore = useWork()
const isProjectActive = computed(
  () => !workStore.currentProject || workStore.currentProject.status === '1',
)

const isForumManager = computed(() => {
  if (accStore.userInfo?.is_superuser || accStore.workManager) return true
  const forum = frmStore.forumList.find(f => f.pk === props.forumId) || frmStore.forum
  if (!forum || !forum.manager) return false
  return (forum.manager as number[]).includes(accStore.userInfo?.pk ?? 0)
})

const { can, PERM } = usePerms()
const canForumCreate = computed(() => {
  if (!isProjectActive.value) return false
  if (isForumManager.value) return true
  const forum = frmStore.forumList.find(f => f.pk === props.forumId) || frmStore.forum
  if (forum?.manager_only) return false
  return can(PERM.FORUM_CREATE, projId.value)
})
const canForumUpdate = computed(() => {
  if (!isProjectActive.value) return false
  if (isForumManager.value) return true
  if (can(PERM.FORUM_UPDATE, projId.value)) return true
  if (can(PERM.FORUM_OWN_UPDATE, projId.value)) {
    return !!props.post?.creator?.pk && props.post.creator.pk === accStore.userInfo?.pk
  }
  return false
})
const canForumManage = computed(() => isProjectActive.value && can(PERM.FORUM_MANAGE, projId.value))

const availableCategories = computed(() => {
  return props.categories.filter(cate => !cate.is_manager_only || isForumManager.value)
})

// 카테고리 간편 추가용 다이얼로그 상태 및 폼 객체
const categoryValidated = ref(false)
const newCategory = ref({
  forum: props.forumId,
  name: '',
  color: '#6c757d',
  order: 1,
  is_manager_only: false,
})
const isSubmittingCategory = ref(false)

const openCategoryDialog = () => {
  newCategory.value = {
    forum: props.forumId,
    name: '',
    color: '#6c757d',
    order: props.categories.length + 1,
    is_manager_only: false,
  }
  categoryForm.value?.callModal()
}

const submitCategory = async (event: Event) => {
  if (isValidate(event)) {
    categoryValidated.value = true
    return
  }
  isSubmittingCategory.value = true
  try {
    const created = await frmStore.createCategory(newCategory.value, projId.value)
    if (created) {
      categoryForm.value?.close()
      categoryValidated.value = false
    }
  } finally {
    isSubmittingCategory.value = false
  }
}

const createPost = (payload: { form: FormData }, project: string = '') =>
  frmStore.createPost(payload, project)
const updatePost = (payload: { pk: number; form: FormData }, project: string = '') =>
  frmStore.updatePost(payload, project)

const refFileForms = ref<InstanceType<typeof FileForms> | null>(null)

const validated = ref(false)
const form = ref<Post>({
  pk: undefined,
  forum: props.forumId,
  category: null,
  title: '',
  content: '',
  is_secret: false,
  password: '',
  is_hide_comment: false,
  is_notice: false,
  is_faq: false,
  is_blind: false,
  ip: null,
  device: '',
})

const newFiles = ref<File[]>([])
const cngFiles = ref<{ pk: number; file: File }[]>([])

const fileUpload = (file: File) => newFiles.value.push(file)
const fileChange = (payload: { pk: number; file: File }) => cngFiles.value.push(payload)
const filesUpdate = (payload: PostFile[]) => (form.value.files = payload)

const submitCheck = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    validated.value = false
    onSubmit()
  }
}

const onSubmit = async () => {
  const formData = new FormData()

  Object.keys(form.value).forEach(key => {
    if (key === 'files') {
      ;(form.value.files ?? []).forEach(val => formData.append(key, JSON.stringify(val)))
    } else if (key !== 'pk') {
      const val = form.value[key] === null ? '' : form.value[key]
      formData.append(key, val as string)
    }
  })

  const activeNewFiles = refFileForms.value?.getNewFiles() ?? newFiles.value
  activeNewFiles.forEach(file => formData.append('newFiles', file))
  cngFiles.value.forEach(val => {
    formData.append('cngPks', val.pk.toString())
    formData.append('cngFiles', val.file)
  })

  if (form.value.pk) {
    const updated = await updatePost({ pk: form.value.pk, form: formData }, projId.value)
    if (!updated) return
    refFileForms.value?.checkRelease()
    await router.replace({
      name: '(게시판) - 게시물 보기',
      params: { projId: route.params.projId, forumId: props.forumId, postId: form.value.pk },
    })
  } else {
    const created = await createPost({ form: formData }, projId.value)
    if (!created) return
    refFileForms.value?.checkRelease()
    await router.replace({
      name: '(게시판) - 보기',
      params: { projId: route.params.projId, forumId: props.forumId },
    })
  }
}

const dataSetup = () => {
  if (props.post) {
    form.value.pk = props.post.pk
    form.value.forum = props.post.forum
    form.value.category = props.post.category
    form.value.title = props.post.title
    form.value.content = props.post.content
    form.value.is_secret = props.post.is_secret
    form.value.password = props.post.password || ''
    form.value.is_hide_comment = props.post.is_hide_comment
    form.value.is_notice = props.post.is_notice
    form.value.is_faq = props.post.is_faq ?? false
    form.value.is_blind = props.post.is_blind
  }
}

watch(
  () => props.post,
  () => dataSetup(),
  { immediate: true },
)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <v-icon icon="mdi-forum-outline" color="green-darken-1" class="me-2" />
        게시물 {{ post ? '수정' : '작성' }}
      </h5>
    </CCol>
  </CRow>

  <CForm
    enctype="multipart/form-data"
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="submitCheck"
  >
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow class="mb-3">
          <CCol sm="12" lg="6">
            <CRow>
              <CFormLabel class="col-form-label text-end col-2 col-lg-4">카테고리</CFormLabel>
              <CCol class="col-sm-10 col-md-6 col-lg-8 col-xl-6 d-flex align-center">
                <CFormSelect v-if="availableCategories.length" v-model.number="form.category">
                  <option value="">---------</option>
                  <option
                    v-for="cate in availableCategories"
                    :value="cate.pk"
                    :key="cate.pk as number"
                  >
                    {{ cate.name }}
                  </option>
                </CFormSelect>

                <v-tooltip text="카테고리 추가">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      v-if="canForumManage"
                      icon="mdi-plus"
                      color="success"
                      size="x-small"
                      variant="text"
                      density="comfortable"
                      title="카테고리 추가"
                      class="ms-2"
                      @click="openCategoryDialog"
                    >
                    </v-btn>
                  </template>
                </v-tooltip>
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="12" lg="6" class="pt-2">
            <CFormCheck
              v-if="canForumManage || isForumManager"
              v-model="form.is_notice"
              label="공지사항"
              id="is_notice"
              inline
              class="me-3"
            />
            <CFormCheck
              v-if="canForumManage || isForumManager"
              v-model="form.is_faq"
              label="FAQ 등록"
              id="is_faq"
              inline
              class="me-3"
            />
            <CFormCheck v-model="form.is_blind" label="숨김글" id="is_blind" inline />
            <span v-if="form.is_blind" class="text-muted">
              숨김글로 설정한 게시물은 관리자만 확인할 수 있습니다.
            </span>
            <CFormCheck v-model="form.is_secret" label="비밀글" id="is_secret" inline />
            <span v-if="form.is_secret" class="text-muted">
              비밀글로 설정한 게시물은 본인과 관리자만 확인할 수 있습니다.
            </span>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-end col-2 required">제목</CFormLabel>
          <CCol class="col-sm-10">
            <CFormInput v-model="form.title" placeholder="게시물 제목" required />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-end col-2">내용</CFormLabel>
          <CCol class="col-sm-10">
            <QuillEditor v-model:content="form.content" />
          </CCol>
        </CRow>

        <FileForms
          ref="refFileForms"
          :files="post?.files ?? []"
          @files-update="filesUpdate"
          @file-upload="fileUpload"
          @file-change="fileChange"
        />
      </CCardBody>
    </CCard>

    <CRow class="mb-5 text-end">
      <CCol>
        <v-btn
          type="submit"
          :color="!post?.pk ? 'primary' : 'success'"
          :disabled="!post?.pk ? !canForumCreate : !canForumUpdate"
          class="me-2"
        >
          저장
        </v-btn>
        <v-btn color="grey" variant="tonal" @click="router.back()">취소</v-btn>
      </CCol>
    </CRow>
  </CForm>

  <!-- 카테고리 간편 추가 다이얼로그 (FormModal 적용) -->
  <FormModal ref="categoryForm">
    <template #header>새 카테고리 등록</template>
    <template #default>
      <CForm
        class="needs-validation"
        novalidate
        :validated="categoryValidated"
        @submit.prevent="submitCategory"
      >
        <CModalBody class="text-body">
          <CRow class="mb-3">
            <CFormLabel for="cat-name" class="col-sm-3 col-form-label required">이름</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="newCategory.name"
                id="cat-name"
                placeholder="카테고리 명칭"
                maxlength="255"
                required
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="cat-color" class="col-sm-3 col-form-label">색상</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="newCategory.color"
                id="cat-color"
                type="color"
                placeholder="색상 코드"
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="cat-order" class="col-sm-3 col-form-label">순서</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model.number="newCategory.order"
                type="number"
                id="cat-order"
                placeholder="출력 순서"
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="cat-manager-only" class="col-sm-3 col-form-label"
              >관리자 전용</CFormLabel
            >
            <CCol sm="9" class="pt-2">
              <CFormCheck
                v-model="newCategory.is_manager_only"
                id="cat-manager-only"
                label="해당 게시판 관리자만 작성 가능"
              />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn variant="tonal" color="grey" size="small" @click="categoryForm?.close()">
            닫기
          </v-btn>
          <v-btn type="submit" color="primary" size="small" :loading="isSubmittingCategory">
            확인
          </v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>
</template>
