import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper.ts'

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

  const fetchCalendarEvents = async (projectSlug?: string, start?: string, end?: string) => {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (projectSlug) params.append('project', projectSlug)
      if (start) params.append('start', start)
      if (end) params.append('end', end)

      const url = `/work-calendar/?${params.toString()}`
      const res = await api.get(url)
      events.value = res.data
    } catch (err: any) {
      errorHandle(err.response.data)
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
