<script lang="ts" setup>
import { type ComputedRef, inject, type PropType } from 'vue'
import { ref, reactive, computed, onMounted, onUpdated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Docs, Link, AFile, SuitCase } from '@/store/types/docs'
import type { Company } from '@/store/types/settings'
import { AlertSecondary } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'
import QuillEditor from '@/components/QuillEditor/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ModalCaseForm from '@/components/Documents/ModalCaseForm.vue'

const props = defineProps({
  sortName: { type: String, default: '【본사】' },
  typeNum: { type: Number, default: 1 },
  categoryList: { type: Object, required: true },
  getSuitCase: { type: Object, default: null },
  docs: { type: Object as PropType<Docs>, default: null },
  viewRoute: { type: String, required: true },
  writeAuth: { type: Boolean, default: true },
})

const emit = defineEmits(['on-submit', 'file-upload', 'file-change', 'close'])

const refDelModal = ref()
const refAlertModal = ref()
const refConfirmModal = ref()
const refCaseForm = ref()

const company = inject<ComputedRef<Company>>('company')

const attach = ref(true)
const validated = ref(false)
const form = reactive<Docs>({
  pk: undefined,
  issue_project: null,
  doc_type: props.typeNum,
  category: null,
  lawsuit: null,
  title: '',
  execution_date: null,
  content: '',
  device: '',
  is_secret: false,
  password: '',
  is_blind: false,
  links: [],
  files: [],
})

const newLinks = ref<Link[]>([])

const formsCheck = computed(() => {
  if (props.docs) {
    const a = form.category === props.docs.category
    const b = form.lawsuit === props.docs.lawsuit
    const c = form.title === props.docs.title
    const d = form.execution_date === props.docs.execution_date
    const e = form.content === props.docs.content

    return a && b && c && d && e && attach.value
  } else return false
})

const [route, router] = [useRoute(), useRouter()]
const btnClass = computed(() => (route.params.docsId ? 'success' : 'primary'))

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
  if ((form.files as any[]).length) {
    ;(form.files as any[])[i].del = false
    ;(form.files as any[])[i].edit = !(form.files as any[])[i].edit
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

const caseCreate = (payload: SuitCase) => {
  // case 생성하고
  // 사건번호 폼에서 새로 생성한 case 를 선택 상태로 만들기
  return
}

const devideUri = (uri: string) => {
  const devidedUri = decodeURI(uri).split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1]]
}

