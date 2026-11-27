import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { useNotice } from '@/store/pinia/notice'
import { usePayment } from '@/store/pinia/payment'
import { useProject } from '@/store/pinia/project'
import { usePermission } from '@/store/pinia/work_permission'
import { PERM } from '@/store/constants/permissions'
import type { User } from '@/store/types/accounts'
import type { Company } from '@/store/types/settings'
import type { Project } from '@/store/types/project'
import type { MessageSendHistoryList } from '@/store/types/notice'
import ContractRow from '../Bill/components/Contract.vue'
import SalesBillIssueForm from '../Bill/components/SalesBillIssueForm.vue'
import HistoryTable from '../Sms/components/HistoryTable.vue'
import HistoryFilter from '../Sms/components/HistoryFilter.vue'
import SelectMessage from '../Sms/components/SelectMessage.vue'
import SendMessage from '../Sms/components/SendMessage.vue'
import { formatMailMergePreview } from '../Mailing/preview'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

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

vi.mock('@/utils/baseMixins', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/baseMixins')>()
  return {
    ...actual,
    getToday: () => '2026-11-28',
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
  template: '<a><slot /></a>',
})

const makeVuetify = () => createVuetify({ components, directives })

const makeUser = (overrides: Partial<User> = {}): User => ({
  pk: 1,
  email: 'staff@example.com',
  username: 'staff',
  is_active: true,
  is_superuser: false,
  is_staff: false,
  work_manager: false,
  date_joined: '2026-01-01',
  profile: null,
  last_login: null,
  is_hq_staff: true,
  has_staff: true,
  staff_name: '홍길동',
  staff_phone: '010-1234-5678',
  staff_fax: '02-1111-2222',
  ...overrides,
})

const makeProject = (overrides: Partial<Project> = {}): Project =>
  ({
    pk: 10,
    company: 1,
    name: '테스트 프로젝트',
    issue_project: 5,
    issue_project_slug: 'test-proj',
    ...overrides,
  }) as unknown as Project

const makeCompany = (overrides: Partial<Company> = {}): Company =>
  ({
    pk: 7,
    name: '주식회사 테스트',
    ...overrides,
  }) as unknown as Company

