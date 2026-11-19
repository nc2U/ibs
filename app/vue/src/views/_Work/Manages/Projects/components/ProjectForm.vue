<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { usePerms } from '@/composables/usePerms'
import { useCompany } from '@/store/pinia/company'
import { useIssue } from '@/store/pinia/work_issue'
import { useWork } from '@/store/pinia/work_project'
import { colorLight } from '@/utils/cssMixins'
import { errorHandle, isValidate } from '@/utils/helper'
import type { IssueProject } from '@/store/types/work_project'
import MdEditor from '@/components/MdEditor/Index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'

const props = defineProps({
  project: { type: Object as PropType<IssueProject | null>, default: null },
})

const { can, canGlobal, PERM } = usePerms()

const canProjectCreate = computed(() => canGlobal(PERM.PROJECT_CREATE))
const canProjectCreateSub = computed(() => canGlobal(PERM.PROJECT_CREATE_SUB))
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const canProjectPublic = computed(() => can(PERM.PROJECT_PUBLIC))

const validated = ref(false)
const isApplyingCopy = ref(false)

const comStore = useCompany()
const comSelect = computed(() => comStore.comSelect)

const workStore = useWork()
const excludedParentPks = computed(() => {
  const excluded = new Set<number>()
  if (!props.project?.pk) return excluded
  excluded.add(props.project.pk)
  const all = workStore.allReadableProjects
  let added = true
  while (added) {
    added = false
    for (const p of all) {
      if (p.pk && p.parent && excluded.has(p.parent) && !excluded.has(p.pk)) {
        excluded.add(p.pk)
        added = true
      }
    }
  }
  return excluded
})
const activeProjects = computed(() => {
  const list = workStore.getAllActiveProjects.filter(p => !excludedParentPks.value.has(p.value))
  if (!props.project && !canProjectCreate.value) {
    return list.filter(p => can(PERM.PROJECT_CREATE_SUB, p.pk))
  }
  return list
})
const allRoles = computed(() => workStore.getRoles)

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
  parent: null as number | string | null,
  is_inherit_members: false,
  allowed_roles: [] as number[],
  trackers: [] as number[],
  chat_channel_enabled: true,
  slack_notifications_enabled: false,
})

const normalizedParent = computed<number | null>(() => {
  if (form.parent === null || form.parent === undefined || form.parent === '') return null
  const num = Number(form.parent)
  return Number.isNaN(num) || num <= 0 ? null : num
})

const canProjectModule = computed(() => {
  if (props.project) return can(PERM.PROJECT_MODULE)
  if (normalizedParent.value) return can(PERM.PROJECT_MODULE, normalizedParent.value)
  return canGlobal(PERM.PROJECT_MODULE)
})

const module = reactive({
  meeting: true,
  issue: true,
  news: true,
  document: true,
  forum: true,
  calendar: true,
})

const hasModuleChanges = computed(() => {
  if (!props.project) return true
  return (
    module.meeting !== (props.project.module?.meeting ?? true) ||
    module.issue !== (props.project.module?.issue ?? true) ||
    module.news !== !!props.project.module?.news ||
    module.document !== !!props.project.module?.document ||
    module.forum !== !!props.project.module?.forum ||
    module.calendar !== !!props.project.module?.calendar
  )
})

const hasProjectBodyChanges = computed(() => {
  if (!props.project) return true
  const a = form.company === props.project.company
  const b = form.type === props.project.type
  const c = form.name === props.project.name
  const d = form.description === props.project.description
  const e = (form.homepage || null) === (props.project.homepage || null)
  const g = normalizedParent.value === (props.project.parent ?? null)
  const n = form.is_inherit_members === props.project.is_inherit_members
  const o =
    JSON.stringify([...form.allowed_roles].sort((x, y) => x - y)) ===
    JSON.stringify(
      [...(props.project.allowed_roles?.map(r => r.pk) ?? [])].sort((x, y) => x - y),
    )
  const p =
    JSON.stringify([...form.trackers].sort((x, y) => x - y)) ===
    JSON.stringify([...(props.project.trackers?.map(t => t.pk) ?? [])].sort((x, y) => x - y))
  const q = form.chat_channel_enabled === (props.project.chat_channel_enabled ?? true)
  const r = form.slack_notifications_enabled === props.project.slack_notifications_enabled
  const modSame = !canProjectModule.value || !hasModuleChanges.value

  return !(a && b && c && d && e && g && n && o && p && q && r && modSame)
})

