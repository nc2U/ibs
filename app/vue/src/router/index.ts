import { createRouter, createWebHashHistory } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
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

router.beforeEach(async (to, from, next) => {
  const accountStore = useAccount()
  const accessToken = Cookies.get('accessToken')

  if (to.meta.auth) {
    if (!accountStore.userInfo) {
      if (accessToken) {
        await accountStore.loginByToken(accessToken)
      }

      if (!accountStore.userInfo) {
        localStorage.setItem('redirectPath', to.path)
        return next({ name: 'Login' })
      }
    }
  }

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

/**
 * 신규 배포 등으로 이전 빌드의 동적 청크(JS 파일)를 찾을 수 없는 경우(404),
 * 브라우저를 1회 새로고침하여 최신 번들을 로드하도록 자동 복구합니다.
 */
function handleChunkLoadError(targetPath?: string) {
  const pathKey = targetPath || window.location.hash.replace(/^#/, '') || '/'
  const reloadKey = `chunk_reload_${pathKey}`
  const hasReloaded = sessionStorage.getItem(reloadKey)

  if (!hasReloaded) {
    sessionStorage.setItem(reloadKey, 'true')
    if (targetPath) {
      window.location.hash = `#${targetPath}`
    }
    window.location.reload()
  } else {
    sessionStorage.removeItem(reloadKey)
    console.error('청크 로드 실패: 새로고침 후에도 모듈을 불러오지 못했습니다.')
  }
}

// 1. Vite 청크 사전 로드 실패 이벤트 감지
window.addEventListener('vite:preloadError', (event: Event) => {
  event.preventDefault()
  handleChunkLoadError()
})

// 2. Vue Router 비동기 컴포넌트 로드 실패 감지
router.onError((error, to) => {
  const chunkFailedMessages = [
    'Failed to fetch dynamically imported module',
    'Loading chunk',
    'Importing a module script failed',
    'error loading dynamically imported module',
  ]

  const isChunkLoadFailed = chunkFailedMessages.some(msg => error?.message?.includes(msg))

  if (isChunkLoadFailed) {
    handleChunkLoadError(to?.fullPath)
  }
})

// 3. 페이지 이동 정상 완료 시 재시도 플래그 정리
router.afterEach(() => {
  for (let i = sessionStorage.length - 1; i >= 0; i--) {
    const key = sessionStorage.key(i)
    if (key?.startsWith('chunk_reload_')) {
      sessionStorage.removeItem(key)
    }
  }
})

export default router
