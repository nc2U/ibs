import { computed, h, resolveComponent } from 'vue'
import { useAccount } from '@/store/pinia/account'

const account = computed(() => useAccount())
const pageViewAuth = computed(
  () =>
    account.value.userInfo?.is_superuser ||
    (account.value.userInfo?.staffauth && account.value.userInfo.staffauth?.company_cash > '0'),
)

const comCash = {
  path: 'cashes',
  name: '본사 자금 관리',
  redirect: '/cashes/status',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'status',
      name: '본사 자금 현황',
      component: () =>
        pageViewAuth.value
          ? import('@/views/comCash/Status/Index.vue')
          : import('@/views/_Accounts/NoAuth.vue'),
      meta: { title: '본사 자금 현황', auth: true },
    },
    {
      path: 'index',
      name: '본사 출납 내역',
      component: () =>
        pageViewAuth.value
          ? import('@/views/comCash/CashManage/Index.vue')
          : import('@/views/_Accounts/NoAuth.vue'),
      meta: { title: '본사 출납 내역', auth: true },
    },
  ],
}

export default comCash
