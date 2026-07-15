<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, onUpdated, type PropType, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useStore } from '@/store'
import { useCompany } from '@/store/pinia/company'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { colorLight } from '@/utils/cssMixins'
import type { IssueProject } from '@/store/types/work_project.ts'
import MdEditor from '@/components/MdEditor/Index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import AllProjectsSelect from '@/views/_Work/components/atomics/AllProjectsSelect.vue'

const props = defineProps({
  project: { type: Object as PropType<IssueProject | null>, default: null },
  redirect: { type: Boolean, default: true },
})

const emit = defineEmits(['modal-close'])

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const { can, PERM } = usePerms()

const canProjectCreate = computed(() => can(PERM.PROJECT_CREATE))
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const canProjectPublic = computed(() => can(PERM.PROJECT_PUBLIC))
const canProjectModule = computed(() => can(PERM.PROJECT_MODULE))

const validated = ref(false)

const comStore = useCompany()
const comSelect = computed(() => comStore.comSelect)

const workStore = useWork()
const getAllProjects = computed(() =>
  workStore.getAllProjects.filter(p => p.value !== props.project?.pk),
)
const allRoles = computed(() => workStore.getRoles.filter(r => r.value !== 1 && r.value !== 2))

const issueStore = useIssue()
const allTrackers = computed(() => issueStore.getTrackers)

const form = reactive({
  pk: undefined as number | undefined,
  company: null as null | number,
  type: '2',
  name: '',
  description: '',
  slug: '',
  homepage: null as string | null,
  is_public: true,
  parent: null as number | null,
  is_inherit_members: false,
  allowed_roles: [6, 7, 8],
  trackers: [4, 5, 6, 7, 8],
  slack_notifications_enabled: false,
})

const module = reactive({
  issue: true,
  news: true,
  document: true,
  forum: true,
  calendar: true,
})

const formsCheck = computed(() => {
  // 1. 권한 체크 로직
  const canSubmit = props.project
    ? canProjectUpdate.value
    : form.parent
      ? can(PERM.PROJECT_CREATE_SUB)
      : canProjectCreate.value

  // 2. 권한이 아예 없으면 무조건 비활성화
  if (!canSubmit) return true

  if (props.project) {
    const a = form.company === props.project.company
    const b = form.type === props.project.type
    const c = form.name === props.project.name
    const d = form.description === props.project.description
    const e = form.homepage === props.project.homepage

    // 공개여부 변경은 권한이 있을 때만 체크
    const f = !canProjectPublic.value || form.is_public === props.project.is_public

    const g = Number(form.parent) === Number(props.project.parent)
    const h = form.is_inherit_members === props.project.is_inherit_members
    const i =
      // eslint-disable-next-line vue/no-side-effects-in-computed-properties
      JSON.stringify(form.allowed_roles.sort((a, b) => a - b)) ===
      JSON.stringify(props.project.allowed_roles?.map(r => r.pk).sort((a, b) => a - b))
    const j =
      // eslint-disable-next-line vue/no-side-effects-in-computed-properties
      JSON.stringify(form.trackers.sort((a, b) => a - b)) ===
      JSON.stringify(props.project.trackers?.map(t => t.pk).sort((a, b) => a - b))

    // 모듈 변경 체크는 권한이 있을 때만
    const l = !canProjectModule.value || module.issue === props.project.module?.issue
    const n = !canProjectModule.value || module.news === props.project.module?.news
    const o = !canProjectModule.value || module.document === props.project.module?.document
    const r = !canProjectModule.value || module.forum === props.project.module?.forum
    const s = !canProjectModule.value || module.calendar === props.project.module?.calendar
    const t = form.slack_notifications_enabled === props.project.slack_notifications_enabled

    const first = a && b && c && d && e && f && g && h && i && j
    const second = l && n && o && r && s && t

    // 3. 권한은 있지만 변경 사항이 없으면 비활성화
    return first && second
  }
  // 4. 생성의 경우 권한이 있다면 활성화(false 반환)
  return false
})

const tempSpace = ref('')

