<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, type PropType, reactive, ref, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { ProjectFilter, selectProject } from '@/store/types/work_project.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import AllProjectsSelect from '@/views/_Work/components/atomics/AllProjectsSelect.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  allProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  targetType: {
    type: String as PropType<'project' | 'calendar' | 'issue' | 'meeting'>,
    default: 'project',
  },
})

const emit = defineEmits(['filter-submit', 'change-view-mode'])

const refQuerySaveModal = ref()

const { can, PERM } = usePerms()
const informStore = useInform()

const viewMode = ref<'board' | 'list'>(
  (localStorage.getItem('project-view-mode') as 'board' | 'list') || 'board',
)

watch(viewMode, nVal => {
  localStorage.setItem('project-view-mode', nVal)
  emit('change-view-mode', nVal)
})

const condVisible = ref(true)
const optVisible = ref(false)

const searchCond = ref(['status'])
const resetFilter = () => {
  searchCond.value = ['status']
  cond.value = {
    status: 'is',
    project: 'is',
    parent: 'all',
    is_public: 'is',
    created: 'is',
    updated: 'is',
    name: 'contains',
    description: 'contains',
  }
  form.value = {
    status: '1',
    is_public: '1',
    created_date: '',
    created_date2: '',
    updated_date: '',
    updated_date2: '',
    name: '',
    description: '',
    bookmark: undefined,
    my_project: undefined,
  }
  selectedProjectVal.value = ''
  if (props.allProjects.length) {
    selectedParentVal.value = props.allProjects[0]?.value
  }
  filterSubmit()
}

const searchOptions = reactive([
  {
    options: [
      { value: 'status', label: '상태', disabled: true },
      { value: 'project', label: '프로젝트' },
      { value: 'parent', label: '상위 프로젝트' },
      { value: 'is_public', label: '공개여부' },
    ],
  },
  {
    label: '문자열 검색',
    options: [
      { value: 'name', label: '\u00A0\u00A0\u00A0이름' },
      { value: 'description', label: '\u00A0\u00A0\u00A0설명' },
    ],
  },
  {
    label: '날짜',
    options: [
      { value: 'created', label: '\u00A0\u00A0\u00A0등록일' },
      { value: 'updated', label: '\u00A0\u00A0\u00A0수정일' },
    ],
  },
])

const cond = ref({
  status: 'is' as 'is' | 'exclude',
  project: 'is' as 'is' | 'exclude',
  parent: 'all' as 'all' | 'none' | 'is' | 'exclude',
  is_public: 'is' as 'is' | 'exclude',
  created: 'is' as 'is' | 'gte' | 'lte' | 'between',
  updated: 'is' as 'is' | 'gte' | 'lte' | 'between',

  name: 'contains',
  description: 'contains',
})

const form = ref<ProjectFilter>({
  status: '1',
  is_public: '1',

  created_date: '',
  created_date2: '',
  updated_date: '',
  updated_date2: '',

  name: '',
  description: '',

  bookmark: undefined,
  my_project: undefined,
})

const selectedProjectVal = ref<number | string>('')
const selectedParentVal = ref<number | string>('')

