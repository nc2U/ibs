import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useSalesNavMenu } from '../_menu/headermixin'
import { useWork } from '@/store/pinia/work_project'
import { useAccount } from '@/store/pinia/account'

describe('useSalesNavMenu Test', () => {
  it('returns all sales menus for project when user has sales permissions in myProjects', () => {
    setActivePinia(createPinia())
    const accountStore = useAccount()
    const workStore = useWork()

    // Non-superuser, non-workManager (e.g. 김민주)
    accountStore.userInfo = {
      is_superuser: false,
      work_manager: false,
      has_staff: true,
    } as any

    // allReadableProjects is empty (as it is when not visiting _Work)
    workStore.allReadableProjects = []

    // myProjects is loaded on app startup
    workStore.myProjects = [
      {
        pk: 3,
        name: '[인천] 동춘 조합',
        project: 1,
        status: '1',
        visible: true,
        my_perms: [
          'sales.read',
          'sales.settle',
          'sales.payout',
          'sales.policy',
          'sales.manage',
        ],
      } as any,
    ]

    const project = ref<number | null>(1)
    const navMenu = useSalesNavMenu(project)

    expect(navMenu.value).toEqual([
      '계약 실적 관리',
      '수수료 정산 관리',
      '수수료 지급 관리',
      '수수료 정책 관리',
      '영업 조직 관리',
    ])
  })

  it('returns empty array when user has no permissions for project', () => {
    setActivePinia(createPinia())
    const accountStore = useAccount()
    const workStore = useWork()

    accountStore.userInfo = {
      is_superuser: false,
      work_manager: false,
      has_staff: true,
    } as any
    workStore.allReadableProjects = []
    workStore.myProjects = [
      {
        pk: 3,
        name: '[인천] 동춘 조합',
        project: 1,
        status: '1',
        visible: true,
        my_perms: [],
      } as any,
    ]

    const project = ref<number | null>(1)
    const navMenu = useSalesNavMenu(project)

    expect(navMenu.value).toEqual([])
  })
})
