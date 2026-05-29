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

  const createMeeting = async (payload: Meeting) =>
    await api
      .post(`/meeting/`, payload)
      .then(res => {
        fetchMeetingList({ page: 1 })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateMeeting = async (payload: Meeting) =>
    await api
      .put(`/meeting/${payload.pk}/`, payload)
      .then(res => {
        fetchMeeting(res.data.pk)
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
    deleteMeeting,
    fetchCategoryList,
  }
})
