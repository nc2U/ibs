<script lang="ts" setup>
import type { PropType } from 'vue'
import { ref, reactive, computed, onMounted, onUpdated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Post, PostLink } from '@/store/types/board'
import { AlertSecondary } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'
import QuillEditor from '@/components/QuillEditor/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  sortName: { type: String, default: '【본사】' },
  boardNum: { type: Number, default: 2 },
  categoryList: { type: Object, required: true },
  getSuitCase: { type: Object, default: null },
  post: { type: Object as PropType<Post>, default: null },
  viewRoute: { type: String, required: true },
  writeAuth: { type: Boolean, default: true },
})

const emit = defineEmits(['on-submit', 'file-upload', 'file-change', 'close'])

const refDelModal = ref()
const refAlertModal = ref()
const refConfirmModal = ref()

const attach = ref(true)
const validated = ref(false)
const form = reactive<Post>({
  pk: undefined,
  issue_project: null,
  board: props.boardNum,
  category: null,
  title: '',
  content: '',
  ip: null,
  device: '',
  is_secret: false,
  password: '',
  is_hide_comment: false,
  is_notice: false,
  is_blind: false,
  links: [],
  files: [],
})

const newLinks = ref<PostLink[]>([])

const formsCheck = computed(() => {
  if (props.post) {
    const a = form.category === props.post.category
    const b = form.title === props.post.title
    const c = form.content === props.post.content
    const d = form.is_notice === props.post.is_notice

    return a && b && c && d && attach.value
  } else return false
})

const [route, router] = [useRoute(), useRouter()]
const btnClass = computed(() => (route.params.postId ? 'success' : 'primary'))

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const newLinkNum = ref(1)
const newLinkRange = computed(() => range(0, newLinkNum.value))

const newFileNum = ref(1)
const newFileRange = computed(() => range(0, newFileNum.value))

const ctlLinkNum = (n: number) => {
  if (n + 1 >= newLinkNum.value) newLinkNum.value = newLinkNum.value + 1
  else newLinkNum.value = newLinkNum.value - 1
}

const ctlFileNum = (n: number) => {
  if (n + 1 >= newFileNum.value) newFileNum.value = newFileNum.value + 1
  else newFileNum.value = newFileNum.value - 1
}

const enableStore = (event: Event) => {
  const el = event.target as HTMLInputElement
  attach.value = !el.value
}

const editFile = (i: number) => {
  if (form.files?.length) {
    form.files[i].del = false
    form.files[i].edit = !form.files[i].edit
  }
}

const fileChange = (event: Event, pk: number) => {
  enableStore(event)
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-change', { pk, file })
  }
}

const fileUpload = (event: Event) => {
  enableStore(event)
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-upload', file)
  }
}

const onSubmit = (event: Event) => {
  if (props.writeAuth) {
    const el = event.currentTarget as HTMLFormElement
    if (!el.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

      validated.value = true
    } else refConfirmModal.value.callModal()
  } else refAlertModal.value.callModal()
}

const modalAction = () => {
  emit('on-submit', { ...form, newLinks: newLinks.value })
  validated.value = false
  refConfirmModal.value.close()
}

const devideUri = (uri: string) => {
  const devidedUri = decodeURI(uri).split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1]]
}

const dataSetup = () => {
  if (props.post) {
    form.pk = props.post.pk
    form.issue_project = props.post.issue_project
    form.board = props.post.board
    form.category = props.post.category
    form.title = props.post.title
    form.content = props.post.content
    // form.hit = props.post.hit
    // form.like = props.post.like
    // form.blame = props.post.blame
    form.ip = props.post.ip
    form.device = props.post.device
    form.is_secret = props.post.is_secret
    form.password = props.post.password
    form.is_hide_comment = props.post.is_hide_comment
    form.is_notice = props.post.is_notice
    form.is_blind = props.post.is_blind
    form.links = props.post.links
    form.files = props.post.files
  }
}

onMounted(() => dataSetup())
onUpdated(() => dataSetup())
</script>

