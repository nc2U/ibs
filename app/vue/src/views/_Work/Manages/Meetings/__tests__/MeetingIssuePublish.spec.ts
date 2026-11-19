import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'
import MeetingDetail from '@/views/_Work/Manages/Meetings/components/MeetingDetail.vue'
import { useAccount } from '@/store/pinia/account'
import { useIssue } from '@/store/pinia/work_issue'
import { useMeeting } from '@/store/pinia/work_meeting'
import { usePermission } from '@/store/pinia/work_permission'
import { useWork } from '@/store/pinia/work_project'
import type { User } from '@/store/types/accounts'
import type { CodeValue, Issue, IssueStatus } from '@/store/types/work_issue'
import type { IssueProject, SimpleVersion } from '@/store/types/work_project'
import type { Meeting } from '@/store/types/work_meeting'

vi.mock('@/utils/notification', () => ({
  markNotificationReadByTarget: vi.fn(),
}))

const vuetify = createVuetify()

const makeRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/work/project/:projId/meeting/:meetingId',
        name: '(회의) - 보기',
        component: { template: '<div />' },
      },
      {
        path: '/work/project/:projId/meeting/:meetingId/update',
        name: '(회의) - 수정',
        component: { template: '<div />' },
      },
      {
        path: '/work/project/:projId/meeting',
        name: '(회의)',
        component: { template: '<div />' },
      },
      {
        path: '/work/meeting',
        name: '회의',
        component: { template: '<div />' },
      },
      {
        path: '/work/project/:projId/issue/:issueId',
        name: '(업무) - 보기',
        component: { template: '<div />' },
      },
    ],
  })

const makeSimpleVersion = (
  pk: number,
  name: string,
  projName: string,
  isDefault = false,
): SimpleVersion => ({
  pk,
  name,
  status: '1',
  status_desc: '진행',
  sharing: '0',
  sharing_desc: '공유 없음',
  is_default: isDefault,
  effective_date: null,
  description: '',
  proj_name: projName,
})

const makeProject = (
  pk: number,
  slug: string,
  name: string,
  versions: SimpleVersion[] = [],
): IssueProject =>
  ({
    pk,
    company: 1,
    project: null,
    type: '2',
    name,
    slug,
    description: '',
    is_public: true,
    parent: null,
    parent_name: null,
    allowed_roles: [],
    status: '1',
    status_display: '사용중',
    chat_channel_enabled: true,
    slack_notifications_enabled: false,
    sub_projects: [],
    depth: 0,
    module: {
      project: pk,
      meeting: true,
      issue: true,
      news: true,
      document: true,
      forum: true,
      calendar: true,
    },
    my_perms: ['issue.read', 'issue.create', 'meeting.read'],
    all_members: [],
    visible: true,
    parent_visible: false,
    homepage: null,
    is_inherit_members: false,
    default_version: null,
    trackers: [{ pk: 1, name: '업무', description: '일반 업무' }],
    ancestors: [],
    members: [],
    versions,
    categories: [],
    forums: [],
  }) as IssueProject

const defaultStatusList: IssueStatus[] = [
  { pk: 1, name: '신규', description: '', closed: false, order: 1 },
]

const defaultPriorityList: CodeValue[] = [
  { pk: 2, name: '보통', active: true, default: true, order: 2 },
]

const commonStubs = {
  MdEditor: {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<textarea class="md-editor-stub" :value="modelValue" />',
  },
  DatePicker: {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<input class="date-picker-stub" :value="modelValue" />',
  },
  Multiselect: {
    props: ['modelValue', 'options'],
    emits: ['update:modelValue'],
    template: '<div class="multiselect-stub" />',
  },
  WatcherAdd: {
    template: '<div class="watcher-add-stub" />',
  },
  FormInIssueVersion: {
    template: '<div />',
  },
  FormInIssueCategory: {
    template: '<div />',
  },
  FileDisplay: {
    template: '<div />',
  },
}

