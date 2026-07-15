<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, type PropType, reactive, ref, watch } from 'vue'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { ProjectFilter, selectProject } from '@/store/types/work_project.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import AllProjectsSelect from '@/views/_Work/components/atomics/AllProjectsSelect.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  allProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  targetType: {
    type: String as PropType<'project' | 'calendar' | 'issue' | 'meeting'>,
    default: 'project',
  },
})

const emit = defineEmits(['filter-submit', 'change-view-mode'])

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
      { value: 'created', label: '\u00A0\u00A0\u00A0등록' },
      { value: 'updated', label: '\u00A0\u00A0\u00A0수정' },
    ],
  },
])

const cond = ref({
  status: 'is' as 'is' | 'exclude',
  project: 'is' as 'is' | 'exclude',
  parent: 'all' as 'all' | 'none' | 'is' | 'exclude',
  is_public: 'is' as 'is' | 'exclude',

  name: 'contains',
  description: 'contains',
})

const form = ref<ProjectFilter>({
  status: '1',
  is_public: '1',

  name: '',
  description: '',
})

const selectedProjectVal = ref<number | string>('')
const selectedParentVal = ref<number | string>('')

const filterSubmit = () => {
  const filterData = {} as ProjectFilter

  if (cond.value.status === 'is') filterData.status = form.value.status
  else if (cond.value.status === 'exclude') filterData.status__exclude = form.value.status

  if (searchCond.value.includes('project')) {
    const selectedProj = props.allProjects.find(p => p.value === Number(selectedProjectVal.value))
    const projectVal = selectedProj ? selectedProj.slug : String(selectedProjectVal.value)

    if (cond.value.project === 'is') filterData.project = projectVal
    else if (cond.value.project === 'exclude') filterData.project__exclude = projectVal
  }

  if (searchCond.value.includes('parent')) {
    if (cond.value.parent === 'all') {
      filterData.parent__isnull = false
    } else if (cond.value.parent === 'none') {
      filterData.parent__isnull = true
    } else if (cond.value.parent === 'is') {
      const selectedParent = props.allProjects.find(p => p.value === Number(selectedParentVal.value))
      filterData.parent = selectedParent ? selectedParent.slug : String(selectedParentVal.value)
    } else if (cond.value.parent === 'exclude') {
      const selectedParent = props.allProjects.find(p => p.value === Number(selectedParentVal.value))
      filterData.parent__exclude = selectedParent ? selectedParent.slug : String(selectedParentVal.value)
    }
  }

  if (searchCond.value.includes('is_public'))
    if (cond.value.is_public === 'is' && searchCond.value.includes('is_public'))
      filterData.is_public = form.value.is_public
    else if (cond.value.is_public === 'exclude' && searchCond.value.includes('is_public'))
      filterData.is_public__exclude = form.value.is_public

  if (searchCond.value.includes('name') && form.value.name) filterData.name = form.value.name
  if (searchCond.value.includes('description') && form.value.description)
    filterData.description = form.value.description

  emit('filter-submit', filterData)
}

watch(searchCond, nVal => {
  if (!nVal.includes('status')) searchCond.value = ['status']
})

onBeforeMount(() => {
  if (props.allProjects.length) {
    selectedProjectVal.value = props.allProjects[0]?.value
    selectedParentVal.value = props.allProjects[0]?.value
  }
})

// 검색양식 관련 기능 구현
const isModalOpen = ref(false)
const queryName = ref('')
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
  isPublic.value = false
  isModalOpen.value = true
}

const saveQuery = async () => {
  if (!queryName.value.trim()) return

  const payload = {
    name: queryName.value,
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
  isModalOpen.value = false
}

const onQuerySelect = (event: Event) => {
  const select = event.target as HTMLSelectElement
  const queryId = Number(select.value)
  if (!queryId) return

  const query = informStore.queries.find(q => q.pk === queryId)
  if (query && query.filters) {
    const f = query.filters
    if (f.searchCond) searchCond.value = f.searchCond
    if (f.cond) cond.value = { ...cond.value, ...f.cond }
    if (f.form) {
      form.value = { ...form.value, ...f.form }
      if (f.form.project !== undefined) selectedProjectVal.value = f.form.project
      if (f.form.parent !== undefined) selectedParentVal.value = f.form.parent
    }

    filterSubmit()
  }
}
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
                  <option value="9">닫힘</option>
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
                  default-title="---------"
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
                  <option value="all">any</option>
                  <option value="none">none</option>
                  <option value="is">is</option>
                  <option value="exclude">is not</option>
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
                  <option value="is">is</option>
                  <option value="exclude">is not</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormSelect v-model="form.is_public" size="sm">
                  <option value="1">예</option>
                  <option value="0">아니오</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('created')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="등록일자" id="created" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect size="sm">
                  <option value="1">is</option>
                  <option value="2">&gt;=</option>
                  <option value="3">&lt;=</option>
                  <option value="4">between</option>
                  <option value="5">less than days ago</option>
                  <option value="6">more than days ago</option>
                  <option value="7">is the past</option>
                  <option value="8">days ago</option>
                  <option value="9">today</option>
                  <option value="10">yesterday</option>
                  <option value="11">this week</option>
                  <option value="12">last week</option>
                  <option value="13">last 2 weeks</option>
                  <option value="14">this month</option>
                  <option value="15">last month</option>
                  <option value="16">this year</option>
                  <option value="17">none</option>
                  <option value="18">any</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <DatePicker size="sm" />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('name')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="이름" id="name" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.name" size="sm">
                  <option value="contains">contains</option>
                  <option value="2" disabled>contains any of</option>
                  <option value="3" disabled>doesn't contain</option>
                  <option value="4" disabled>starts with</option>
                  <option value="5" disabled>ends with</option>
                  <option value="6" disabled>none</option>
                  <option value="7" disabled>any</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormInput v-model="form.name" size="sm" />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('description')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="설명" id="description" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.description" size="sm">
                  <option value="contains">contains</option>
                  <option value="2">contains any of</option>
                  <option value="3">doesn't contain</option>
                  <option value="4">starts with</option>
                  <option value="5">ends with</option>
                  <option value="6">none</option>
                  <option value="7">any</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormInput v-model="form.description" size="sm" />
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

  <CModal :visible="isModalOpen" @close="isModalOpen = false">
    <CModalHeader>
      <CModalTitle>검색양식 저장</CModalTitle>
    </CModalHeader>
    <CForm class="needs-validation" novalidate @submit.prevent="saveQuery">
      <CModalBody class="text-body">
        <CRow class="mb-3">
          <CFormLabel for="query-name" class="col-3 col-form-label required text-right">
            이름
          </CFormLabel>
          <CCol class="col-7">
            <CFormInput id="query-name" v-model="queryName" placeholder="검색양식 이름" required />
          </CCol>
        </CRow>
        <CRow class="mb-3" v-if="can(PERM.PROJECT_PUB_QUERY)">
          <CCol class="offset-3 col-7">
            <CFormCheck id="query-is-public" v-model="isPublic" label="공용 (프로젝트 내 공유)" />
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <v-btn type="submit" size="small" color="indigo" class="text-white">저장</v-btn>
        <v-btn color="light" size="small" @click="isModalOpen = false" flat>닫기</v-btn>
      </CModalFooter>
    </CForm>
  </CModal>
</template>
