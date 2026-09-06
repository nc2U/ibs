<script lang="ts" setup>
import { computed } from 'vue'
import { navMenu, pageTitle } from '@/views/sales/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import type { Project } from '@/store/types/project'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
</script>

<template>
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />
  <ContentBody>
    <CCard class="mb-4">
      <CCardBody>
        <div class="py-5 text-center text-medium-emphasis">
          <CIcon icon="cil-money" size="3xl" class="mb-3 text-secondary" />
          <h5 class="fw-bold">수수료 지급 관리</h5>
          <p class="mb-1 text-body-secondary">
            정산 승인 대장, 은행 이체 파일(엑셀) 생성, 회계(비용화) 지출 전표 연계 및 지급 이력을 관리합니다.
          </p>
          <small class="text-muted">기능 개발 및 DB 모델링 준비 단계입니다.</small>
        </div>
      </CCardBody>
    </CCard>
  </ContentBody>
</template>