describe('IssueForm & MeetingDetail follow-up issue creation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('binds form.project to currentProject.slug even when route.params.projId differs', async () => {
    const router = makeRouter()
    await router.push('/work/project/redmine/meeting/71')
    await router.isReady()

    const pinia = createTestingPinia({ createSpy: vi.fn, stubActions: true })
    const projB = makeProject(2, 'proj-b', '프로젝트 B', [
      makeSimpleVersion(101, 'v1.0', '프로젝트 B', true),
    ])

    const wrapper = mount(IssueForm, {
      props: {
        currentProject: projB,
        myProjects: [
          { value: 1, pk: 1, slug: 'redmine', label: 'Redmine' },
          { value: 2, pk: 2, slug: 'proj-b', label: '프로젝트 B' },
        ],
        statusList: defaultStatusList,
        priorityList: defaultPriorityList,
      },
      global: {
        plugins: [pinia, vuetify, CoreuiVue, router],
        stubs: commonStubs,
      },
    })

    await flushPromises()

    await wrapper.find('#tracker').setValue('1')
    await wrapper.find('#subject').setValue('후속 조치 테스트')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted('on-submit')
    expect(emitted).toBeTruthy()
    const payload = emitted![0][0] as Record<string, unknown>
    expect(payload.project).toBe('proj-b')
    expect(payload.fixed_version).toBe(101)
  })

  it('does not leak unrelated versions from workStore.versionList when currentProject has no versions', async () => {
    const router = makeRouter()
    await router.push('/work/project/proj-empty/meeting/10')
    await router.isReady()

    const pinia = createTestingPinia({ createSpy: vi.fn, stubActions: true })
    const workStore = useWork(pinia)
    workStore.versionList = [
      {
        pk: 999,
        project: {
          pk: 5,
          type: '2',
          name: '타 프로젝트',
          slug: 'other-proj',
          visible: true,
          status: '1',
        },
        name: '타 프로젝트 기본 단계',
        status: '1',
        status_desc: '진행',
        sharing: '0',
        sharing_desc: '공유 없음',
        effective_date: null,
        description: '',
        is_default: true,
        closed_num: 0,
        open_num: 0,
        total_num: 0,
        done_ratio: 0,
      },
    ]

    const projEmpty = makeProject(3, 'proj-empty', '빈 프로젝트', [])

    const wrapper = mount(IssueForm, {
      props: {
        currentProject: projEmpty,
        myProjects: [{ value: 3, pk: 3, slug: 'proj-empty', label: '빈 프로젝트' }],
        statusList: defaultStatusList,
        priorityList: defaultPriorityList,
      },
      global: {
        plugins: [pinia, vuetify, CoreuiVue, router],
        stubs: commonStubs,
      },
    })

    await flushPromises()

    const versionOptions = wrapper
      .findAll('#fixed_version option')
      .map(o => o.element.getAttribute('value'))
    expect(versionOptions).toEqual([''])

    await wrapper.find('#tracker').setValue('1')
    await wrapper.find('#subject').setValue('단계 없는 업무')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const payload = wrapper.emitted('on-submit')![0][0] as Record<string, unknown>
    expect(payload.fixed_version).toBeNull()
  })

  it('clears stale fixed_version when currentProject resolves to another project after mount', async () => {
    const router = makeRouter()
    await router.push('/work/project/redmine/meeting/71')
    await router.isReady()

    const pinia = createTestingPinia({ createSpy: vi.fn, stubActions: true })
    const projA = makeProject(1, 'redmine', 'Redmine', [
      makeSimpleVersion(10, 'R-v1', 'Redmine', true),
    ])
    const projB = makeProject(2, 'proj-b', '프로젝트 B', [])

    const wrapper = mount(IssueForm, {
      props: {
        currentProject: projA,
        myProjects: [
          { value: 1, pk: 1, slug: 'redmine', label: 'Redmine' },
          { value: 2, pk: 2, slug: 'proj-b', label: '프로젝트 B' },
        ],
        statusList: defaultStatusList,
        priorityList: defaultPriorityList,
      },
      global: {
        plugins: [pinia, vuetify, CoreuiVue, router],
        stubs: commonStubs,
      },
    })

    await flushPromises()
    await wrapper.setProps({ currentProject: projB })
    await flushPromises()

    await wrapper.find('#tracker').setValue('1')
    await wrapper.find('#subject').setValue('전환된 프로젝트 업무')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const payload = wrapper.emitted('on-submit')![0][0] as Record<string, unknown>
    expect(payload.project).toBe('proj-b')
    expect(payload.fixed_version).toBeNull()
  })

  it('canonicalizes route projId and submits meeting actual project from MeetingDetail + 업무 발행', async () => {
    const router = makeRouter()
    await router.push('/work/project/redmine/meeting/71')
    await router.isReady()

    const pinia = createTestingPinia({ createSpy: vi.fn, stubActions: true })
    const accountStore = useAccount(pinia)
    const workStore = useWork(pinia)
    const meetingStore = useMeeting(pinia)
    const issueStore = useIssue(pinia)
    const permStore = usePermission(pinia)

    accountStore.userInfo = {
      pk: 1,
      username: 'tester',
      is_superuser: true,
      work_manager: true,
    } as unknown as User
    vi.mocked(permStore.can).mockReturnValue(true)

    const projB = makeProject(2, 'proj-b', '프로젝트 B', [
      makeSimpleVersion(101, 'v1.0', '프로젝트 B', true),
    ])
    workStore.currentProject = makeProject(1, 'redmine', 'Redmine', [
      makeSimpleVersion(10, 'R-v1', 'Redmine', true),
    ])
    workStore.myProjects = [projB]

    issueStore.statusList = defaultStatusList
    issueStore.priorityList = defaultPriorityList
    issueStore.trackerList = [
      {
        pk: 1,
        name: '업무',
        description: '일반 업무',
        is_in_roadmap: true,
        default_status: 1,
        projects: [],
        order: 1,
      },
    ]

    const meetingObj: Meeting = {
      pk: 71,
      project: 2,
      project_desc: {
        pk: 2,
        type: '2',
        name: '프로젝트 B',
        slug: 'proj-b',
        visible: true,
        status: '1',
      },
      title: '주간 회의',
      category: null,
      category_desc: null,
      status: '1',
      status_display: '준비',
      is_confirmed: false,
      agenda: '',
      content: '',
      decisions: '',
      action_items: '- [ ] 첫 번째 후속 조치\n- [ ] 두 번째 후속 조치',
      meeting_date: '2026-11-19T10:00:00+09:00',
      location: '회의실',
      attendees: [1],
      attendees_desc: [{ pk: 1, username: 'tester' }],
      attendees_count: 1,
      other_attendees: '',
      other_attendees_list: [],
      other_attendees_count: 0,
      total_attendees_count: 1,
      files: [],
      links: [],
      issues: [],
      created: '2026-11-19T09:00:00+09:00',
      updated: '2026-11-19T09:00:00+09:00',
      creator: { pk: 1, username: 'tester' },
      updater: null,
    }

    vi.mocked(meetingStore.fetchMeeting).mockImplementation(async () => {
      meetingStore.meeting = meetingObj
    })
    vi.mocked(workStore.fetchIssueProject).mockImplementation(async (slug: string) => {
      if (slug === 'proj-b') {
        workStore.currentProject = projB
      }
    })

    const callModalSpy = vi.fn()
    const closeModalSpy = vi.fn()

    const wrapper = mount(MeetingDetail, {
      global: {
        plugins: [pinia, vuetify, CoreuiVue, router],
        stubs: {
          ...commonStubs,
          FormModal: {
            template: '<div class="form-modal-stub"><slot /></div>',
            methods: {
              callModal: callModalSpy,
              close: closeModalSpy,
            },
          },
          ConfirmModal: {
            template: '<div />',
          },
          AlertModal: {
            template: '<div />',
          },
        },
      },
    })

    await flushPromises()

    expect(router.currentRoute.value.params.projId).toBe('proj-b')

    const issueButtons = wrapper.findAll('button').filter(btn => btn.text().includes('업무 발행'))
    expect(issueButtons.length).toBe(2)

    await issueButtons[0].trigger('click')
    await flushPromises()
    expect(callModalSpy).toHaveBeenCalledTimes(1)

    const issueForm = wrapper.findComponent(IssueForm)
    expect(issueForm.exists()).toBe(true)

    // First submit fails (createIssue returns undefined) -> modal should not close
    vi.mocked(issueStore.createIssue).mockResolvedValueOnce(undefined)
    await issueForm.find('#tracker').setValue('1')
    await issueForm.find('form').trigger('submit')
    await flushPromises()

    expect(issueStore.createIssue).toHaveBeenCalledTimes(1)
    expect(closeModalSpy).not.toHaveBeenCalled()
    const firstFormData = vi.mocked(issueStore.createIssue).mock.calls[0][0] as FormData
    expect(firstFormData.get('project')).toBe('proj-b')
    expect(firstFormData.get('fixed_version')).toBe('101')
    expect(firstFormData.get('meeting')).toBe('71')
    expect(firstFormData.get('subject')).toBe('첫 번째 후속 조치')

    // Click second action item button -> IssueForm remounts with second item's subject
    await issueButtons[1].trigger('click')
    await flushPromises()
    expect(callModalSpy).toHaveBeenCalledTimes(2)

    const issueFormSecond = wrapper.findComponent(IssueForm)
    vi.mocked(issueStore.createIssue).mockResolvedValueOnce({ pk: 501 } as unknown as Issue)
    await issueFormSecond.find('#tracker').setValue('1')
    await issueFormSecond.find('form').trigger('submit')
    await flushPromises()

    expect(issueStore.createIssue).toHaveBeenCalledTimes(2)
    expect(closeModalSpy).toHaveBeenCalledTimes(1)
    const secondFormData = vi.mocked(issueStore.createIssue).mock.calls[1][0] as FormData
    expect(secondFormData.get('project')).toBe('proj-b')
    expect(secondFormData.get('subject')).toBe('두 번째 후속 조치')
  })
})
