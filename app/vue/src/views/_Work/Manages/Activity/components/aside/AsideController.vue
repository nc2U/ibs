<script lang="ts" setup>
import { computed, onBeforeMount, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'
import { dateFormat } from '@/utils/baseMixins'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { User } from '@/store/types/accounts.ts'
import type { ActLogEntryFilter } from '@/store/types/work_logging.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({
  toDate: { type: Date, required: true },
  fromDate: { type: Date, required: true },
  hasSubs: { type: Boolean, default: false },
})

watch(
  () => props.toDate,
  nVal => {
    if (nVal) actFilter.to_act_date = dateFormat(nVal)
  },
)

watch(
  () => props.fromDate,
  nVal => {
    if (nVal) {
      actFilter.from_act_date = dateFormat(nVal)
      filterActivity()
    }
  },
)

const actFilter = reactive<ActLogEntryFilter & { subProjects: boolean }>({
  project: '',
  project__search: '',
  to_act_date: '',
  from_act_date: '',
  creator: '',
  sort: ['1', '2', '3', '4', '5', '6'],
  subProjects: true,
})

watch(
  () => actFilter.sort,
  nVal => {
    if (nVal && actFilter.sort) {
      const currentSort = [...nVal]
      const hasIssue = currentSort.includes('1')
      const hasComment = currentSort.includes('2')

      if (hasIssue && !hasComment) {
        actFilter.sort.push('2')
        return
      } else if (!hasIssue && hasComment) {
        const filtered = actFilter.sort.filter(s => s !== '2')
        actFilter.sort.splice(0, actFilter.sort.length, ...filtered)
        return
      }

      if (nVal.length === 0) {
        const defaults: Array<'1' | '2' | '3' | '4' | '5' | '6'> = ['1', '2', '3', '4', '5', '6']
        actFilter.sort.splice(0, actFilter.sort.length, ...defaults)
        localStorage.removeItem('activity-log-enabled-modules')
      } else {
        localStorage.setItem('activity-log-enabled-modules', [...nVal].sort().join('-'))
        filterActivity()
      }
    }
  },
  { deep: true },
)

const pickSort = (sort: '1' | '2' | '3' | '4' | '5' | '6') => {
  if (actFilter.sort) {
    const nextSort: Array<'1' | '2' | '3' | '4' | '5' | '6'> = sort === '1' ? ['1', '2'] : [sort]
    actFilter.sort.splice(0, actFilter.sort.length, ...nextSort)
  }
}

const emit = defineEmits(['loading-start', 'loading-end'])

const route = useRoute()
const logStore = useLogging()
const filterActivity = async () => {
  emit('loading-start')
  if (route.params.projId) {
    if (actFilter.subProjects) {
      actFilter.project = route.params.projId as string
      actFilter.project__search = ''
    } else {
      actFilter.project = ''
      actFilter.project__search = route.params.projId as string
    }
  } else {
    actFilter.project = ''
    actFilter.project__search = ''
  }

  try {
    await logStore.fetchActivityLogList({ ...actFilter })
  } finally {
    emit('loading-end')
  }
}

defineExpose({ filterActivity })

watch(
  () => route.params.projId,
  () => filterActivity(),
)

const workStore = useWork()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const getUsers = computed(() =>
  workStore.currentProject
    ? workStore.currentProject?.all_members?.map(m => ({
        value: m.user.pk,
        label: m.user.username,
      }))
    : accStore.getUsers,
)

onBeforeMount(async () => {
  await accStore.fetchUsersList()

  const enabledModules = (localStorage.getItem('activity-log-enabled-modules') as string)?.split(
    '-',
  ) as any[]
  if (enabledModules?.length) actFilter.sort = enabledModules

  if (props.toDate) actFilter.to_act_date = dateFormat(props.toDate)
  if (props.fromDate) actFilter.from_act_date = dateFormat(props.fromDate)

  if (route.query.user) actFilter.creator = route.query.user as string

  await filterActivity()
})
</script>

<template>
  <CRow class="mb-3">
    <CCol><h6 class="text-subtitle-1 mb-2">업무실행내역</h6></CCol>
  </CRow>
  <CRow class="mb-2">
    <CFormLabel for="log-date" class="col-sm-4 col-form-label">10일 기록</CFormLabel>
    <CCol class="col-xxl-6">
      <DatePicker v-model="actFilter.to_act_date" id="log-date" />
    </CCol>
  </CRow>

  <CRow class="mb-3">
    <CFormLabel for="log-user" class="col-sm-4 col-form-label">사용자</CFormLabel>
    <CCol class="col-xxl-6">
      <CFormSelect v-model="actFilter.creator" id="log-user" size="sm">
        <option value="">---------</option>
        <option :value="(userInfo as User)?.pk">&lt;&lt; 나 &gt;&gt;</option>
        <option v-for="user in getUsers" :value="user.value" :key="user.value">
          {{ user.label }}
        </option>
      </CFormSelect>
    </CCol>
  </CRow>
  <CRow class="mb-3">
    <CCol>
      <CFormCheck v-model="actFilter.sort" value="1" id="issue-filter" />
      <a href="javascript:void(0)" @click="pickSort('1')" class="ml-2">업무</a> <br />
      <CFormCheck v-model="actFilter.sort" value="3" id="meeting-filter" />
      <a href="javascript:void(0)" @click="pickSort('3')" class="ml-2">회의</a> <br />
      <CFormCheck v-model="actFilter.sort" value="4" id="news-filter" />
      <a href="javascript:void(0)" @click="pickSort('4')" class="ml-2">공지</a> <br />
      <CFormCheck v-model="actFilter.sort" value="5" id="docs-filter" />
      <a href="javascript:void(0)" @click="pickSort('5')" class="ml-2">문서</a> <br />
      <CFormCheck v-model="actFilter.sort" value="6" id="message-filter" />
      <a href="javascript:void(0)" @click="pickSort('6')" class="ml-2">글</a>
    </CCol>
  </CRow>

  <CRow v-if="hasSubs" class="mb-3">
    <CCol>
      <CFormCheck v-model="actFilter.subProjects" label="하위 프로젝트" id="sub-project-filter" />
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <v-btn color="blue-grey-darken-1" size="small" @click="filterActivity">적용</v-btn>
    </CCol>
  </CRow>
</template>
