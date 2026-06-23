import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import type { Meeting, MeetingCategory, MeetingFilter } from '@/store/types/work_meeting.ts'

export const useMeeting = defineStore('meeting', () => {
  // states
  const meeting = ref<Meeting | null>(null)
  const meetingList = ref<Meeting[]>([])
  const meetingCount = ref(0)
  const categoryList = ref<MeetingCategory[]>([])

  // actions
  const fetchMeetingList = async (payload: MeetingFilter) => {
    let url = `/meeting/?page=${payload.page ?? 1}`
    if (payload.project) url += `&project__slug=${payload.project}`
    if (payload.category) url += `&category=${payload.category}`
    if (payload.status) url += `&status=${payload.status}`
    if (payload.meeting_date) url += `&meeting_date=${payload.meeting_date}`
    if (payload.meeting_date__range) url += `&meeting_date__range=${payload.meeting_date__range}`
    if (payload.search) url += `&search=${payload.search}`

    return await api
      .get(url)
      .then(res => {
        meetingList.value = res.data.results
        meetingCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const meetingPages = (limit: number) => Math.ceil(meetingCount.value / limit)

  const fetchMeeting = async (pk: number) =>
    await api
      .get(`/meeting/${pk}/`)
      .then(res => (meeting.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const config_headers = { headers: { 'Content-Type': 'multipart/form-data' } }

  const createMeeting = async (payload: Meeting) =>
    await api
      .post(`/meeting/`, payload, config_headers)
      .then(res => {
        fetchMeetingList({ page: 1 })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateMeeting = async (pk: number, payload: FormData) =>
    await api
      .put(`/meeting/${pk}/`, payload, config_headers)
      .then(async res => {
        await fetchMeeting(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchMeeting = async (pk: number, payload: FormData) =>
    await api
      .patch(`/meeting/${pk}/`, payload, config_headers)
      .then(async res => {
        await fetchMeeting(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteMeeting = async (pk: number, project?: string) =>
    await api
      .delete(`/meeting/${pk}/`)
      .then(() => {
        fetchMeetingList({ page: 1, project })
        message('warning', '알림!', '해당 회의록이 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  const fetchCategoryList = async (project?: string) => {
    let url = `/meeting-category/`
    if (project) url += `?project__slug=${project}`
    return await api
      .get(url)
      .then(res => (categoryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createCategory = async (payload: MeetingCategory) =>
    await api
      .post(`/meeting-category/`, payload)
      .then(res => {
        fetchCategoryList(res.data.project_slug)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const generatePdf = (pk: number) => {
    const url = `/pdf/work/meeting/${pk}/`
    window.open(url, '_blank')
  }

  return {
    meeting,
    meetingList,
    meetingCount,
    categoryList,
    fetchMeetingList,
    meetingPages,
    fetchMeeting,
    createMeeting,
    updateMeeting,
    patchMeeting,
    deleteMeeting,
    fetchCategoryList,
    createCategory,
    generatePdf,
  }
})
