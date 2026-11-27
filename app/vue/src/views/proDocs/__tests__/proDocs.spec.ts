import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, reactive } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { useAccount } from '@/store/pinia/account'
import { useDocs } from '@/store/pinia/docs'
import { useProject } from '@/store/pinia/project'
import { useWork } from '@/store/pinia/work_project'
import { usePermission } from '@/store/pinia/work_permission'
import { PERM } from '@/store/constants/permissions'
import type { User } from '@/store/types/accounts'
import type { Project } from '@/store/types/project'
import type { IssueProject } from '@/store/types/work_project'
import type { Docs, SuitCase, TrashDocs } from '@/store/types/docs'
import ProDocsAuthGuard from '@/components/AuthGuard/ProDocsAuthGuard.vue'
import DocsDetail from '@/components/Documents/DocsDetail.vue'
import CaseDetail from '@/components/LawSuitCase/CaseDetail.vue'
import GeneralDocsIndex from '../GeneralDocs/Index.vue'
import LawsuitDocsIndex from '../LawsuitDocs/Index.vue'
import LawsuitCaseIndex from '../LawsuitCase/Index.vue'
import TrashCanIndex from '../TrashCan/Index.vue'
import TrashDocsList from '../TrashCan/components/TrashDocsList.vue'
import TrashDocsDetail from '../TrashCan/components/TrashDocsDetail.vue'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockRoute = reactive({
  name: '일반 문서 관리',
  fullPath: '/project-docs/general/docs',
  params: {} as Record<string, string>,
  query: {} as Record<string, string>,
})
const mockPush = vi.fn()
const mockReplace = vi.fn()
const mockGo = vi.fn()

vi.mock('vue-router', async importOriginal => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => mockRoute,
    useRouter: () => ({
      push: mockPush,
      replace: mockReplace,
      go: mockGo,
    }),
    onBeforeRouteUpdate: vi.fn(),
  }
})

const mockMessage = vi.fn()
const mockErrorHandle = vi.fn()

vi.mock('@/utils/helper', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/helper')>()
  return {
    ...actual,
    message: (...args: unknown[]) => mockMessage(...args),
    errorHandle: (...args: unknown[]) => mockErrorHandle(...args),
  }
})

const mockApi = api as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: {
    to: { type: [String, Object], required: false, default: '' },
  },
  template: '<a :data-to="JSON.stringify(to)"><slot /></a>',
})

const ContentHeaderStub = defineComponent({
  name: 'ContentHeader',
  props: ['pageTitle', 'navMenu', 'selector'],
  template: '<div class="content-header-stub" />',
})

const ContentBodyStub = defineComponent({
  name: 'ContentBody',
  template: '<div class="content-body-stub"><slot /></div>',
})

const makeVuetify = () => createVuetify({ components, directives })

const makeUser = (overrides: Partial<User> = {}): User => ({
  pk: 1,
  email: 'staff@example.com',
  username: 'staff',
  is_active: true,
  is_superuser: false,
  is_staff: true,
  work_manager: false,
  date_joined: '2026-01-01',
  profile: null,
  last_login: null,
  ...overrides,
})

const makeProject = (overrides: Partial<Project> = {}): Project => ({
  pk: 1,
  issue_project: 10,
  issue_project_slug: 'dev-proj-1',
  company: 1,
  name: '개발사업 1지구',
  order: 1,
  kind: '1',
  kind_desc: '공동주택',
  start_year: '2025',
  is_direct_manage: true,
  is_returned_area: false,
  is_unit_set: true,
  monthly_aggr_start_date: '2026-01-01',
  construction_start_date: '2026-01-01',
  construction_period_months: null,
  location: '',
  area_usage: '',
  build_size: '',
  num_unit: null,
  buy_land_extent: null,
  scheme_land_extent: null,
  donation_land_extent: null,
  on_floor_area: null,
  under_floor_area: null,
  total_floor_area: null,
  build_area: null,
  floor_area_ratio: null,
  build_to_land_ratio: null,
  num_legal_parking: null,
  num_planed_parking: null,
  ...overrides,
})

