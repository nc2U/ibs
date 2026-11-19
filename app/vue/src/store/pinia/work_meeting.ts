import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { downloadFile, errorHandle, message } from '@/utils/helper'
import type { Meeting, MeetingCategory, MeetingFilter } from '@/store/types/work_meeting.ts'

export const useMeeting = defineStore('meeting', () => {
  // states
  const meeting = ref<Meeting | null>(null)
  const meetingList = ref<Meeting[]>([])
  const meetingCount = ref(0)
  const categoryList = ref<MeetingCategory[]>([])

  // actions
  const fetchMeetingList = async (payload: MeetingFilter) => {
    const params = new URLSearchParams()
    params.append('page', String(payload.page ?? 1))
    const paramMap: Record<string, string> = {
      project: 'project__slug',
      project__exclude: 'project__exclude',
      project__my_project: 'project__my_project',
      project__bookmark: 'project__bookmark',
      project_status: 'project_status',
      project_status__exclude: 'project_status__exclude',
      status: 'status',
      status__exclude: 'status__exclude',
      is_confirmed: 'is_confirmed',
      category: 'category',
      category__exclude: 'category__exclude',
      creator: 'creator',
      creator__exclude: 'creator__exclude',
      attendees: 'attendees',
      attendees__exclude: 'attendees__exclude',
      meeting_date: 'meeting_date',
      meeting_date__range: 'meeting_date__range',
      meeting_date_after: 'meeting_date_after',
      meeting_date_before: 'meeting_date_before',
      created_after: 'created_after',
      created_before: 'created_before',
      search: 'search',
      title: 'title',
      title__exclude: 'title__exclude',
      agenda: 'agenda',
      agenda__exclude: 'agenda__exclude',
      content: 'content',
      content__exclude: 'content__exclude',
      decisions: 'decisions',
      decisions__exclude: 'decisions__exclude',
    }
    for (const [key, apiParam] of Object.entries(paramMap)) {
      const val = payload[key as keyof MeetingFilter]
      if (val !== undefined && val !== null && val !== '') {
        params.append(apiParam, String(val))
      }
    }

    return await api
      .get(`/meeting/?${params.toString()}`)
      .then(res => {
        meetingList.value = res.data.results
        meetingCount.value = res.data.count
      })
      .catch(err => errorHandle(err))
  }

  const meetingPages = (limit: number) => Math.ceil(meetingCount.value / limit)

  const fetchMeeting = async (pk: number) =>
    await api
      .get(`/meeting/${pk}/`)
      .then(res => {
        meeting.value = res.data
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const removeMeeting = () => {
    meeting.value = null
  }

  const config_headers = { headers: { 'Content-Type': 'multipart/form-data' } }

  const createMeeting = async (payload: FormData) =>
    await api
      .post(`/meeting/`, payload, config_headers)
      .then(async res => {
        await fetchMeetingList({ page: 1, project: res.data.project_desc?.slug })
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateMeeting = async (pk: number, payload: FormData) =>
    await api
      .put(`/meeting/${pk}/`, payload, config_headers)
      .then(async res => {
        await fetchMeeting(res.data.pk)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchMeeting = async (pk: number, payload: FormData) =>
    await api
      .patch(`/meeting/${pk}/`, payload, config_headers)
      .then(async res => {
        await fetchMeeting(res.data.pk)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteMeeting = async (pk: number, project?: string): Promise<boolean> =>
    await api
      .delete(`/meeting/${pk}/`)
      .then(async () => {
        meeting.value = null
        await fetchMeetingList({ page: 1, project })
        message('warning', '알림!', '해당 회의록이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const fetchCategoryList = async (project?: string) => {
    const params = new URLSearchParams()
    params.append('limit', '500')
    if (project) params.append('project__slug', project)
    return await api
      .get(`/meeting-category/?${params.toString()}`)
      .then(res => (categoryList.value = res.data.results ?? []))
      .catch(err => errorHandle(err))
  }

  const createCategory = async (payload: Partial<MeetingCategory> | Record<string, unknown>) =>
    await api
      .post(`/meeting-category/`, payload)
      .then(async res => {
        await fetchCategoryList(res.data.project_slug)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const generatePdf = (pk: number) => {
    const url = `/pdf/work/meeting/${pk}/`
    downloadFile(url)
  }

  const confirmMeeting = async (pk: number) =>
    await api
      .post(`/meeting/${pk}/confirm/`)
      .then(async res => {
        await fetchMeeting(pk)
        message(
          `${res.data.is_confirmed ? 'success' : 'warning'}`,
          '알림!',
          `회의가 ${res.data.is_confirmed ? '확정' : '확정 취소'}되었습니다.`,
        )
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const aiSummarizeMeeting = async (audioBlob: Blob, filename = 'recording.webm') => {
    const formData = new FormData()
    formData.append('audio', audioBlob, filename)
    return await api
      .post('/meeting/ai-summarize/', formData, config_headers)
      .then(res => res.data)
      .catch(err => {
        errorHandle(err)
        throw err
      })
  }

  return {
    meeting,
    meetingList,
    meetingCount,
    categoryList,
    fetchMeetingList,
    meetingPages,
    fetchMeeting,
    removeMeeting,
    createMeeting,
    updateMeeting,
    patchMeeting,
    deleteMeeting,
    confirmMeeting,
    fetchCategoryList,
    createCategory,
    generatePdf,
    aiSummarizeMeeting,
  }
})
