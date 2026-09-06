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
          <CIcon icon="cil-briefcase" size="3xl" class="mb-3 text-secondary" />
          <h5 class="fw-bold">영업 조직 및 인력 관리</h5>
          <p class="mb-1 text-body-secondary">
            프로젝트별 분양대행 영업 조직(본부/팀) 구성 및 분양상담사, 프리랜서(3.3%) 인력을 관리합니다.
          </p>
          <small class="text-muted">기능 개발 및 DB 모델링 준비 단계입니다.</small>
        </div>
      </CCardBody>
    </CCard>
  </ContentBody>
</template>
