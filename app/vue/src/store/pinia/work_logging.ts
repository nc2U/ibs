import { defineStore } from 'pinia'
import api from '@/api'
import { computed, ref } from 'vue'
import { errorHandle } from '@/utils/helper.ts'
import type { ActLogEntryFilter, IssueLogEntry } from '@/store/types/work_logging.ts'

export const useLogging = defineStore('logging', () => {
  // activity-log states & getters
  const activityLogList = ref<any[]>([])
  const groupedActivities = computed(() => {
    return activityLogList.value.reduce((result, currentValue) => {
      ;(result[currentValue['act_date']] = result[currentValue['act_date']] || []).push(
        currentValue,
      )
      return result
    }, {})
  })

  const fetchActivityLogList = async (payload: ActLogEntryFilter) => {
    let url = `/act-entry/?1=1`
    if (payload.project) url += `&project__slug=${payload.project}`
    else if (payload.project__search) url += `&project__search=${payload.project__search}`
    if (payload.from_act_date) url += `&from_act_date=${payload.from_act_date}`
    if (payload.to_act_date) url += `&to_act_date=${payload.to_act_date}`
    if (payload.user) url += `&user=${payload.user}`
    if (!!payload.sort?.length) url += `&sort=${payload.sort.join(',')}`
    if (!!payload.limit) url += `&limit=${payload.limit}`

    return await api
      .get(url)
      .then(res => (activityLogList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  // activity-log states & getters
  const issueLogList = ref<IssueLogEntry[]>([])

  const fetchIssueLogList = async (payload: { issue?: number; user?: number }) => {
    let url = `/log-entry/?1=1`
    if (payload.issue) url += `&issue=${payload.issue}`
    if (payload.user) url += `&user=${payload.user}`
    return await api
      .get(url)
      .then(res => (issueLogList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  return {
    activityLogList,
    groupedActivities,
    fetchActivityLogList,

    issueLogList,
    fetchIssueLogList,
  }
})
