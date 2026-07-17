<script lang="ts" setup>
import AllProjectsSelect from '@/views/_Work/components/atomics/AllProjectsSelect.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import type { PropType } from 'vue'
import type { Category } from '@/store/types/docs.ts'
import type { selectProject } from '@/store/types/work_project.ts'

defineProps({
  myProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  categoryList: { type: Array as PropType<Category[]>, default: () => [] },
  filter: { type: Object, required: true },
  typeNumber: { type: Number, default: 1 },
  suitCaseOptions: { type: Array, default: () => [] },
})

const emit = defineEmits(['select-cate', 'update:filter', 'search'])
</script>

<template>
  <CRow v-if="$route.name === '문서'" class="mb-4 pr-2 mr-2">
    <CCol>
      <h6 class="text-subtitle-1 mb-2">프로젝트 선택</h6>
      <v-divider class="mt-0" />
      <AllProjectsSelect
        :model-value="filter.issue_project"
        @update:model-value="emit('update:filter', { ...filter, issue_project: $event })"
        :all-projects="myProjects"
      />
    </CCol>
  </CRow>

  <CRow class="mb-4 pr-2 mr-2">
    <CCol>
      <h6 class="text-subtitle-1 mb-2">문서 카테고리</h6>
      <v-divider class="mt-0" />
      <v-list density="compact" nav class="pa-0 aside-menu card-white">
        <v-list-item
          :active="filter.category === '' || filter.category === 0"
          @click="emit('select-cate', 0)"
          rounded="lg"
        >
          <template v-slot:prepend>
            <v-icon icon="mdi-folder-outline" size="small" />
          </template>
          <v-list-item-title>전체 문서</v-list-item-title>
        </v-list-item>

        <v-list-item
          v-for="cate in categoryList"
          :key="cate.pk as number"
          :active="filter.category === cate.pk"
          @click="emit('select-cate', cate.pk as number)"
          rounded="lg"
        >
          <template v-slot:prepend>
            <v-icon
              icon="mdi-folder-text-outline"
              size="small"
              :color="cate.color ?? 'secondary'"
            />
          </template>
          <v-list-item-title>{{ cate.name }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </CCol>
  </CRow>

  <CRow>
    <CCol class="mt-4">
      <h6 class="text-subtitle-1 mb-2">{{ typeNumber === 1 ? '키워드' : '관련 사건' }}</h6>
      <v-divider class="mt-0" />
    </CCol>
  </CRow>

  <template v-if="typeNumber === 2">
    <CRow v-if="suitCaseOptions.length" class="mb-3 mr-2">
      <CCol>
        <MultiSelect
          mode="single"
          :model-value="filter.lawsuit"
          @update:model-value="emit('update:filter', { ...filter, lawsuit: $event })"
          :options="suitCaseOptions"
          placeholder="관련 사건 목록"
        />
      </CCol>
    </CRow>
  </template>

  <CRow class="mb-3 mr-2">
    <CCol>
      <div class="input-group mb-3">
        <CFormInput
          :model-value="filter.search"
          @update:model-value="emit('update:filter', { ...filter, search: $event })"
          placeholder="검색어 입력"
          @keydown.enter="emit('search')"
        />
        <button
          class="btn btn-outline-secondary"
          type="button"
          @click="emit('search', { ...filter, search: filter.search })"
        >
          <v-btn icon="mdi-magnify" size="sm" color="light" flat />
          검색
        </button>
      </div>
    </CCol>
  </CRow>
</template>