const getSlug = (event: { key: string; code: string }) => {
  if (!props.project?.slug) {
    const pattern = /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/ //한글

    let slug = form.slug.length === 0 ? '' : form.slug

    if (event.code === 'Backspace') {
      if (slug.length >= form.name.length) slug = slug.slice(0, -1)
    } else if (event.code === 'Space') tempSpace.value = !!slug.length ? '-' : ''
    else if (
      event.code.includes('Digit') ||
      (event.code.includes('Key') && event.key.length === 1 && !pattern.test(event.key))
    ) {
      if (event.key !== 'Process') {
        slug = slug + tempSpace.value + event.key.toLowerCase()
        tempSpace.value = ''
      }
    }

    form.slug = slug
  }
}

const [route, router] = [useRoute(), useRouter()]

const onSubmit = async (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()
    validated.value = true
  } else {
    localStorage.setItem('workSettingMenu', '프로젝트')

    if (form.pk) {
      // 1. 일반 프로젝트 정보 업데이트 (is_public은 제외하고 업데이트)
      const { is_public, ...projectData } = form
      await workStore.updateIssueProject({ ...projectData, ...module } as any)

      // 2. 공개 여부 변경 시 별도 액션 호출
      if (props.project && form.is_public !== props.project.is_public) {
        if (canProjectPublic.value) {
          await workStore.toggleProjectPublic(props.project.slug as string)
        }
      }
    } else {
      await workStore.createIssueProject({ ...form, ...module } as any)
      if (props.redirect)
        await router.push({
          name: '(설정)',
          params: { projId: (workStore.issueProject as IssueProject)?.slug },
        })
      else emit('modal-close')
    }
    validated.value = false
  }
}

const dataSetup = () => {
  if (props.project) {
    form.pk = props.project.pk
    form.company = props.project.company
    form.type = props.project.type
    form.name = props.project.name
    form.description = props.project.description
    form.slug = props.project.slug
    form.homepage = props.project.homepage
    form.is_public = props.project.is_public
    form.parent = props.project.parent
    form.is_inherit_members = props.project.is_inherit_members
    form.allowed_roles = props.project.allowed_roles?.map(r => r.pk) ?? []
    form.trackers = props.project.trackers?.map(t => t.pk) ?? []
    form.slack_notifications_enabled = props.project.slack_notifications_enabled

    module.issue = true
    module.news = !!props.project.module?.news
    module.document = !!props.project.module?.document
    module.forum = !!props.project.module?.forum
    module.calendar = !!props.project.module?.calendar
  }
}

const types = ref([
  { value: '1', label: '본사관리' },
  { value: '2', label: '부동산개발' },
  { value: '3', label: '기타 프로젝트' },
])

onMounted(() => dataSetup())
onUpdated(() => dataSetup())

onBeforeMount(() => {
  if (!!route.query.parent) form.parent = Number(route.query.parent)
  comStore.fetchCompanyList()
  workStore.fetchRoleList()
  issueStore.fetchTrackerList()
})
</script>

