import { defineStore } from 'pinia'
import api from '@/api'
import { computed, ref } from 'vue'
import { errorHandle } from '@/utils/helper.ts'
import type { ActLogEntry, ActLogEntryFilter, IssueLogEntry } from '@/store/types/work_logging.ts'

export const useLogging = defineStore('logging', () => {
  // activity-log states & getters
  const activityLogList = ref<ActLogEntry[]>([])
  const groupedActivities = computed<Record<string, ActLogEntry[]>>(() => {
    return activityLogList.value.reduce<Record<string, ActLogEntry[]>>((result, currentValue) => {
      const key = currentValue.act_date
      ;(result[key] = result[key] || []).push(currentValue)
      return result
    }, {})
  })

  const fetchActivityLogList = async (payload: ActLogEntryFilter) => {
    const { project, project__search, from_act_date, to_act_date, sort, creator, limit } = payload
    const params: Record<string, string | number> = {}
    if (project) params.project__slug = project
    else if (project__search) params.project__search = project__search
    if (from_act_date) params.from_act_date = from_act_date
    if (to_act_date) params.to_act_date = to_act_date
    if (creator) params.creator = creator
    if (sort?.length) params.sort = sort.join(',')
    if (limit) params.limit = limit

    return await api
      .get('/act-entry/', { params })
      .then(res => (activityLogList.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  // issue-log states & getters
  const issueLogList = ref<IssueLogEntry[]>([])

  const fetchIssueLogList = async (payload: {
    issue?: number
    user?: number
    creator?: number
    limit?: number
  }) => {
    const params: Record<string, number> = {
      limit: payload.limit ?? 500,
    }
    if (payload.issue) params.issue = payload.issue
    const creatorId = payload.creator ?? payload.user
    if (creatorId) params.creator = creatorId
    return await api
      .get('/log-entry/', { params })
      .then(res => (issueLogList.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  const reset = () => {
    activityLogList.value = []
    issueLogList.value = []
  }

  return {
    activityLogList,
    groupedActivities,
    fetchActivityLogList,

    issueLogList,
    fetchIssueLogList,
    reset,
  }
})
