<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import type { IssueProject } from '@/store/types/work_project'
import { markdownRender } from '@/utils/helper'

// 컴포넌트 자체 참조를 위해 이름 명시
defineOptions({
  name: 'ProjectCard',
})

defineProps({
  project: {
    type: Object as PropType<IssueProject>,
    required: true,
  },
})

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const isOwnProject = (project: IssueProject) => {
  if (!userInfo.value?.pk) return false
  return project.all_members?.some(m => m.user.pk === userInfo.value?.pk) ?? false
}
</script>

<template>
  <div v-if="project.visible" class="project-item">
    <div class="project-header">
      <router-link
        :to="{ name: '(개요)', params: { projId: project.slug } }"
        :class="{ 'text-grey': project.status !== '1' }"
      >
        {{ project.name }}
      </router-link>
      <v-icon
        v-if="!project.is_public"
        icon="mdi-lock"
        color="blue-grey-lighten-2"
        size="15"
        class="ms-2"
        title="비공개 워크스페이스"
      />
      <v-icon
        v-if="isOwnProject(project)"
        icon="mdi-account-tag"
        color="success"
        size="15"
        class="ms-2"
        title="내 워크스페이스"
      />
      <v-icon
        v-if="project?.is_bookmarked"
        icon="mdi-bookmark"
        color="info"
        size="15"
        class="ms-2"
        title="북마크됨"
      />
      <div v-if="project.description" class="project-desc" v-html="markdownRender(project.description)" />
    </div>

    <!-- 재귀 호출: 하위 프로젝트가 있는 경우 -->
    <div v-if="project.sub_projects && project.sub_projects.length > 0" class="child">
      <template v-for="sub in project.sub_projects" :key="sub.pk">
        <ProjectCard v-if="sub.visible" :project="sub" />
      </template>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.project-item {
  margin-bottom: 0; // margin 제거
}

.project-header a {
  font-weight: bold;
  font-size: 1.13em;
}

.project-header a.text-grey {
  color: #888888 !important;
}

.child {
  padding-left: 12px;
  border-left: 3px solid #ddd;
  margin-top: 0.15rem; // 아주 작은 간격 추가

  // 하위 레벨일수록 폰트 크기 조절
  .project-header a {
    font-size: 1em;
    font-weight: normal;
  }
}
</style>
