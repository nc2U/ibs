import { createRouter, createWebHashHistory } from 'vue-router'
import Cookies from 'js-cookie'
import routes from '@/router/routes'

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 계약 관련 페이지 매핑 테이블: 기본 페이지명 → 상세 페이지명
const contractPageMapping: Record<string, string> = {
  '계약 상세 관리': '계약 상세 보기',
  '권리 의무 승계': '권리 의무 승계 보기',
  '계약 해지 관리': '계약 해지 보기',
}

router.beforeEach((to, from, next) => {
  if (!!to.meta.auth) Cookies.set('redirectPath', to.path)

  // contractorId 자동 전달 로직
  const fromContractorId = from.params.contractorId

  // 현재 페이지에서 contractorId가 있고, 이동하려는 페이지가 계약 관련 기본 페이지인 경우
  if (fromContractorId && to.name && contractPageMapping[to.name as string]) {
    const detailRouteName = contractPageMapping[to.name as string]
    next({ name: detailRouteName, params: { contractorId: fromContractorId } })
  } else {
    next()
  }
})

export default router