const filterSubmit = () => {
  const filterData = {} as ProjectFilter

  if (cond.value.status === 'is') filterData.status = form.value.status
  else if (cond.value.status === 'exclude') filterData.status__exclude = form.value.status

  if (searchCond.value.includes('project')) {
    if (selectedProjectVal.value === '') {
      if (cond.value.project === 'is') {
        filterData.my_project = true
      } else if (cond.value.project === 'exclude') {
        filterData.my_project = false
      }
    } else {
      const selectedProj = props.allProjects.find(p => p.value === Number(selectedProjectVal.value))
      const projectVal = selectedProj ? selectedProj.slug : String(selectedProjectVal.value)

      if (cond.value.project === 'is') filterData.project = projectVal
      else if (cond.value.project === 'exclude') filterData.project__exclude = projectVal
    }
  }

  if (searchCond.value.includes('parent')) {
    if (cond.value.parent === 'all') {
      filterData.parent__isnull = false
    } else if (cond.value.parent === 'none') {
      filterData.parent__isnull = true
    } else if (cond.value.parent === 'is') {
      const selectedParent = props.allProjects.find(
        p => p.value === Number(selectedParentVal.value),
      )
      filterData.parent = selectedParent ? selectedParent.slug : String(selectedParentVal.value)
    } else if (cond.value.parent === 'exclude') {
      const selectedParent = props.allProjects.find(
        p => p.value === Number(selectedParentVal.value),
      )
      filterData.parent__exclude = selectedParent
        ? selectedParent.slug
        : String(selectedParentVal.value)
    }
  }

  if (searchCond.value.includes('is_public'))
    if (cond.value.is_public === 'is' && searchCond.value.includes('is_public'))
      filterData.is_public = form.value.is_public
    else if (cond.value.is_public === 'exclude' && searchCond.value.includes('is_public'))
      filterData.is_public__exclude = form.value.is_public

  if (searchCond.value.includes('name')) {
    if (cond.value.name === 'none') {
      filterData.name__isnull = true
    } else if (cond.value.name === 'any') {
      filterData.name__isnull = false
    } else if (form.value.name) {
      if (cond.value.name === 'contains') filterData.name = form.value.name
      else if (cond.value.name === 'exclude') filterData.name__exclude = form.value.name
      else if (cond.value.name === 'startswith') filterData.name__startswith = form.value.name
      else if (cond.value.name === 'endswith') filterData.name__endswith = form.value.name
    }
  }

  if (searchCond.value.includes('description')) {
    if (cond.value.description === 'none') {
      filterData.description__isnull = true
    } else if (cond.value.description === 'any') {
      filterData.description__isnull = false
    } else if (form.value.description) {
      if (cond.value.description === 'contains') filterData.description = form.value.description
      else if (cond.value.description === 'exclude')
        filterData.description__exclude = form.value.description
      else if (cond.value.description === 'startswith')
        filterData.description__startswith = form.value.description
      else if (cond.value.description === 'endswith')
        filterData.description__endswith = form.value.description
    }
  }

  if (searchCond.value.includes('created')) {
    if (cond.value.created === 'is' && form.value.created_date) {
      filterData.from_created = form.value.created_date
      filterData.to_created = form.value.created_date
    } else if (cond.value.created === 'gte' && form.value.created_date) {
      filterData.from_created = form.value.created_date
    } else if (cond.value.created === 'lte' && form.value.created_date) {
      filterData.to_created = form.value.created_date
    } else if (
      cond.value.created === 'between' &&
      form.value.created_date &&
      form.value.created_date2
    ) {
      filterData.from_created = form.value.created_date
      filterData.to_created = form.value.created_date2
    }
  }

  if (searchCond.value.includes('updated')) {
    if (cond.value.updated === 'is' && form.value.updated_date) {
      filterData.from_updated = form.value.updated_date
      filterData.to_updated = form.value.updated_date
    } else if (cond.value.updated === 'gte' && form.value.updated_date) {
      filterData.from_updated = form.value.updated_date
    } else if (cond.value.updated === 'lte' && form.value.updated_date) {
      filterData.to_updated = form.value.updated_date
    } else if (
      cond.value.updated === 'between' &&
      form.value.updated_date &&
      form.value.updated_date2
    ) {
      filterData.from_updated = form.value.updated_date
      filterData.to_updated = form.value.updated_date2
    }
  }

  // 검색 양식 필터(bookmark, my_project)를 직접 필터데이터에 매핑
  if (form.value.bookmark !== undefined) filterData.bookmark = form.value.bookmark
  if (form.value.my_project !== undefined) filterData.my_project = form.value.my_project

  emit('filter-submit', filterData)
}

