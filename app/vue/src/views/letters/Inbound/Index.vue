<script setup lang="ts">
import { useRouter } from 'vue-router'
import { navMenu, pageTitle } from '@/views/letters/_menu/headermixin'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComAuthGuard from '@/components/AuthGuard/ComAuthGuard.vue'

const router = useRouter()
const comSelect = (_target: number | null) => {}

const goToProjectDocs = () => {
  router.push({ name: '일반 문서 관리' })
}
</script>

<template>
  <ComAuthGuard>
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <div class="py-5 text-center">
          <div class="mb-4">
            <CIcon name="cilEnvelopeClosed" size="4xl" class="text-primary opacity-75" />
          </div>
          <h4 class="fw-bold mb-3">수신 공문 관리 준비 중</h4>
          <p class="text-muted mb-4 mx-auto" style="max-width: 620px; line-height: 1.8">
            수신 공문(대외 기관 및 협력사로부터 수신된 공문서)의 접수, 부서 배부, 접수번호 부여 및
            전자결재 공람/후속 조치 통합 관리 시스템을 고도화하고 있습니다.<br />
            현재 프로젝트별 수신 공문은 <strong>문서 소송 관리 &gt; 일반 문서 관리</strong>의
            <strong>[수신공문]</strong> 카테고리에서 확인 및 등록하실 수 있습니다.
          </p>
          <div class="d-flex justify-content-center gap-2">
            <CButton color="primary" variant="outline" @click="goToProjectDocs">
              <CIcon name="cilLibrary" class="me-1" />
              문서 소송 관리 (수신공문) 바로가기
            </CButton>
            <CButton color="secondary" variant="ghost" @click="router.push({ name: '발송 공문 관리' })">
              <CIcon name="cilEnvelopeLetter" class="me-1" />
              발송 공문 관리로 이동
            </CButton>
          </div>
        </div>
      </CCardBody>
    </ContentBody>
  </ComAuthGuard>
</template>