describe('notices module regression suite', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    const accountStore = useAccount()
    accountStore.userInfo = makeUser({ is_superuser: true, work_manager: true })
    const permStore = usePermission()
    permStore.setProjectPermissions([
      PERM.NOTICE_READ,
      PERM.NOTICE_CREATE,
      PERM.NOTICE_UPDATE,
      PERM.NOTICE_DELETE,
    ])
    const projectStore = useProject()
    projectStore.project = makeProject()
    const companyStore = useCompany()
    companyStore.company = makeCompany()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('fetches SalesBillIssue by project query parameter instead of PK path', async () => {
    const noticeStore = useNotice()
    const bill = {
      pk: 99,
      project: 10,
      now_payment_order: 3,
      host_name: '테스트시행사',
      host_tel: '02-1111-2222',
      agency: '',
      agency_tel: '',
      bank_account1: '국민은행',
      bank_number1: '123-456',
      bank_host1: '예금주',
      bank_account2: '',
      bank_number2: '',
      bank_host2: '',
      zipcode: '06100',
      address1: '서울 강남구',
      address2: '101호',
      address3: '',
      title: '고지서',
      content: '내용',
    }
    mockApi.get.mockResolvedValueOnce({ data: { count: 1, results: [bill] } })

    const res = await noticeStore.fetchSalesBillIssue(10)

    expect(mockApi.get).toHaveBeenCalledWith('/sales-bill-issue/', { params: { project: 10 } })
    expect(res).toEqual(bill)
    expect(noticeStore.billIssue).toEqual(bill)
  })

  it('updates billIssue and payOrder when creating a SalesBillIssue', async () => {
    const noticeStore = useNotice()
    const paymentStore = usePayment()
    const paySpy = vi.spyOn(paymentStore, 'fetchPayOrder').mockResolvedValue({
      pk: 5,
      pay_code: 3,
      pay_time: 2,
      pay_due_date: '2026-12-31',
    } as never)

    const payload = {
      pk: null,
      project: 10,
      now_payment_order: 5,
      host_name: '시행사',
      host_tel: '02-1111-2222',
      agency: '',
      agency_tel: '',
      bank_account1: '국민은행',
      bank_number1: '111-222',
      bank_host1: '시행사',
      bank_account2: '',
      bank_number2: '',
      bank_host2: '',
      zipcode: '06100',
      address1: '서울시 강남구',
      address2: '',
      address3: '',
      title: '제목',
      content: '내용',
    }
    mockApi.post.mockResolvedValueOnce({ data: { ...payload, pk: 42 } })

    const created = await noticeStore.createSalesBillIssue(payload)

    expect(created.pk).toBe(42)
    expect(noticeStore.billIssue?.pk).toBe(42)
    expect(paySpy).toHaveBeenCalledWith(5)
  })

  it('emits only one error toast per failed notice action', async () => {
    const noticeStore = useNotice()
    mockApi.post.mockRejectedValueOnce({
      response: { data: { detail: '발송 권한이 없습니다.' } },
    })

    await expect(
      noticeStore.sendKakao({
        template_code: 'T1',
        recipients: [{ phone: '010-1234-5678' }],
        sender_number: '02-1234-5678',
      }),
    ).rejects.toBeDefined()

    expect(mockMessage).toHaveBeenCalledTimes(1)
    expect(mockErrorHandle).not.toHaveBeenCalled()
  })

  it('uses KST date and supports personalized SMS without crashing in sendSMS and appends project in sendMMS', async () => {
    vi.useFakeTimers()
    const noticeStore = useNotice()

    mockApi.post.mockResolvedValueOnce({
      data: { resultCode: 0, message: 'ok', requestNo: 'REQ-1', msgType: 'SMS' },
    })
    mockApi.get.mockResolvedValueOnce({
      data: {
        resultCode: 0,
        message: 'ok',
        totalCount: 1,
        list: [
          {
            requestNo: 'REQ-1',
            companyid: 'company7',
            msgType: 'SMS',
            phone: '01012345678',
            callback: '0212345678',
            sendStatusCode: '06',
            sendDate: '2026-11-28',
          },
        ],
      },
    })

    const smsPromise = noticeStore.sendSMS({
      message_type: 'SMS',
      sender_number: '02-1234-5678',
      company_id: 'company7',
      project: 10,
      is_personalized: true,
      personalized_recipients: [{ phone: '010-1234-5678', message: '홍길동님 안내' }],
    })
    await vi.advanceTimersByTimeAsync(2500)
    await smsPromise

    expect(mockApi.get).toHaveBeenCalledWith('/messages/send-history/', {
      params: expect.objectContaining({
        start_date: '2026-11-28',
        end_date: '2026-11-28',
        request_no: 'REQ-1',
      }),
    })
    expect(mockMessage).toHaveBeenCalledWith(
      'success',
      '발송 성공',
      'SMS가 성공적으로 발송되었습니다. (1건)',
    )

    const img = new File(['abc'], 'photo.jpg', { type: 'image/jpeg' })
    mockApi.post.mockResolvedValueOnce({
      data: { resultCode: 0, message: 'ok', requestNo: 'REQ-2', msgType: 'MMS' },
    })

    await noticeStore.sendMMS({
      message: '포토 안내',
      sender_number: '02-1234-5678',
      recipients: ['010-1234-5678'],
      project: 10,
      image: img,
    })

    const sentFormData = mockApi.post.mock.calls[1][1] as FormData
    expect(sentFormData.get('project')).toBe('10')
  })

  it('compares paid status in Contract row using pay_code when available', () => {
    const wrapper = mount(ContractRow, {
      global: {
        plugins: [makeVuetify(), CoreuiVue],
        stubs: { RouterLink: RouterLinkStub, CIcon: true },
      },
      props: {
        nowOrder: 3,
        contract: {
          pk: 1,
          order_group_desc: { pk: 1, sort: '1', name: '1차' },
          unit_type_desc: null,
          serial_number: 'S-001',
          key_unit: null,
          contractor: { pk: 11, name: '홍길동', contract_date: '2026-01-01' },
          total_paid: 10000000,
          last_paid_order: {
            pk: 2,
            pay_sort: '2',
            pay_code: 2,
            pay_time: 3, // pay_time은 높지만 pay_code는 목표 회차(3)보다 낮음
            pay_name: '1차 중도금',
            str_display: '1차 중도금',
          },
        } as never,
      },
    })

    expect(wrapper.text()).toContain('미납중')
    expect(wrapper.find('input[type="checkbox"]').attributes('disabled')).toBeUndefined()
  })

  it('emits get-now-order when user changes payment order in SalesBillIssueForm', async () => {
    const paymentStore = usePayment()
    paymentStore.payOrderList = [
      { pk: 1, str_display: '1회차', pay_due_date: '2026-05-01' },
      { pk: 2, str_display: '2회차', pay_due_date: '2026-06-01' },
    ] as never

    const wrapper = mount(SalesBillIssueForm, {
      global: {
        plugins: [makeVuetify(), CoreuiVue],
        stubs: {
          CIcon: true,
          DatePicker: {
            props: ['modelValue'],
            template: '<input :value="modelValue || \'\'" />',
          },
          DaumPostcode: true,
          ConfirmModal: true,
          AlertModal: true,
        },
        directives: { maska: {} },
      },
      props: {
        project: 10,
        billIssue: null,
      },
    })

    const select = wrapper.find('select')
    await select.setValue('2')

    expect(wrapper.emitted('get-now-order')?.[0]).toEqual([2])
  })

  it('passes activePage prop cleanly in HistoryTable and initializes KST dates in HistoryFilter', () => {
    const noticeStore = useNotice()
    noticeStore.messageSendHistory = {
      count: 45,
      next: 'http://localhost/api/v1/message-send-history/?page=3',
      previous: 'http://localhost/api/v1/message-send-history/?page=1',
      results: [
        {
          id: 1,
          message_type: 'SMS',
          sender_number: '02-1234-5678',
          title: '안내',
          message_content: '테스트',
          recipient_count: 1,
          sent_at: '2026-11-28T10:00:00Z',
          request_no: 'R1',
          scheduled_send: false,
          sent_by: { pk: 1, username: 'staff' },
          created: '2026-11-28T10:00:00Z',
        } as MessageSendHistoryList,
      ],
    }

    const tableWrapper = mount(HistoryTable, {
      global: {
        plugins: [makeVuetify(), CoreuiVue],
      },
      props: {
        loading: false,
        currentPage: 2,
      },
    })

    expect(tableWrapper.get('.page-item.active').text()).toBe('2')

    const filterWrapper = mount(HistoryFilter, {
      global: {
        plugins: [makeVuetify(), CoreuiVue],
        stubs: {
          DatePicker: {
            props: ['modelValue'],
            template: '<input class="dp" :value="modelValue" />',
          },
        },
      },
    })
    const inputs = filterWrapper.findAll('input.dp')
    expect((inputs[0].element as HTMLInputElement).value).toBe('2026-11-21')
    expect((inputs[1].element as HTMLInputElement).value).toBe('2026-11-28')
  })

  it('auto-switches SMS to LMS using UTF-8 byte count (>90 bytes) without mutating SendMessage props', async () => {
    mockApi.get.mockResolvedValue({ data: [] })
    const smsForm = {
      messageType: 'SMS' as const,
      message: '',
      senderNumber: '',
      scheduledSend: false,
      scheduleDate: '',
      scheduleTime: '',
    }
    const kakaoForm = {
      templateId: '',
      message: '',
      senderNumber: '',
      parameters: {},
      scheduledSend: false,
      scheduleDate: '',
      scheduleTime: '',
      reSend: true,
      resendType: 'Y' as const,
      resendTitle: '',
      resendContent: '',
    }

    const msgWrapper = mount(SelectMessage, {
      global: {
        plugins: [makeVuetify(), CoreuiVue],
        stubs: {
          SenderNumberModal: true,
          MessageTemplateModal: true,
          SpecialCharModal: true,
          KakaoGuideModal: true,
        },
      },
      props: {
        activeTab: 'sms',
        smsForm,
        kakaoForm,
      },
    })
    await flushPromises()

    // 한글 31자 = 93 UTF-8 bytes (> 90 bytes) => 자동 LMS 전환
    await msgWrapper.setProps({
      smsForm: { ...smsForm, message: '가'.repeat(31) },
    })
    expect(msgWrapper.emitted('update:smsForm')?.[0]?.[0]).toMatchObject({
      messageType: 'LMS',
    })

    const sendWrapper = mount(SendMessage, {
      global: {
        plugins: [makeVuetify(), CoreuiVue],
        stubs: {
          DatePicker: true,
          TimePicker: true,
        },
      },
      props: {
        activeTab: 'sms',
        currentForm: { scheduledSend: false, scheduleDate: '', scheduleTime: '' },
        isDisabled: false,
        buttonText: 'SMS 전송',
        isSending: false,
        sendProgress: 50,
      },
    })

    await sendWrapper.get('button').trigger('click')
    expect(sendWrapper.emitted('sendMessage')).toHaveLength(1)
  })

  it('sanitizes HTML merge preview while preserving merge tags', () => {
    const clean = formatMailMergePreview('<p>{{ 계약자명 }}</p><script>alert(1)</script>')
    expect(clean).toContain('{{ 계약자명 }}')
    expect(clean).not.toContain('<script>')
  })
})