watch(searchCond, nVal => {
  if (!nVal.includes('status')) searchCond.value = ['status']
})

onBeforeMount(() => {
  selectedProjectVal.value = ''
  if (props.allProjects.length) {
    selectedParentVal.value = props.allProjects[0]?.value
  }
})

// 검색양식 관련 기능 구현
const queryName = ref('')
const queryDescription = ref('')
const isPublic = ref(false)

const myQueries = computed(() =>
  informStore.queries.filter(q => !q.is_public && q.target_type === props.targetType),
)
const publicQueries = computed(() =>
  informStore.queries.filter(q => q.is_public && q.target_type === props.targetType),
)

onMounted(() => {
  informStore.fetchQueries({ targetType: props.targetType })
})

const openSaveModal = () => {
  queryName.value = ''
  queryDescription.value = ''
  isPublic.value = false
  refQuerySaveModal.value.callModal()
}

const validated = ref(false)
const saveQuery = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
    return
  }
  validated.value = false

  // if (!queryName.value.trim()) return

  const payload = {
    name: queryName.value,
    description: queryDescription.value,
    target_type: props.targetType,
    is_public: isPublic.value,
    project: null,
    filters: {
      searchCond: searchCond.value,
      cond: cond.value,
      form: {
        ...form.value,
        project: selectedProjectVal.value,
        parent: selectedParentVal.value,
      },
    },
  }

  await informStore.createQuery(payload)
  await informStore.fetchQueries({ targetType: props.targetType })
  refQuerySaveModal.value.close()
}

const applyQuery = (query: any) => {
  if (query && query.filters) {
    const f = query.filters

    // 이전 필터 상태 완전 초기화
    searchCond.value = ['status']
    cond.value = {
      status: 'is',
      project: 'is',
      parent: 'all',
      is_public: 'is',
      created: 'is',
      updated: 'is',
      name: 'contains',
      description: 'contains',
    }
    form.value = {
      status: '1',
      is_public: '1',
      created_date: '',
      created_date2: '',
      updated_date: '',
      updated_date2: '',
      name: '',
      description: '',
      bookmark: undefined,
      my_project: undefined,
    }
    selectedProjectVal.value = ''
    if (props.allProjects.length) {
      selectedParentVal.value = props.allProjects[0]?.value
    }

    if (f.searchCond) searchCond.value = f.searchCond
    if (f.cond) cond.value = { ...cond.value, ...f.cond }
    if (f.form) {
      form.value = { ...form.value, ...f.form }
      if (f.form.project !== undefined) selectedProjectVal.value = f.form.project
      if (f.form.parent !== undefined) selectedParentVal.value = f.form.parent
    } else {
      // seeds-data.json 처럼 플랫한 필터 구조일 경우 처리
      if (f.bookmark !== undefined) form.value.bookmark = f.bookmark
      if (f.my_project !== undefined) form.value.my_project = f.my_project
    }

    filterSubmit()
  }
}

const onQuerySelect = (event: Event) => {
  const select = event.target as HTMLSelectElement
  const queryId = Number(select.value)
  if (!queryId) return

  const query = informStore.queries.find(q => q.pk === queryId)
  if (query) {
    applyQuery(query)
  }
}

defineExpose({ applyQuery, resetFilter })
</script>