<template>
  <CRow v-if="!project" class="py-2">
    <CCol>
      <h5>새 프로젝트</h5>
    </CCol>
  </CRow>

  <slot></slot>

  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow class="mb-3">
          <CFormLabel class="required col-form-label text-right col-2">회사</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <MultiSelect
              v-model="form.company"
              :options="comSelect"
              mode="single"
              placeholder="회사 선택"
              :attrs="form.company ? {} : { required: true }"
              required
            />
          </CCol>
          <CCol class="mt-2">
            <CFormCheck
              type="radio"
              id="type-1"
              inline
              label="본사관리"
              value="1"
              v-model="form.type"
            />
            <CFormCheck
              type="radio"
              id="type-2"
              inline
              label="부동산개발 프로젝트"
              value="2"
              v-model="form.type"
            />
            <CFormCheck
              type="radio"
              id="type-3"
              inline
              label="기타 프로젝트"
              value="3"
              v-model="form.type"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="required col-form-label text-right col-2">이름</CFormLabel>
          <CCol>
            <CFormInput
              v-model="form.name"
              @keydown="getSlug"
              maxlength="100"
              required
              placeholder="프로젝트 이름"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">설명</CFormLabel>
          <CCol>
            <MdEditor v-model="form.description" placeholder="프로젝트 설명" />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="required col-form-label text-right col-2">식별자</CFormLabel>
          <CCol>
            <CFormInput
              v-model="form.slug"
              maxlength="100"
              placeholder="프로젝트 식별자 (영문, 숫자, - 문자만 사용)"
              :disabled="!!project?.slug"
              required
              text="1에서 100글자 소문자(a-z), 숫자, 대쉬(-)와 밑줄(_)만 가능합니다. 식별자 저장 후에는 수정할 수 없습니다."
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">홈페이지</CFormLabel>
          <CCol>
            <CFormInput v-model="form.homepage" maxlength="255" placeholder="홈페이지 URL" />
          </CCol>
        </CRow>

        <CRow v-if="canProjectPublic" class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">공개여부</CFormLabel>
          <CCol style="padding-top: 5px">
            <CFormSwitch v-model="form.is_public" id="is_public" label="프로젝트 공개 여부" />
            <div class="form-text">
              공개 프로젝트는 네트워크의 모든 사용자가 접속할 수 있습니다.
            </div>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">상위 프로젝트</CFormLabel>
          <CCol>
            <AllProjectsSelect
              v-model.number.lazy="form.parent"
              :all-projects="getAllProjects"
              default-title="---------"
              :disabled="!can(PERM.PROJECT_CREATE_SUB)"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">상위 프로젝트 구성원 상속</CFormLabel>
          <CCol class="pt-2">
            <CFormSwitch
              v-model="form.is_inherit_members"
              id="is_inherit_members"
              label="상위 프로젝트 구성원 상속 여부"
              :disabled="!form.parent"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">허용 역할</CFormLabel>
          <CCol>
            <MultiSelect
              v-model="form.allowed_roles"
              id="allowed_roles"
              :options="allRoles"
              placeholder="허용 역할 항목 선택"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">허용 유형</CFormLabel>
          <CCol>
            <MultiSelect
              v-model="form.trackers"
              id="trackers"
              :options="allTrackers"
              placeholder="허용 유형 항목 선택"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">슬랙 알림</CFormLabel>
          <CCol style="padding-top: 5px">
            <CFormSwitch
              v-model="form.slack_notifications_enabled"
              id="slack_notifications_enabled"
              label="슬랙 알림 사용 여부"
            />
            <span v-if="form.slack_notifications_enabled" class="form-text">
              슬랙 웹훅이 등록된 경우에만 슬랙 알림을 사용할 수 있습니다. 웹훅 등록은 관리자에게
              요청하세요.
            </span>
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <h6>
      <v-icon icon="mdi-check-bold" size="sm" color="success" />
      모듈
    </h6>
    <CCard class="mb-3" :color="!isDark ? 'light' : ''">
      <CCardBody>
        <CRow>
          <CCol sm="6" md="4" lg="3" xl="2">
            <CFormCheck v-model="module.issue" id="issue" label="업무관리" :disabled="true" />
          </CCol>
          <CCol sm="6" md="4" lg="3" xl="2">
            <CFormCheck
              v-model="module.news"
              id="news"
              label="공지"
              :disabled="!canProjectModule"
            />
          </CCol>
          <CCol sm="6" md="4" lg="3" xl="2">
            <CFormCheck
              v-model="module.document"
              id="document"
              label="문서"
              :disabled="!canProjectModule"
            />
          </CCol>
          <CCol sm="6" md="4" lg="3" xl="2">
            <CFormCheck
              v-model="module.forum"
              id="forum"
              label="게시판"
              :disabled="!canProjectModule"
            />
          </CCol>
          <CCol sm="6" md="4" lg="3" xl="2">
            <CFormCheck
              v-model="module.calendar"
              id="calendar"
              label="캘린더"
              :disabled="!canProjectModule"
            />
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <CRow>
      <CCol class="text-right">
        <v-btn type="submit" :color="!project ? 'primary' : 'success'" :disabled="formsCheck">
          저장
        </v-btn>
        <!--        <v-btn color="primary" type="submit">저장 후 계속하기</v-btn>-->
      </CCol>
    </CRow>
  </CForm>
</template>