<template>
  <CRow class="mt-5">
    <CCol>
      <h5>
        {{ sortName }}
        <v-icon icon="mdi-chevron-double-right" size="xs" />
        {{ viewRoute.substring(3) }}
      </h5>
    </CCol>
  </CRow>

  <v-divider />

  <CForm
    enctype="multipart/form-data"
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="onSubmit"
  >
    <CRow class="mb-3">
      <CFormLabel for="title" class="col-md-2 col-form-label">제목</CFormLabel>
      <CCol :md="boardNum === 3 ? 9 : 8">
        <CFormInput id="title" v-model="form.title" required placeholder="게시물 제목" />
      </CCol>
      <CCol v-if="boardNum !== 3">
        <v-checkbox-btn v-model="form.is_notice" label="공지글" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel
        for="category"
        class="col-sm-2 col-form-label"
        :class="{ 'col-lg-1': boardNum === 3 }"
      >
        카테고리
      </CFormLabel>
      <CCol :md="boardNum === 3 ? 2 : 3">
        <CFormSelect id="category" v-model="form.category" required>
          <option value="">카테고리 선택</option>
          <option v-for="cate in categoryList" :key="cate.pk" :value="cate.pk">
            {{ cate.name }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="title" class="col-md-2 col-form-label">내용</CFormLabel>
      <CCol md="10 mb-5">
        <QuillEditor v-model:content="form.content" placeholder="본문 내용" />
      </CCol>
    </CRow>

    <CRow class="mt-3 bg-success-lighten">
      <CFormLabel for="title" class="col-md-2 col-form-label">링크</CFormLabel>
      <CCol md="10" lg="8" xl="6">
        <CRow v-if="post && form.links?.length">
          <CAlert :color="AlertSecondary">
            <CCol>
              <CInputGroup v-for="(link, i) in form.links" :key="link.pk" class="mb-2">
                <CFormInput
                  :id="`post-link-${link.pk}`"
                  v-model="form.links[i].link"
                  size="sm"
                  placeholder="파일 링크"
                  @input="enableStore"
                />
                <CInputGroupText id="basic-addon1" class="py-0">
                  <CFormCheck
                    :id="`del-link-${link.pk}`"
                    v-model="form.links[i].del"
                    :value="true"
                    @input="enableStore"
                    label="삭제"
                  />
                </CInputGroupText>
              </CInputGroup>
            </CCol>
          </CAlert>
        </CRow>

        <CRow class="mb-2">
          <CCol>
            <CInputGroup v-for="lNum in newLinkRange" :key="`ln-${lNum}`" class="mb-2">
              <CFormInput
                :id="`link-${lNum}`"
                v-model="newLinks[lNum]"
                placeholder="파일 링크"
                @input="enableStore"
              />
              <CInputGroupText id="basic-addon1" @click="ctlLinkNum(lNum)">
                <v-icon
                  :icon="`mdi-${lNum + 1 < newLinkNum ? 'minus' : 'plus'}-thick`"
                  :color="lNum + 1 < newLinkNum ? 'error' : 'primary'"
                />
              </CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="title" class="col-md-2 col-form-label">파일</CFormLabel>
      <CCol md="10" lg="8" xl="6">
        <CRow v-if="post && form.files?.length">
          <CAlert :color="AlertSecondary">
            <small>{{ devideUri(form.files[0].file ?? ' ')[0] }}</small>
            <CCol v-for="(file, i) in form.files" :key="file.pk" xs="12" color="primary">
              <small>
                현재 :
                <a :href="file.file" target="_blank">
                  {{ devideUri(file.file ?? ' ')[1] }}
                </a>
                <span>
                  <CFormCheck
                    v-model="form.files[i].del"
                    :id="`del-file-${file.pk}`"
                    @input="enableStore"
                    label="삭제"
                    inline
                    :disabled="form.files[i].edit"
                    class="ml-4"
                  />
                  <CFormCheck
                    :id="`edit-file-${file.pk}`"
                    label="변경"
                    inline
                    @click="editFile(i)"
                  />
                </span>
                <CRow v-if="form.files[i].edit">
                  <CCol>
                    <CInputGroup>
                      변경 : &nbsp;
                      <CFormInput
                        :id="`post-file-${file.pk}`"
                        v-model="form.files[i].newFile"
                        size="sm"
                        type="file"
                        @input="fileChange($event, file.pk as number)"
                      />
                    </CInputGroup>
                  </CCol>
                </CRow>
              </small>
            </CCol>
          </CAlert>
        </CRow>

        <CRow class="mb-2">
          <CCol>
            <CInputGroup v-for="fNum in newFileRange" :key="`fn-${fNum}`" class="mb-2">
              <CFormInput :id="`file-${fNum}`" type="file" @input="fileUpload" />
              <CInputGroupText id="basic-addon2" @click="ctlFileNum(fNum)">
                <v-icon
                  :icon="`mdi-${fNum + 1 < newFileNum ? 'minus' : 'plus'}-thick`"
                  :color="fNum + 1 < newFileNum ? 'error' : 'primary'"
                />
              </CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol class="text-right">
        <v-btn color="light" @click="router.push({ name: `${viewRoute}` })"> 목록으로</v-btn>
        <v-btn v-if="route.params.postId" color="light" @click="router.go(-1)"> 뒤로</v-btn>
        <!--        <v-btn :color="btnClass" type="submit" :disabled="formsCheck"> 저장하기</CButton>-->
        <v-btn color="warning" type="submit" disabled> 업데이트 중 ...</v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> {{ viewRoute }}</template>
    <template #default>현재 삭제 기능이 구현되지 않았습니다.</template>
    <template #footer>
      <v-btn color="warning" size="small" disabled>삭제</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> {{ viewRoute }}</template>
    <template #default> {{ viewRoute }} 저장을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn :color="btnClass" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
