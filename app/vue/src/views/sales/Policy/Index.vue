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
          <CIcon icon="cil-cog" size="3xl" class="mb-3 text-secondary" />
          <h5 class="fw-bold">수수료 정책 관리</h5>
          <p class="mb-1 text-body-secondary">
            유니트 및 타입별 건당 인센티브 기준표와 직급별(상담사/팀장/본부장) 수수료 요율(R값)을 설정합니다.
          </p>
          <small class="text-muted">기능 개발 및 DB 모델링 준비 단계입니다.</small>
        </div>
      </CCardBody>
    </CCard>
  </ContentBody>
</template>