const makeIssueProject = (
  pk: number,
  slug: string,
  perms: string[],
  status: '1' | '2' | '9' = '1',
): IssueProject => ({
  pk,
  company: 1,
  name: `프로젝트-${pk}`,
  slug,
  type: '2',
  depth: 0,
  status,
  status_display:
    status === '2' ? '닫힘' : status === '9' ? '잠금보관(모든 접근이 차단됨)' : '사용중',
  description: '',
  parent: null,
  parent_name: null,
  parent_visible: true,
  allowed_roles: [],
  is_public: false,
  is_inherit_members: false,
  chat_channel_enabled: false,
  slack_notifications_enabled: false,
  sub_projects: [],
  all_members: [],
  homepage: null,
  trackers: [],
  ancestors: [],
  members: [],
  versions: [],
  categories: [],
  forums: [],
  module: {
    project: pk,
    meeting: true,
    issue: true,
    news: true,
    document: true,
    forum: true,
    calendar: true,
  },
  default_version: null,
  project: pk,
  my_perms: perms,
  created: '2026-01-01',
})

const makeDoc = (overrides: Partial<Docs> = {}): Docs => ({
  pk: 101,
  project: {
    pk: 10,
    type: '2',
    name: '개발사업 1지구',
    slug: 'dev-proj-1',
    visible: true,
    status: '1',
  },
  doc_type: 1,
  type_name: '일반문서',
  category: 5,
  cate_name: '일반',
  cate_color: '#0099ff',
  lawsuit: null,
  lawsuit_name: '',
  title: '테스트 문서',
  execution_date: '2026-11-28',
  description: '<p>내용</p>',
  hit: 3,
  scrape: 0,
  my_scrape: false,
  device: '',
  is_pinned: false,
  security_level: '3',
  security_level_desc: '3등급 프로젝트 공개',
  is_blind: false,
  links: [{ pk: 11, docs: 101, link: 'https://example.com', description: '', hit: 1 }],
  files: [{ pk: 21, file: '/media/test.pdf', file_name: 'test.pdf', hit: 2 }],
  creator: { pk: 1, username: 'staff' },
  created: '2026-11-28T00:00:00Z',
  prev_pk: null,
  next_pk: null,
  ...overrides,
})

const makeSuitCase = (overrides: Partial<SuitCase> = {}): SuitCase => ({
  pk: 301,
  issue_project: 10,
  proj_name: '개발사업 1지구',
  proj_sort: '2',
  sort: '1',
  sort_desc: '민사',
  level: '1',
  level_desc: '1심',
  related_case: null,
  related_case_name: '',
  court: '000210',
  court_desc: '서울중앙지방법원',
  other_agency: '',
  case_number: '2026가합1234',
  case_name: '분양대금 소송',
  __str__: '서울중앙지방법원 2026가합1234 분양대금 소송',
  plaintiff: '원고',
  plaintiff_attorney: '',
  plaintiff_case_price: 1000000,
  defendant: '피고',
  defendant_attorney: '',
  defendant_case_price: null,
  related_debtor: '',
  case_start_date: '2026-01-10',
  case_end_date: null,
  summary: '요약',
  creator: { pk: 99, username: 'other_author' },
  links: [],
  files: [],
  created: '2026-01-10T00:00:00Z',
  prev_pk: null,
  next_pk: null,
  ...overrides,
})

const defaultMountOptions = () => ({
  global: {
    plugins: [makeVuetify(), CoreuiVue],
    stubs: {
      RouterLink: RouterLinkStub,
      ContentHeader: ContentHeaderStub,
      ContentBody: ContentBodyStub,
      Loading: true,
    },
  },
})

