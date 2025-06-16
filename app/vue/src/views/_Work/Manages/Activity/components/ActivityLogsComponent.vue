<script lang="ts" setup>
import Cookies from 'js-cookie'
import { computed, onBeforeMount, type PropType, watch } from 'vue'
import { useRoute } from 'vue-router'
import { dateFormat } from '@/utils/baseMixins'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import NoData from '@/views/_Work/components/NoData.vue'
import ActivityLogs from '@/views/_Work/Manages/Activity/components/ActivityLogs.vue'

const props = defineProps({
  toDate: { type: Date as PropType<Date>, required: true },
  activityFilter: { type: Object as PropType<any>, default: () => null },
})

const emit = defineEmits(['to-back', 'to-next'])

const cookieSort = computed(() => Cookies.get('cookieSort')?.split('-') as any)
const sort = computed(() =>
  cookieSort.value?.length ? cookieSort : ['1', '2', '4', '5', '6', '9'],
)

const logStore = useLogging()
const groupedActivities = computed<{ [key: string]: ActLogEntry[] }>(
  () => logStore.groupedActivities,
)

const fromDate = computed(
  () => new Date(new Date(props.toDate as Date).getTime() - 9 * 24 * 60 * 60 * 1000),
)

const toBack = () => {
  if (props.toDate)
    emit('to-back', new Date(new Date(props.toDate).setDate(new Date(props.toDate).getDate() - 10)))
}

const toNext = () => {
  if (props.toDate)
    emit('to-next', new Date(new Date(props.toDate).setDate(new Date(props.toDate).getDate() + 10)))
}

const route = useRoute()
const projId = computed(() => (route.params.projId as string) ?? '')

watch(
  () => route,
  nVal => {
    if (nVal.params.projId)
      logStore.fetchActivityLogList({
        project: nVal.params.projId,
        from_act_date: dateFormat(fromDate.value),
        to_act_date: dateFormat(props.toDate as Date),
        sort: sort.value,
        ...props.activityFilter,
      })
  },
  { deep: true },
)

const workStore = useWork()
onBeforeMount(async () => {
  if (route.params.projId) await workStore.fetchIssueProject(projId.value)
  await logStore.fetchActivityLogList({
    project: projId.value,
    from_act_date: dateFormat(fromDate.value),
    to_act_date: dateFormat(props.toDate as Date),
    sort: sort.value,
    ...props.activityFilter,
  })
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>작업내역</h5>
    </CCol>
  </CRow>

  <CRow class="fst-italic">
    <CCol> {{ dateFormat(fromDate, '/') }}부터 {{ dateFormat(toDate, '/') }}까지</CCol>
  </CRow>

  <NoData v-if="!Object.getOwnPropertyNames(groupedActivities).length" />

  <CRow v-else class="my-3">
    <CCol>
      <ActivityLogs :grouped-activities="groupedActivities" />
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <v-btn-group density="compact" role="group">
        <v-btn color="primary" variant="outlined" size="small" @click="toBack">« 뒤로</v-btn>
        <v-btn
          v-if="dateFormat(toDate) < dateFormat(new Date())"
          color="primary"
          variant="outlined"
          size="small"
          @click="toNext"
        >
          다음 »
        </v-btn>
      </v-btn-group>
    </CCol>
  </CRow>
</template>