const formsCheck = computed(() => {
  // 1. 권한 체크 로직
  const canSubmit = props.project
    ? canProjectUpdate.value || canProjectPublic.value
    : normalizedParent.value
      ? can(PERM.PROJECT_CREATE_SUB, normalizedParent.value)
      : canProjectCreate.value

  // 2. 권한이 아예 없으면 무조건 비활성화
  if (!canSubmit) return true

  if (props.project) {
    const publicChanged = canProjectPublic.value && form.is_public !== props.project.is_public
    const bodyChanged = canProjectUpdate.value && hasProjectBodyChanges.value
    // 3. 권한은 있지만 변경 사항이 없으면 비활성화
    return !publicChanged && !bodyChanged
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
  if (isValidate(event)) {
    validated.value = true
  } else {
    localStorage.setItem('workSettingMenu', '메인설정')
    const parentVal = normalizedParent.value

    if (props.project?.pk) {
      // 0. 현재 설정된 공개 여부 값을 미리 캡처 (onUpdated/dataSetup에 의한 덮어쓰기 방지)
      const targetPublic = form.is_public
      const originPublic = props.project.is_public

      // 1. 일반 워크스페이스 정보 업데이트 (is_public은 제외, 모듈은 권한+변경 시에만 포함)
      if (canProjectUpdate.value && hasProjectBodyChanges.value) {
        const { is_public: _unusedPublic, ...projectData } = form
        const payload: Record<string, unknown> = {
          ...projectData,
          parent: parentVal,
          is_inherit_members: parentVal ? form.is_inherit_members : false,
          ...(canProjectModule.value && hasModuleChanges.value ? { ...module } : {}),
        }
        const updated = await workStore.updateIssueProject(payload as unknown as IssueProject)
        if (!updated) return
      }

      // 2. 공개 여부 변경 시 별도 액션 호출
      if (targetPublic !== originPublic && canProjectPublic.value) {
        await workStore.toggleProjectPublic(props.project.slug as string)
      }
    } else {
      const payload: Record<string, unknown> = {
        ...form,
        parent: parentVal,
        is_inherit_members: parentVal ? form.is_inherit_members : false,
        ...(canProjectModule.value ? { ...module } : {}),
      }
      const created = await workStore.createIssueProject(payload as unknown as IssueProject)
      if (created?.slug) {
        await router.push({ name: '(설정)', params: { projId: created.slug } })
      }
    }
    validated.value = false
  }
}

const setDefaultRolesAndTrackers = () => {
  if (props.project || isApplyingCopy.value) return

  if (form.type === '1') {
    // 본사관리(1): 전체 역할 및 업무유형 기본 할당
    form.allowed_roles = workStore.roleList.filter(r => ![1, 2, 3].includes(r.pk)).map(r => r.pk)
    form.trackers = issueStore.trackerList.filter(r => ![1, 2, 3].includes(r.pk)).map(t => t.pk)
  } else if (form.type === '2') {
    // 부동산개발 프로젝트(type='2'): is_for_dev_project 플래그가 true인 항목들을 기본 할당
    const devRoles = workStore.roleList.filter(r => r.is_for_dev_project).map(r => r.pk)
    form.allowed_roles = devRoles.length > 0 ? devRoles : workStore.roleList.map(r => r.pk)

    const devTrackers = issueStore.trackerList.filter(t => t.is_for_dev_project).map(t => t.pk)
    form.trackers = devTrackers.length > 0 ? devTrackers : issueStore.trackerList.map(t => t.pk)
  } else {
    // 기타 워크스페이스(3): 전체 역할 및 업무유형 기본 할당
    form.allowed_roles = workStore.roleList.filter(r => [1, 2, 3].includes(r.pk)).map(r => r.pk)
    form.trackers = issueStore.trackerList.filter(r => [1, 2, 3].includes(r.pk)).map(t => t.pk)
  }
}

watch(
  () => form.type,
  () => {
    if (!props.project && !isApplyingCopy.value) {
      setDefaultRolesAndTrackers()
    }
  },
)

watch(normalizedParent, nVal => {
  if (!nVal) form.is_inherit_members = false
})

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
    form.chat_channel_enabled = props.project.chat_channel_enabled ?? true
    form.slack_notifications_enabled = props.project.slack_notifications_enabled

    module.meeting =
      props.project.module?.meeting !== undefined ? !!props.project.module?.meeting : true
    module.issue =
      props.project.module?.issue !== undefined ? !!props.project.module?.issue : true
    module.news = !!props.project.module?.news
    module.document = !!props.project.module?.document
    module.forum = !!props.project.module?.forum
    module.calendar = !!props.project.module?.calendar
  } else {
    if (form.allowed_roles.length === 0 && form.trackers.length === 0) {
      setDefaultRolesAndTrackers()
    }
  }
}

const applyCopySource = async (copyKey: string) => {
  isApplyingCopy.value = true
  try {
    const res = await api.get(`/issue-project/${copyKey}/`)
    const src = res.data as IssueProject
    form.company = src.company
    form.type = src.type
    form.name = `${src.name} (복사본)`
    form.description = src.description ?? ''
    form.slug = ''
    form.homepage = src.homepage ?? null
    form.is_public = src.is_public
    form.parent = src.parent ?? null
    form.is_inherit_members = src.is_inherit_members
    form.allowed_roles = src.allowed_roles?.map(r => r.pk) ?? []
    form.trackers = src.trackers?.map(t => t.pk) ?? []
    form.chat_channel_enabled = src.chat_channel_enabled ?? true
    form.slack_notifications_enabled = src.slack_notifications_enabled ?? false
    if (src.module) {
      module.meeting = !!src.module.meeting
      module.issue = !!src.module.issue
      module.news = !!src.module.news
      module.document = !!src.module.document
      module.forum = !!src.module.forum
      module.calendar = !!src.module.calendar
    }
  } catch (err) {
    errorHandle(err)
  } finally {
    isApplyingCopy.value = false
  }
}

