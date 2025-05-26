<script lang="ts" setup>
import { ref, reactive, type PropType, onBeforeMount, watch } from 'vue'
import type { IssueProject, ProjectFilter } from '@/store/types/work_project.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/index.vue'
import IProjectSelect from '@/views/_Work/components/IProjectSelect.vue'

const props = defineProps({
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
})

const emit = defineEmits(['filter-submit'])

const viewMode = ref<'board' | 'list'>('board')
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
      { value: 'parent', label: '상위 프로젝트', disabled: true },
      { value: 'is_public', label: '공개여부' },
      { value: 'created', label: '등록일자', disabled: true },
    ],
  },
  {
    label: '문자열 검색',
    options: [
      { value: 'name', label: '이름' },
      { value: 'description', label: '설명' },
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
  project: '',
  is_public: '1',

  name: '',
  description: '',
})

const filterSubmit = () => {
  const filterData = {} as ProjectFilter

  if (cond.value.status === 'is') filterData.status = form.value.status
  else if (cond.value.status === 'exclude') filterData.status__exclude = form.value.status

  if (searchCond.value.includes('project'))
    if (cond.value.project === 'is') filterData.project = form.value.project
    else if (cond.value.project === 'exclude') filterData.project__exclude = form.value.project

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
    form.value.project = props.allProjects[0]?.slug
  }
})
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
                  <option value="is">is</option>
                  <option value="exclude">is not</option>
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
                  <option value="is">is</option>
                  <option value="exclude">is not</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <IProjectSelect v-model="form.project" :all-projects="allProjects" size="sm" />
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
                <CFormSelect size="sm">
                  <option v-for="proj in allProjects" :key="proj.pk" value="1">사용중</option>
                </CFormSelect>
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
              value="board"
              inline
              type="radio"
            />
            <CFormCheck
              v-model="viewMode"
              label="목록"
              name="viewMode"
              value="list"
              inline
              type="radio"
              disabled
            />
          </CCol>
        </CRow>
      </slot>
    </CCollapse>
  </CRow>

  <CRow class="my-3">
    <CCol>
      <slot name="footer">
        <v-icon icon="mdi-check-bold" size="sm" color="success" class="mr-1" />
        <router-link to="" class="mr-3" @click="filterSubmit">검색</router-link>
        <v-icon icon="mdi-replay" size="sm" color="success" class="mr-1" />
        <router-link to="" class="mr-3" @click="resetFilter">초기화</router-link>
        <!--        <router-link to=""> Save 검색양식</router-link>-->
      </slot>
    </CCol>
  </CRow>
</template>
