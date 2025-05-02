<script lang="ts" setup>
import { inject, onBeforeMount, type ComputedRef, type PropType } from 'vue'
import type { User } from '@/store/types/accounts'
import { useRoute } from 'vue-router'
import type { IssueProject, ProjectFilter } from '@/store/types/work'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'
import SearchList from './SearchList.vue'
import ProjectCard from './ProjectCard.vue'
import NoData from '@/views/_Work/components/NoData.vue'

defineProps({
  projectList: { type: Array as PropType<IssueProject[]>, default: () => [] },
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
})

const emit = defineEmits(['aside-visible', 'filter-submit'])

const workManager = inject<ComputedRef<boolean>>('workManager')

const route = useRoute()

const filterSubmit = (payload: ProjectFilter) => emit('filter-submit', payload)

onBeforeMount(() => emit('aside-visible', true))
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>프로젝트</h5>
    </CCol>

    <CCol v-if="workManager" class="text-right form-text">
      <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link :to="{ name: '프로젝트 - 추가' }" class="ml-1">새 프로젝트</router-link>
      </span>
      <span>
        <v-icon icon="mdi-cog" color="secondary" size="sm" />
        <router-link :to="{ name: '(프로젝트)' }" class="ml-1">관리</router-link>
      </span>
    </CCol>
  </CRow>

  <SearchList :all-projects="allProjects" @filter-submit="filterSubmit" />

  <NoData v-if="!projectList.length" />

  <CRow v-else>
    <template v-for="(proj, i) in projectList" :key="proj.pk">
      <CCol sm="6">
        <ProjectCard :project="proj" />
      </CCol>
    </template>
  </CRow>

  <CRow>
    <CCol class="text-right form-text">
      <span class="mr-2">
        <v-icon icon="mdi-account-tag" color="success" size="15" class="mr-1" />
        <span class="mt-2">내 프로젝트</span>
      </span>

      <span>
        <v-icon icon="mdi-bookmark" color="info" size="15" class="mr-1" />
        <span class="mt-2">내 북마크</span>
      </span>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
.project-set {
  padding-bottom: 0;
}

.project-set a {
  font-weight: bold;
  font-size: 1.13em;
}

.project-set .child {
  a {
    font-size: 0.96em;
    font-weight: normal;
  }

  padding-left: 12px;
  border-left: 3px solid #ddd;
}
</style>
