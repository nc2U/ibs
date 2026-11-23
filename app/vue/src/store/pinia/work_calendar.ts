import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper.ts'
import type { IssueFilter } from '@/store/types/work_issue.ts'

export interface CalendarEvent {
  id: string
  type: 'issue' | 'meeting'
  title: string
  start: string
  end?: string | null
  project: string
  status?: {
    pk: number
    closed: boolean
  }
  expected_duration?: string | null
}

export const useCalendar = defineStore('calendar', () => {
  const events = ref<CalendarEvent[]>([])
  const loading = ref<boolean>(false)

  const fetchCalendarEvents = async (
    projectOrFilters?: string | IssueFilter | Record<string, unknown>,
    start?: string,
    end?: string,
  ) => {
    const filterObj =
      projectOrFilters && typeof projectOrFilters === 'object'
        ? (projectOrFilters as Record<string, unknown>)
        : null
    if (filterObj?.event_type === 'none') {
      events.value = []
      return
    }
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (start) params.append('start', start)
      if (end) params.append('end', end)

      if (typeof projectOrFilters === 'string' && projectOrFilters) {
        params.append('project', projectOrFilters)
      } else if (filterObj) {
        Object.keys(filterObj).forEach(key => {
          const val = filterObj[key]
          if (val !== null && val !== undefined && val !== '') {
            params.append(key, String(val))
          }
        })
      }

      const url = `/work-calendar/?${params.toString()}`
      const res = await api.get(url)
      events.value = res.data
    } catch (err: unknown) {
      errorHandle(err)
    } finally {
      loading.value = false
    }
  }

  return {
    events,
    loading,
    fetchCalendarEvents,
  }
})
