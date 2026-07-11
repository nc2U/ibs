<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUpdate, type PropType, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { isValidate } from '@/utils/helper.ts'
import { useForum } from '@/store/pinia/forum'
import { colorLight } from '@/utils/cssMixins'
import type { Post, PostCategory } from '@/store/types/forum'
import QuillEditor from '@/components/QuillEditor/index.vue'
import FileForms from '@/components/OtherParts/FileForms.vue'
import LinkForms from '@/components/OtherParts/LinkForms.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  post: { type: Object as PropType<Post | null>, default: null },
  forumId: { type: Number, required: true },
  categories: { type: Array as PropType<PostCategory[]>, default: () => [] },
})

const categoryForm = ref()

const [route, router] = [useRoute(), useRouter()]

const projId = computed(() => route.params.projId as string)

const { can, PERM } = usePerms()
const canForumCreate = computed(() => can(PERM.FORUM_CREATE))
const canForumUpdate = computed(() => can(PERM.FORUM_UPDATE))
const canForumManage = computed(() => can(PERM.FORUM_MANAGE))

const frmStore = useForum()

// 카테고리 간편 추가용 다이얼로그 상태 및 폼 객체
const categoryValidated = ref(false)
const newCategory = ref({
  forum: props.forumId,
  name: '',
  color: '#6c757d',
  order: 1,
})
const isSubmittingCategory = ref(false)

const openCategoryDialog = () => {
  newCategory.value = {
    forum: props.forumId,
    name: '',
    color: '#6c757d',
    order: props.categories.length + 1,
  }
  categoryForm.value.callModal()
}

const submitCategory = (event: Event) => {
  if (isValidate(event)) categoryValidated.value = true
  else {
    isSubmittingCategory.value = true
    frmStore.createCategory(newCategory.value, projId.value).then(() => {
      categoryForm.value.close()
      categoryValidated.value = false
      isSubmittingCategory.value = false
    })
  }
}

const createPost = (payload: { form: FormData }, project: string = '') =>
  frmStore.createPost(payload, project)
const updatePost = (payload: { pk: number; form: FormData }, project: string = '') =>
  frmStore.updatePost(payload, project)

const refFileForms = ref()
const refLinkForms = ref()

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
  is_blind: false,
  ip: null,
  device: '',
})

const newFiles = ref<File[]>([])
const cngFiles = ref<{ pk: number; file: File }[]>([])
const newLinks = ref<string[]>([])

const fileUpload = (file: File) => newFiles.value.push(file)
const fileChange = (payload: { pk: number; file: File }) => cngFiles.value.push(payload)
const filesUpdate = (payload: any[]) => (form.value.files = payload)
const linksUpdate = (payload: any[]) => (form.value.links = payload)
const newLinkPush = (payload: any[]) => payload.forEach(l => newLinks.value.push(l.link))

const submitCheck = (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()
    validated.value = true
  } else {
    validated.value = false
    refLinkForms.value.newLinkPush()
    onSubmit()
    refFileForms.value.checkRelease()
  }
}

const onSubmit = async () => {
  const formData = new FormData()

  Object.keys(form.value).forEach(key => {
    if (key === 'links' || key === 'files') {
      ;(form.value[key] as any[]).forEach(val => formData.append(key, JSON.stringify(val)))
    } else if (key !== 'pk') {
      const val = form.value[key] === null ? '' : form.value[key]
      formData.append(key, val as string)
    }
  })

  newFiles.value.forEach(file => formData.append('newFiles', file))
  cngFiles.value.forEach(val => {
    formData.append('cngPks', val.pk.toString())
    formData.append('cngFiles', val.file)
  })
  newLinks.value.forEach(link => formData.append('newLinks', link))

  if (form.value.pk) {
    await updatePost({ pk: form.value.pk, form: formData }, projId.value)
    await router.replace({
      name: '(게시판) - 게시물 보기',
      params: { projId: route.params.projId, forumId: props.forumId, postId: form.value.pk },
    })
  } else {
    await createPost({ form: formData }, projId.value)
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
    form.value.password = props.post.password
    form.value.is_hide_comment = props.post.is_hide_comment
    form.value.is_notice = props.post.is_notice
    form.value.is_blind = props.post.is_blind
  }
}

onBeforeMount(() => dataSetup())
onBeforeUpdate(() => dataSetup())
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <v-icon icon="mdi-forum-outline" color="primary" class="mr-2" />
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
              <CFormLabel class="col-form-label text-right col-2 col-lg-4">카테고리</CFormLabel>
              <CCol class="col-sm-10 col-md-6 col-lg-8 col-xl-6 d-flex align-center">
                <CFormSelect v-if="categories.length" v-model.number="form.category">
                  <option value="">---------</option>
                  <option v-for="cate in categories" :value="cate.pk" :key="cate.pk as number">
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
                      class="ml-2"
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
              v-if="can(PERM.FORUM_MANAGE)"
              v-model="form.is_notice"
              label="공지사항"
              id="is_notice"
              inline
              class="mr-3"
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
          <CFormLabel class="col-form-label text-right col-2 required">제목</CFormLabel>
          <CCol class="col-sm-10">
            <CFormInput v-model="form.title" placeholder="게시물 제목" required />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">내용</CFormLabel>
          <CCol class="col-sm-10">
            <QuillEditor v-model:content="form.content" />
          </CCol>
        </CRow>

        <FileForms
          ref="refFileForms"
          :files="(post?.files as any[]) ?? []"
          @files-update="filesUpdate"
          @file-upload="fileUpload"
          @file-change="fileChange"
        />

        <LinkForms
          ref="refLinkForms"
          :links="(post?.links as any[]) ?? []"
          @links-update="linksUpdate"
          @new-link-push="newLinkPush"
        />
      </CCardBody>
    </CCard>

    <CRow class="mb-5 text-right">
      <CCol>
        <v-btn
          type="submit"
          :color="!post?.pk ? 'primary' : 'success'"
          :disabled="!post?.pk ? !canForumCreate : !canForumUpdate"
          class="mr-2"
        >
          저장
        </v-btn>
        <v-btn color="light" @click="router.back()" flat>취소</v-btn>
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
            <CFormLabel for="cat-name" class="col-sm-3 col-form-label">색상</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="newCategory.color"
                id="cat-color"
                type="color"
                :value="newCategory.color"
                placeholder="색상 코드"
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="cat-name" class="col-sm-3 col-form-label">순서</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model.number="newCategory.order"
                type="number"
                id="cat-order"
                placeholder="출력 순서"
                maxlength="255"
              />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn variant="flat" color="light" size="small" @click="categoryForm.close()">
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