watch(
  () => props.project,
  () => dataSetup(),
  { immediate: true },
)

onBeforeMount(async () => {
  if (!!route.query.parent) form.parent = Number(route.query.parent)
  comStore.fetchCompanyList()
  await Promise.all([workStore.fetchRoleList(), issueStore.fetchTrackerList()])
  if (!props.project) {
    if (route.query.copy) {
      await applyCopySource(String(route.query.copy))
    } else {
      setDefaultRolesAndTrackers()
    }
  }
})
</script>

<template>
  <CRow v-if="!project" class="py-2">
    <CCol>
      <h5>새 워크스페이스</h5>
    </CCol>
  </CRow>

  <slot></slot>

  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow class="mb-3">
          <CFormLabel class="required col-form-label text-end col-2">회사</CFormLabel>
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
              label="기타 워크스페이스"
              value="3"
              v-model="form.type"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="project-name" class="required col-form-label text-end col-2">이름</CFormLabel>
          <CCol>
            <CFormInput
              id="project-name"
              v-model="form.name"
              @keydown="getSlug"
              maxlength="100"
              required
              placeholder="워크스페이스 이름"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-end col-2">설명</CFormLabel>
          <CCol>
            <MdEditor v-model="form.description" placeholder="워크스페이스 설명" />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="project-slug" class="required col-form-label text-end col-2">식별자</CFormLabel>
          <CCol>
            <CFormInput
              id="project-slug"
              v-model="form.slug"
              maxlength="100"
              pattern="[a-z0-9_-]+"
              placeholder="워크스페이스 식별자 (영문 소문자, 숫자, -, _ 문자만 사용)"
              :disabled="!!project?.slug"
              required
              text="1에서 100글자 소문자(a-z), 숫자, 대쉬(-)와 밑줄(_)만 가능합니다. 식별자 저장 후에는 수정할 수 없습니다."
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="project-homepage" class="col-form-label text-end col-2">홈페이지</CFormLabel>
          <CCol>
            <CFormInput id="project-homepage" v-model="form.homepage" maxlength="255" placeholder="홈페이지 URL" />
          </CCol>
        </CRow>

        <CRow v-if="canProjectPublic" class="mb-3">
          <CFormLabel class="col-form-label text-end col-2">공개여부</CFormLabel>
          <CCol style="padding-top: 5px">
            <CFormSwitch v-model="form.is_public" id="is_public" label="워크스페이스 공개 여부" />
            <div class="form-text">
              공개 워크스페이스는 네트워크의 모든 사용자가 접속할 수 있습니다.
            </div>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-end col-2">상위 워크스페이스</CFormLabel>
          <CCol>
            <IssueProjectSelector
              v-model.number.lazy="form.parent"
              :issue-project-list="activeProjects"
              default-title="---------"
              :disabled="project ? !canProjectUpdate : !canProjectCreateSub"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-end col-2">
            상위 워크스페이스 구성원 상속
          </CFormLabel>
          <CCol class="pt-2">
            <CFormSwitch
              v-model="form.is_inherit_members"
              id="is_inherit_members"
              label="상위 워크스페이스 구성원 상속 여부"
              :disabled="!normalizedParent"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-end col-2">허용 역할</CFormLabel>
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
          <CFormLabel class="col-form-label text-end col-2">허용 유형</CFormLabel>
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
          <CFormLabel class="col-form-label text-end col-2">공용 대화방</CFormLabel>
          <CCol style="padding-top: 5px">
            <CFormSwitch
              v-model="form.chat_channel_enabled"
              id="chat_channel_enabled"
              label="실시간 메신저 공용 대화방(#채널) 개설 여부"
            />
            <span class="form-text">
              활성화 시 이 워크스페이스 소속 구성원들을 위한 실시간 메신저 공용 채널이 개설됩니다.
            </span>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-end col-2">슬랙 알림</CFormLabel>
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
      <v-icon icon="mdi-check-bold" size="small" color="success" />
      모듈
    </h6>
    <CCard class="mb-3" :color="colorLight">
      <CCardBody>
        <CRow>
          <CCol sm="6" md="4" lg="3" xl="2">
            <CFormCheck v-model="module.issue" id="issue" label="업무관리" :disabled="true" />
          </CCol>
          <CCol sm="6" md="4" lg="3" xl="2">
            <CFormCheck
              v-model="module.meeting"
              id="meeting"
              label="회의록"
              :disabled="!canProjectModule"
            />
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
      <CCol class="text-end">
        <v-btn type="submit" :color="!project ? 'primary' : 'success'" :disabled="formsCheck">
          저장
        </v-btn>
        <!--        <v-btn color="primary" type="submit">저장 후 계속하기</v-btn>-->
      </CCol>
    </CRow>
  </CForm>
</template>