const dataSetup = () => {
  if (props.docs) {
    form.pk = props.docs.pk
    form.issue_project = props.docs.issue_project
    form.doc_type = props.docs.doc_type
    form.category = props.docs.category
    form.lawsuit = props.docs.lawsuit
    form.title = props.docs.title
    form.execution_date = props.docs.execution_date
    form.content = props.docs.content
    form.device = props.docs.device
    form.is_secret = props.docs.is_secret
    form.password = props.docs.password
    form.is_blind = props.docs.is_blind
    form.links = props.docs.links
    form.files = props.docs.files
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
      <CCol :md="typeNum === 2 ? 9 : 8">
        <CFormInput id="title" v-model="form.title" required placeholder="게시물 제목" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel v-if="typeNum === 2" for="inputPassword" class="col-sm-2 col-form-label">
        사건번호 (사건번호 등록)
      </CFormLabel>
      <CCol v-if="typeNum === 2" md="2">
        <Multiselect
          v-model="form.lawsuit"
          :options="getSuitCase"
          placeholder="사건번호 선택"
          autocomplete="label"
          :classes="{ search: 'form-control multiselect-search' }"
          :attrs="form.lawsuit ? {} : { required: true }"
          :add-option-on="['enter', 'tab']"
          searchable
        />
      </CCol>
      <CCol v-if="typeNum === 2" md="1" style="padding-top: 7px">
        <div style="width: 20px">
          <v-icon
            icon="mdi-plus-circle"
            color="success"
            class="pointer"
            @click="refCaseForm.callModal()"
          />
          <v-tooltip activator="parent" location="end">새 소송사건 등록하기</v-tooltip>
        </div>
      </CCol>

      <CFormLabel
        for="category"
        class="col-sm-2 col-form-label"
        :class="{ 'col-lg-1': typeNum === 2 }"
      >
        카테고리
      </CFormLabel>
      <CCol :md="typeNum === 2 ? 2 : 3">
        <CFormSelect id="category" v-model="form.category" required>
          <option value="">카테고리 선택</option>
          <option v-for="cate in categoryList" :key="cate.pk" :value="cate.pk">
            {{ cate.name }}
          </option>
        </CFormSelect>
      </CCol>

      <CFormLabel
        for="inputPassword"
        class="col-sm-2 col-form-label"
        :class="{ 'col-lg-1': typeNum === 2 }"
      >
        문서 발행일자
      </CFormLabel>
      <CCol :md="typeNum === 2 ? 2 : 3">
        <DatePicker v-model="form.execution_date" placeholder="문서 발행일자" />
      </CCol>
      <CCol v-if="typeNum !== 2">
        <v-checkbox-btn v-model="form.is_secret" label="비밀글" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="title" class="col-md-2 col-form-label">내용</CFormLabel>
      <CCol md="10 mb-5">
        <QuillEditor v-model:content="form.content" placeholder="본문 내용" />
      </CCol>
    </CRow>

    <CRow>
      <CFormLabel for="title" class="col-md-2 col-form-label">링크</CFormLabel>
      <CCol md="10" lg="8" xl="6">
        <CRow v-if="docs && (form.links as Link[]).length">
          <CAlert :color="AlertSecondary">
            <CCol>
              <CInputGroup v-for="(link, i) in form.links as Link[]" :key="link.pk" class="mb-2">
                <CFormInput
                  :id="`docs-link-${link.pk}`"
                  v-model="(form.links as Link[])[i].link"
                  size="sm"
                  placeholder="파일 링크"
                  @input="enableStore"
                />
                <CInputGroupText id="basic-addon1" class="py-0">
                  <CFormCheck
                    :id="`del-link-${link.pk}`"
                    v-model="(form.links as Link[])[i].del"
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
        <CRow v-if="docs && (form.files as AFile[]).length">
          <CAlert :color="AlertSecondary">
            <small>{{ devideUri((form.files as AFile[])[0]?.file ?? ' ')[0] }}</small>
            <CCol v-for="(file, i) in form.files as AFile[]" :key="file.pk" xs="12" color="primary">
              <small>
                현재 :
                <a :href="file.file" target="_blank">
                  {{ devideUri(file.file ?? ' ')[1] }}
                </a>
                <span>
                  <CFormCheck
                    v-model="(form.files as AFile[])[i].del"
                    :id="`del-file-${file.pk}`"
                    @input="enableStore"
                    label="삭제"
                    inline
                    :disabled="(form.files as AFile[])[i].edit"
                    class="ml-4"
                  />
                  <CFormCheck
                    :id="`edit-file-${file.pk}`"
                    label="변경"
                    inline
                    @click="editFile(i)"
                  />
                </span>
                <CRow v-if="(form.files as AFile[])[i].edit">
                  <CCol>
                    <CInputGroup>
                      변경 : &nbsp;
                      <CFormInput
                        :id="`docs-file-${file.pk}`"
                        v-model="(form.files as AFile[])[i].newFile"
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
        <CButton color="light" @click="router.push({ name: `${viewRoute}` })"> 목록으로</CButton>
        <CButton v-if="route.params.docsId" color="light" @click="router.go(-1)"> 뒤로</CButton>
        <CButton :color="btnClass" type="submit" :disabled="formsCheck"> 저장하기</CButton>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> {{ viewRoute }}</template>
    <template #default>현재 삭제 기능이 구현되지 않았습니다.</template>
    <template #footer>
      <CButton color="danger" disabled>삭제</CButton>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> {{ viewRoute }}</template>
    <template #default> {{ viewRoute }} 저장을 진행하시겠습니까?</template>
    <template #footer>
      <CButton :color="btnClass" @click="modalAction">저장</CButton>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />

  <ModalCaseForm ref="refCaseForm" @on-submit="caseCreate" />
</template>