<template>
  <CRow>
    <CCol class="pointer pt-1 mb-0" @click="condVisible = !condVisible">
      <v-icon :icon="condVisible ? 'mdi-chevron-down' : 'mdi-chevron-right'" size="sm" />
      검색조건
    </CCol>
    <v-divider class="mx-3 mt-2 mb-0" />

    <CCollapse :visible="condVisible">
      <slot name="condition">
        <CRow class="m-2" color="light">
          <CCol class="col-12 col-md-8">
            <CRow>
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck label="상태" id="status" checked="true" readonly />
              </CCol>
              <CCol class="d-none d-lg-block col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.status" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormSelect v-model="form.status" size="sm">
                  <option value="1">사용중</option>
                  <option value="9">잠금보관</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('project')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="프로젝트" id="project" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.project" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <AllProjectsSelect
                  v-model="selectedProjectVal"
                  :all-projects="allProjects"
                  default-title="<< 내 프로젝트 >>"
                  size="sm"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('parent')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="상위 프로젝트" id="parent" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.parent" size="sm">
                  <option value="all">모두</option>
                  <option value="none">없음</option>
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <AllProjectsSelect
                  v-if="cond.parent === 'is' || cond.parent === 'exclude'"
                  v-model="selectedParentVal"
                  :all-projects="allProjects"
                  default-title="---------"
                  size="sm"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('is_public')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="공개여부" id="is_public" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.is_public" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormSelect v-model="form.is_public" size="sm">
                  <option value="1">예</option>
                  <option value="0">아니오</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('name')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="이름" id="name" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.name" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                  <option value="startswith">앞문자 일치</option>
                  <option value="endswith">뒷문자 일치</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormInput
                  v-if="cond.name !== 'none' && cond.name !== 'any'"
                  v-model="form.name"
                  placeholder="키워드 입력"
                  size="sm"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('description')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="설명" id="description" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.description" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                  <option value="startswith">앞문자 일치</option>
                  <option value="endswith">뒷문자 일치</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormInput
                  v-if="cond.description !== 'none' && cond.description !== 'any'"
                  v-model="form.description"
                  placeholder="키워드 입력"
                  size="sm"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('created')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="등록일" id="created" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.created" size="sm">
                  <option value="is">이다</option>
                  <option value="gte">&gt;=</option>
                  <option value="lte">&lt;=</option>
                  <option value="between">사이</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <DatePicker v-model="form.created_date" size="sm" />
              </CCol>
              <CCol v-if="cond.created === 'between'" class="col-4 col-lg-3">
                <DatePicker v-model="form.created_date2" size="sm" />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('updated')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="수정일" id="updated" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.updated" size="sm">
                  <option value="is">이다</option>
                  <option value="gte">&gt;=</option>
                  <option value="lte">&lt;=</option>
                  <option value="between">사이</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <DatePicker v-model="form.updated_date" size="sm" />
              </CCol>
              <CCol v-if="cond.updated === 'between'" class="col-4 col-lg-3">
                <DatePicker v-model="form.updated_date2" size="sm" />
              </CCol>
            </CRow>
          </CCol>

          <CCol md="4" class="text-right">
            <CRow>
              <CFormLabel
                for="searchOptions"
                class="col-4 col-lg-2 col-xl-4 col-xxl-5 col-form-label d-block d-md-none d-lg-block"
              >
                검색조건 추가
              </CFormLabel>
              <CCol class="col-8 col-md-12 col-lg-10 col-xl-8 col-xxl-7">
                <Multiselect
                  mode="tags"
                  v-model="searchCond"
                  id="searchOptions"
                  :groups="true"
                  :options="searchOptions"
                  size="sm"
                  class="multiselect-blue"
                  placeholder="검색조건 추가"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </slot>
    </CCollapse>
  </CRow>

  <CRow class="mt-2">
    <CCol class="pointer mb-0" @click="optVisible = !optVisible">
      <v-icon :icon="optVisible ? 'mdi-chevron-down' : 'mdi-chevron-right'" size="sm" />
      옵션
    </CCol>
    <v-divider class="mx-3 mt-2 mb-0" />
    <CCollapse :visible="optVisible">
      <slot name="option">
        <CRow class="m-2" color="light">
          <CCol>
            <span class="mr-3">결과 표시 </span>
            <CFormCheck
              v-model="viewMode"
              label="보드"
              name="viewMode"
              id="board-view-mode"
              value="board"
              inline
              type="radio"
            />
            <CFormCheck
              v-model="viewMode"
              label="목록"
              name="viewMode"
              id="list-view-mode"
              value="list"
              inline
              type="radio"
            />
          </CCol>
        </CRow>
      </slot>
    </CCollapse>
  </CRow>

  <CRow class="my-3">
    <CCol>
      <slot name="footer">
        <TextButton
          name="검색"
          icon="mdi-check-bold"
          icon-color="info"
          font-size="1"
          @click="filterSubmit"
        />

        <TextButton
          name="초기화"
          icon="mdi-autorenew"
          icon-color="info"
          font-size="1"
          @click="resetFilter"
        />

        <TextButton
          v-if="can(PERM.PROJECT_SAVE_QUERY)"
          name="검색양식 저장"
          icon="mdi-content-save"
          icon-color="indigo"
          font-size="1"
          @click="openSaveModal"
        />

        <CFormSelect
          v-if="myQueries.length || publicQueries.length"
          class="d-inline-block ml-3"
          style="width: auto; max-width: 250px; vertical-align: middle"
          size="sm"
          @change="onQuerySelect"
        >
          <option value="">-- 검색양식 선택 --</option>
          <optgroup v-if="myQueries.length" label="내 검색양식">
            <option v-for="q in myQueries" :key="q.pk" :value="q.pk">
              {{ q.name }}
            </option>
          </optgroup>
          <optgroup v-if="publicQueries.length" label="공용 검색양식">
            <option v-for="q in publicQueries" :key="q.pk" :value="q.pk">
              {{ q.name }}
            </option>
          </optgroup>
        </CFormSelect>
      </slot>
    </CCol>
  </CRow>

  <FormModal ref="refQuerySaveModal" size="lg">
    <template #header>검색양식 저장</template>
    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="saveQuery">
      <CModalBody class="text-body">
        <CRow class="mb-3">
          <CFormLabel for="query-name" class="col-3 col-form-label required text-right">
            이름
          </CFormLabel>
          <CCol class="col-7">
            <CFormInput id="query-name" v-model="queryName" placeholder="검색양식 이름" required />
          </CCol>
        </CRow>
        <CRow class="mb-3">
          <CFormLabel for="query-desc" class="col-3 col-form-label text-right"> 설명 </CFormLabel>
          <CCol class="col-7">
            <CFormInput id="query-desc" v-model="queryDescription" placeholder="검색양식 설명" />
          </CCol>
        </CRow>
        <CRow class="mb-3" v-if="can(PERM.PROJECT_PUB_QUERY)">
          <CCol class="offset-3 col-7">
            <CFormCheck id="query-is-public" v-model="isPublic" label="공용 (프로젝트 내 공유)" />
          </CCol>
        </CRow>
        <CRow class="mb-3">
          <CFormLabel for="modalSearchOptions" class="col-3 col-form-label text-right">
            검색 조건 추가
          </CFormLabel>
          <CCol class="col-7 pt-1">
            <Multiselect
              id="modalSearchOptions"
              v-model="searchCond"
              mode="tags"
              placeholder="검색조건 추가"
              :options="searchOptions"
              :groups="true"
              :close-on-select="false"
              :searchable="false"
              :create-option="false"
              size="sm"
            />
          </CCol>
        </CRow>

        <v-divider class="my-4" />
        <h6 class="mb-3 text-indigo">
          <v-icon icon="mdi-filter-cog" class="mr-2" size="small" />
          저장될 검색 조건 설정
        </h6>

        <div class="px-3 py-2 border rounded bg-light">
          <!-- 상태 -->
          <CRow class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>상태</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.status" size="sm">
                <option value="is">이다</option>
                <option value="exclude">아니다</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-4">
              <CFormSelect v-model="form.status" size="sm">
                <option value="1">사용중</option>
                <option value="9">잠금/닫힘</option>
              </CFormSelect>
            </CCol>
          </CRow>

          <!-- 프로젝트 -->
          <CRow v-if="searchCond.includes('project')" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>프로젝트</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.project" size="sm">
                <option value="is">이다</option>
                <option value="exclude">아니다</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-4">
              <AllProjectsSelect
                v-model="selectedProjectVal"
                :all-projects="allProjects"
                default-title="<< 내 프로젝트 >>"
                size="sm"
              />
            </CCol>
          </CRow>

          <!-- 상위 프로젝트 -->
          <CRow v-if="searchCond.includes('parent')" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>상위 프로젝트</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.parent" size="sm">
                <option value="all">모두</option>
                <option value="none">없음</option>
                <option value="is">이다</option>
                <option value="exclude">아니다</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-4">
              <AllProjectsSelect
                v-if="cond.parent === 'is' || cond.parent === 'exclude'"
                v-model="selectedParentVal"
                :all-projects="allProjects"
                default-title="---------"
                size="sm"
              />
            </CCol>
          </CRow>

          <!-- 공개여부 -->
          <CRow v-if="searchCond.includes('is_public')" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>공개여부</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.is_public" size="sm">
                <option value="is">이다</option>
                <option value="exclude">아니다</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-4">
              <CFormSelect v-model="form.is_public" size="sm">
                <option value="1">예</option>
                <option value="0">아니오</option>
              </CFormSelect>
            </CCol>
          </CRow>

          <!-- 이름 -->
          <CRow v-if="searchCond.includes('name')" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>이름</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.name" size="sm">
                <option value="contains">포함되는 키워드</option>
                <option value="exclude">포함하지 않는 키워드</option>
                <option value="startswith">앞문자 일치</option>
                <option value="endswith">뒷문자 일치</option>
                <option value="none">없음</option>
                <option value="any">모두</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-4">
              <CFormInput
                v-if="cond.name !== 'none' && cond.name !== 'any'"
                v-model="form.name"
                placeholder="키워드 입력"
                size="sm"
              />
            </CCol>
          </CRow>

          <!-- 설명 -->
          <CRow v-if="searchCond.includes('description')" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>설명</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.description" size="sm">
                <option value="contains">포함되는 키워드</option>
                <option value="exclude">포함하지 않는 키워드</option>
                <option value="startswith">앞문자 일치</option>
                <option value="endswith">뒷문자 일치</option>
                <option value="none">없음</option>
                <option value="any">모두</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-4">
              <CFormInput
                v-if="cond.description !== 'none' && cond.description !== 'any'"
                v-model="form.description"
                placeholder="키워드 입력"
                size="sm"
              />
            </CCol>
          </CRow>

          <!-- 등록일자 -->
          <CRow v-if="searchCond.includes('created')" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>등록일자</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.created" size="sm">
                <option value="is">이다</option>
                <option value="gte">&gt;=</option>
                <option value="lte">&lt;=</option>
                <option value="between">사이</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-3">
              <DatePicker v-model="form.created_date" size="sm" />
            </CCol>
            <CCol v-if="cond.created === 'between'" class="col-3">
              <DatePicker v-model="form.created_date2" size="sm" />
            </CCol>
          </CRow>

          <!-- 수정일자 -->
          <CRow v-if="searchCond.includes('updated')" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>수정일자</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.updated" size="sm">
                <option value="is">이다</option>
                <option value="gte">&gt;=</option>
                <option value="lte">&lt;=</option>
                <option value="between">사이</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-3">
              <DatePicker v-model="form.updated_date" size="sm" />
            </CCol>
            <CCol v-if="cond.updated === 'between'" class="col-3">
              <DatePicker v-model="form.updated_date2" size="sm" />
            </CCol>
          </CRow>
        </div>
      </CModalBody>
      <CModalFooter>
        <v-btn type="submit" size="small" color="indigo" class="text-white">저장</v-btn>
        <v-btn color="light" size="small" @click="refQuerySaveModal.close()" flat>닫기</v-btn>
      </CModalFooter>
    </CForm>
  </FormModal>
</template>
