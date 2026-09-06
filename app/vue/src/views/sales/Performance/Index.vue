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
          <CIcon icon="cil-spreadsheet" size="3xl" class="mb-3 text-secondary" />
          <h5 class="fw-bold">계약 실적 관리</h5>
          <p class="mb-1 text-body-secondary">
            체결된 분양계약(Contract)과 담당 영업 인력/팀을 매핑하고 실시간 계약 실적 현황을 모니터링합니다.
          </p>
          <small class="text-muted">기능 개발 및 DB 모델링 준비 단계입니다.</small>
        </div>
      </CCardBody>
    </CCard>
  </ContentBody>
</template>
