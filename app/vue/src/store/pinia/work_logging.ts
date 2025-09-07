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
    const { project, project__search, from_act_date, to_act_date, sort, creator, limit } = payload
    let url = `/act-entry/?1=1`
    if (project) url += `&project__slug=${project}`
    else if (project__search) url += `&project__search=${project__search}`
    if (from_act_date) url += `&from_act_date=${from_act_date}`
    if (to_act_date) url += `&to_act_date=${to_act_date}`
    if (creator) url += `&creator=${creator}`
    if (!!sort?.length) url += `&sort=${sort?.join(',')}`
    if (!!limit) url += `&limit=${limit}`

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