describe('proDocs 정밀검사 검증 테스트', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockRoute.name = '일반 문서 관리'
    mockRoute.fullPath = '/project-docs/general/docs'
    mockRoute.params = {}
    mockRoute.query = {}
    mockApi.get.mockResolvedValue({ data: { results: [], count: 0 } })
    mockApi.post.mockResolvedValue({ data: { pk: 500, doc_type: 1, issue_project: 10 } })
    mockApi.put.mockResolvedValue({ data: { pk: 101, doc_type: 1, issue_project: 10 } })
    mockApi.patch.mockResolvedValue({ data: { pk: 101 } })
    mockApi.delete.mockResolvedValue({ status: 204, data: null })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('useDocs 스토어 동작', () => {
    it('hitDocs / hitLink / hitFile은 /hit/ 엔드포인트를 호출하고 현재 docs 카운트를 즉시 갱신한다', async () => {
      const store = useDocs()
      store.setDocs(makeDoc())
      mockApi.post
        .mockResolvedValueOnce({ data: { hit: 4 } })
        .mockResolvedValueOnce({ data: { hit: 9 } })
        .mockResolvedValueOnce({ data: { hit: 7 } })

      await store.hitDocs(101)
      await store.hitLink(11)
      await store.hitFile(21)

      expect(mockApi.post).toHaveBeenNthCalledWith(1, '/docs/101/hit/')
      expect(mockApi.post).toHaveBeenNthCalledWith(2, '/link/11/hit/')
      expect(mockApi.post).toHaveBeenNthCalledWith(3, '/file/21/hit/')
      expect(store.docs?.hit).toBe(4)
      expect(store.docs?.links?.[0]?.hit).toBe(9)
      expect(store.docs?.files?.[0]?.hit).toBe(7)
    })

    it('deleteSuitCase와 createDocs는 마지막 조회 필터(is_real_dev, project, category)를 보존하여 재조회한다', async () => {
      const store = useDocs()
      await store.fetchSuitCaseList({
        company: 1,
        project: 5,
        is_real_dev: 'true',
        court: '000210',
      })
      await store.fetchAllSuitCaseList({ company: 1, project: 5, is_real_dev: 'true' })
      mockApi.get.mockClear()

      const deleted = await store.deleteSuitCase(301)
      expect(deleted).toBe(true)
      expect(mockApi.get).toHaveBeenCalledWith(
        '/all-suitcase/?company=1&issue_project__project=5&is_real_dev=true',
      )
      expect(mockApi.get).toHaveBeenCalledWith(
        '/suitcase/?company=1&issue_project__project=5&is_real_dev=true&court=000210&limit=10&page=1',
      )

      await store.fetchDocsList({
        project: 5,
        is_real_dev: 'true',
        doc_type: 1,
        category: 9,
        ordering: '-created',
      })
      mockApi.get.mockClear()
      mockApi.post.mockResolvedValueOnce({ data: { pk: 202, doc_type: 1, issue_project: 10 } })
      await store.createDocs({ form: new FormData(), isProject: true })
      expect(mockApi.get).toHaveBeenCalledWith(
        '/docs/?limit=10&page=1&issue_project__project=5&is_real_dev=true&doc_type=1&category=9&ordering=-created',
      )
    })

    it('restoreDocs와 deleteTrashDocs는 성공/실패 boolean을 반환한다', async () => {
      const store = useDocs()
      expect(await store.restoreDocs(11, 2)).toBe(true)
      mockApi.patch.mockRejectedValueOnce(new Error('403'))
      expect(await store.restoreDocs(11, 2)).toBe(false)

      expect(await store.deleteTrashDocs(11, 2)).toBe(true)
      mockApi.delete.mockRejectedValueOnce(new Error('403'))
      expect(await store.deleteTrashDocs(11, 2)).toBe(false)
    })
  })

  describe('GeneralDocs & LawsuitDocs 폼 직렬화, 에러 처리, 권한/조회수', () => {
    it('GeneralDocs는 newLinks Link 객체 배열을 URL 문자열로 직렬화하며 undefined 필드를 전송하지 않는다', async () => {
      const acc = useAccount()
      acc.userInfo = makeUser()
      const proj = useProject()
      proj.project = makeProject()
      const perm = usePermission()
      perm.setProjectPermissions([PERM.DOCS_READ, PERM.DOCS_CREATE])

      const wrapper = mount(GeneralDocsIndex, defaultMountOptions())
      await flushPromises()

      const vm = wrapper.vm as unknown as {
        onSubmit: (payload: Record<string, unknown>) => Promise<void>
      }
      await vm.onSubmit({
        doc_type: 1,
        category: 5,
        lawsuit: null,
        title: '링크 첨부 테스트',
        execution_date: null,
        description: '<p>본문</p>',
        device: '',
        is_pinned: false,
        security_level: '3',
        is_blind: false,
        files: [],
        newFiles: [],
        cngFiles: [],
        links: [],
        newLinks: [{ docs: null, link: 'https://valid.example.com', description: '' }],
        extraUndefined: undefined,
      })

      expect(mockApi.post).toHaveBeenCalledTimes(1)
      const sentForm = mockApi.post.mock.calls[0][1] as FormData
      expect(sentForm.getAll('newLinks')).toEqual(['https://valid.example.com'])
      expect(sentForm.getAll('newLinks')).not.toContain('[object Object]')
      expect(sentForm.has('extraUndefined')).toBe(false)
      expect(mockReplace).toHaveBeenCalledWith({ name: '일반 문서 관리' })
    })

    it('createDocs 실패 시 router.replace를 호출하지 않아 작성 데이터를 유지한다', async () => {
      const acc = useAccount()
      acc.userInfo = makeUser()
      const proj = useProject()
      proj.project = makeProject()
      const perm = usePermission()
      perm.setProjectPermissions([PERM.DOCS_READ, PERM.DOCS_CREATE])

      const wrapper = mount(GeneralDocsIndex, defaultMountOptions())
      await flushPromises()
      mockApi.post.mockRejectedValueOnce(new Error('400 Bad Request'))

      const vm = wrapper.vm as unknown as {
        onSubmit: (payload: Record<string, unknown>) => Promise<void>
      }
      await vm.onSubmit({
        doc_type: 1,
        category: 5,
        lawsuit: null,
        title: '실패 테스트',
        execution_date: null,
        description: '',
        device: '',
        is_pinned: false,
        security_level: '3',
        is_blind: false,
        files: [],
        newFiles: [],
        cngFiles: [],
        links: [],
        newLinks: [],
      })

      expect(mockReplace).not.toHaveBeenCalled()
    })

    it('LawsuitDocs의 createLawSuit는 is_real_dev=true를 강제해 프로젝트 소송 목록 소실을 방지한다', async () => {
      mockRoute.name = '소송 문서 관리'
      const acc = useAccount()
      acc.userInfo = makeUser()
      const work = useWork()
      const ip = makeIssueProject(10, 'dev-proj-1', [PERM.DOCS_READ, PERM.DOCS_CREATE])
      work.myProjects = [ip]
      work.currentProject = ip
      const proj = useProject()
      proj.project = makeProject()
      const perm = usePermission()
      perm.setProjectPermissions([PERM.DOCS_READ, PERM.DOCS_CREATE])

      const wrapper = mount(LawsuitDocsIndex, defaultMountOptions())
      await flushPromises()
      mockApi.get.mockClear()
      mockApi.post.mockResolvedValueOnce({ data: makeSuitCase({ pk: 777 }) })

      const vm = wrapper.vm as unknown as {
        createLawSuit: (payload: SuitCase) => Promise<void>
      }
      await vm.createLawSuit(makeSuitCase({ pk: null, issue_project: null }))

      expect(mockApi.post).toHaveBeenCalledWith(
        '/suitcase/',
        expect.objectContaining({ issue_project: 10, is_real_dev: true }),
      )
      expect(mockApi.get).toHaveBeenCalledWith(
        '/all-suitcase/?issue_project__project=1&is_real_dev=true',
      )
    })

    it('docsHit/linkHit/fileHit는 PATCH 대신 POST .../hit/ 액션을 호출한다', async () => {
      const acc = useAccount()
      acc.userInfo = makeUser()
      const proj = useProject()
      proj.project = makeProject()
      const perm = usePermission()
      perm.setProjectPermissions([PERM.DOCS_READ])

      const wrapper = mount(GeneralDocsIndex, defaultMountOptions())
      await flushPromises()
      mockApi.patch.mockClear()

      const vm = wrapper.vm as unknown as {
        docsHit: (pk: number) => Promise<void>
        linkHit: (pk: number) => Promise<void>
        fileHit: (pk: number) => Promise<void>
      }
      await vm.docsHit(101)
      await vm.docsHit(101)
      await vm.linkHit(11)
      await vm.fileHit(21)

      expect(mockApi.patch).not.toHaveBeenCalled()
      expect(mockApi.post).toHaveBeenCalledWith('/docs/101/hit/')
      expect(mockApi.post).toHaveBeenCalledWith('/link/11/hit/')
      expect(mockApi.post).toHaveBeenCalledWith('/file/21/hit/')
      expect(mockApi.post).toHaveBeenCalledTimes(3)
    })

    it('DOCS_READ 권한이 없는 프로젝트 선택 시 API를 호출하지 않는다', async () => {
      const acc = useAccount()
      acc.userInfo = makeUser()
      const work = useWork()
      work.myProjects = [makeIssueProject(10, 'dev-proj-1', [])]
      work.currentProject = work.myProjects[0]
      const proj = useProject()
      proj.project = makeProject()
      const perm = usePermission()
      perm.setProjectPermissions([])

      mount(GeneralDocsIndex, defaultMountOptions())
      await flushPromises()

      expect(mockApi.get).not.toHaveBeenCalled()
    })
  })

  describe('LawsuitCase & CaseDetail & DocsDetail & TrashCan', () => {
    it('CaseDetail은 related_case가 null일 때 "null" caseId 라우터 링크를 생성하지 않고 권한 기준으로 수정/삭제 버튼을 노출한다', () => {
      mockRoute.name = '소송 사건 관리 - 보기'
      mockRoute.params = { caseId: '301' }
      const acc = useAccount()
      acc.userInfo = makeUser({ pk: 1, username: 'staff' })
      const work = useWork()
      const ip = makeIssueProject(10, 'dev-proj-1', [
        PERM.DOCS_READ,
        PERM.DOCS_UPDATE,
        PERM.DOCS_DELETE,
      ])
      work.myProjects = [ip]
      work.currentProject = ip
      const perm = usePermission()
      perm.setProjectPermissions([PERM.DOCS_READ, PERM.DOCS_UPDATE, PERM.DOCS_DELETE])

      const wrapper = mount(CaseDetail, {
        props: {
          suitcase: makeSuitCase({ related_case: null }),
          viewRoute: '소송 사건 관리',
          currPage: 1,
        },
        ...defaultMountOptions(),
      })

      const links = wrapper.findAll('a[data-to]')
      expect(links.some(a => a.attributes('data-to')?.includes('"caseId":"null"'))).toBe(false)
      const btnTexts = wrapper.findAll('button').map(b => b.text())
      expect(btnTexts).toContain('수정')
      expect(btnTexts).toContain('삭제')
    })

    it('LawsuitCase의 excelUrl은 related_case와 URL 인코딩된 search를 포함한다', async () => {
      mockRoute.name = '소송 사건 관리'
      const acc = useAccount()
      acc.userInfo = makeUser()
      const proj = useProject()
      proj.project = makeProject({ pk: 3, company: 7 })
      const perm = usePermission()
      perm.setProjectPermissions([PERM.DOCS_READ])

      const wrapper = mount(LawsuitCaseIndex, defaultMountOptions())
      await flushPromises()

      const vm = wrapper.vm as unknown as {
        agencySearch: (q: string) => void
        relatedFilter: (id: number) => void
        excelUrl: string
      }
      vm.agencySearch('A&B 법원')
      vm.relatedFilter(44)
      await flushPromises()

      expect(vm.excelUrl).toContain('company=7')
      expect(vm.excelUrl).toContain('project=3')
      expect(vm.excelUrl).toContain('related_case=44')
      expect(vm.excelUrl).toContain('search=A%26B')
    })

    it('DocsDetail은 superAuth 사용자 본문을 숨기지 않고 execution_date 없이도 관련사건 테이블을 표시하며 copy 시 nowProject를 전달한다', async () => {
      mockRoute.name = '소송 문서 관리 - 보기'
      mockRoute.params = { docsId: '101' }
      const acc = useAccount()
      acc.userInfo = makeUser({ pk: 99, is_superuser: true, work_manager: false })
      const perm = usePermission()
      perm.setProjectPermissions([PERM.DOCS_READ, PERM.DOCS_UPDATE])

      const docStore = useDocs()
      const targetDoc = makeDoc({
        doc_type: 2,
        execution_date: null,
        lawsuit: 301,
        lawsuit_name: '2026가합1234 분양대금',
        is_pinned: true,
        is_blind: true,
        security_level: '1',
      })
      docStore.setDocs(targetDoc)

      const wrapper = mount(DocsDetail, {
        props: {
          typeNum: 2,
          heatedPage: [101],
          reOrder: false,
          docs: targetDoc,
          viewRoute: '소송 문서 관리',
          currPage: 1,
        },
        ...defaultMountOptions(),
      })
      await flushPromises()

      expect(wrapper.html()).toContain('2026가합1234 분양대금')
      expect(wrapper.find('.mdi-bullhorn').exists()).toBe(true)

      const vm = wrapper.vm as unknown as {
        copyDocs: (nType?: number, nProj?: number) => Promise<void>
      }
      await vm.copyDocs(1, 10)
      expect(mockApi.post).toHaveBeenCalledWith('/docs/101/copy/', {
        docs: 101,
        doc_type: 1,
        issue_project: 10,
      })
    })

    it('ProDocsAuthGuard global 모드는 무관한 currentProject가 남아 있어도 globalPermSet에 DOCS_READ가 있으면 TrashCan 접근을 허용한다', async () => {
      const acc = useAccount()
      acc.userInfo = makeUser()
      const work = useWork()
      const projNoDocs = makeIssueProject(1, 'no-docs-ws', [])
      const projWithDocs = makeIssueProject(2, 'has-docs-ws', [PERM.DOCS_READ])
      work.myProjects = [projNoDocs, projWithDocs]
      work.currentProject = projNoDocs
      const perm = usePermission()
      perm.setProjectPermissions([])

      const wrapper = mount(ProDocsAuthGuard, {
        props: { global: true },
        slots: { default: '<div class="trash-allowed">OK</div>' },
        ...defaultMountOptions(),
      })

      expect(wrapper.find('.trash-allowed').exists()).toBe(true)
    })

    it('TrashDocsList와 TrashDocsDetail은 closed 프로젝트(status=2)나 삭제권한 없는 문서의 복원/완전삭제 버튼을 차단한다', () => {
      const acc = useAccount()
      acc.userInfo = makeUser({ pk: 1, username: 'staff' })
      const work = useWork()
      const closedProj = makeIssueProject(
        20,
        'closed-proj',
        [PERM.DOCS_READ, PERM.DOCS_UPDATE, PERM.DOCS_DELETE],
        '2',
      )
      const openOwnProj = makeIssueProject(21, 'open-proj', [PERM.DOCS_READ, PERM.DOCS_OWN_UPDATE])
      work.myProjects = [closedProj, openOwnProj]

      const closedDoc: TrashDocs = {
        pk: 1,
        doc_type: 1,
        type_name: '일반문서',
        cate_name: '일반',
        project_name: '닫힌 프로젝트',
        project_slug: 'closed-proj',
        title: '닫힌 문서',
        description: '',
        creator: 'staff',
        created: '2026-01-01',
        deleted: '2026-01-02',
      }
      const ownUpdateOnlyDoc: TrashDocs = {
        pk: 2,
        doc_type: 1,
        type_name: '일반문서',
        cate_name: '일반',
        project_name: '열린 프로젝트',
        project_slug: 'open-proj',
        title: '복원만 가능 문서',
        description: '',
        creator: 'staff',
        created: '2026-01-01',
        deleted: '2026-01-02',
      }

      const listWrapper = mount(TrashDocsList, {
        props: {
          trashDocsList: [closedDoc, ownUpdateOnlyDoc],
          trashDocsCount: 2,
          viewRoute: '문서 휴지통',
          page: 1,
        },
        ...defaultMountOptions(),
      })
      expect(listWrapper.findAll('.mdi-delete-restore')).toHaveLength(1)
      expect(listWrapper.findAll('.mdi-delete-forever-outline')).toHaveLength(0)

      const detailWrapper = mount(TrashDocsDetail, {
        props: {
          docs: ownUpdateOnlyDoc,
          viewRoute: '문서 휴지통',
        },
        ...defaultMountOptions(),
      })
      const btnTexts = detailWrapper.findAll('button').map(b => b.text())
      expect(btnTexts).toContain('복원하기')
      expect(btnTexts).not.toContain('완전 삭제')
    })

    it('TrashCan은 마지막 페이지의 유일한 항목 삭제 성공 시 이전 페이지로 보정한다', async () => {
      mockRoute.name = '문서 휴지통'
      const acc = useAccount()
      acc.userInfo = makeUser({ is_superuser: true })
      const work = useWork()
      work.myProjects = [makeIssueProject(2, 'has-docs-ws', [PERM.DOCS_READ, PERM.DOCS_DELETE])]

      const wrapper = mount(TrashCanIndex, defaultMountOptions())
      await flushPromises()

      const docStore = useDocs()
      docStore.trashDocsList = [
        {
          pk: 90,
          type_name: '일반문서',
          cate_name: '일반',
          title: '마지막 항목',
          description: '',
          creator: 'staff',
          created: '2026-01-01',
          deleted: '2026-01-02',
        },
      ]
      docStore.trashDocsCount = 11

      const vm = wrapper.vm as unknown as {
        page: number
        callDeleteDocs: (pk: number) => void
        delModalAction: () => Promise<void>
      }
      vm.page = 2
      vm.callDeleteDocs(90)
      mockApi.get.mockClear()
      await vm.delModalAction()

      expect(mockApi.delete).toHaveBeenCalledWith('/docs-trash-can/90/?hard=1')
      expect(mockApi.get).toHaveBeenCalledWith('/docs-trash-can/?limit=10&page=1')
      expect(vm.page).toBe(1)
    })
  })
})
