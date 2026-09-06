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
          <CIcon icon="cil-calculator" size="3xl" class="mb-3 text-secondary" />
          <h5 class="fw-bold">수수료 정산 관리</h5>
          <p class="mb-1 text-body-secondary">
            계약금 납부 확인 기반의 인센티브 자동 산출, 기본 일비/활동비 합산, 3.3% 사업소득세 공제액을 정산합니다.
          </p>
          <small class="text-muted">기능 개발 및 DB 모델링 준비 단계입니다.</small>
        </div>
      </CCardBody>
    </CCard>
  </ContentBody>
</template>
