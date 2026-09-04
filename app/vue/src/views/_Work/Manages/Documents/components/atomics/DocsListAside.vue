<script lang="ts" setup>
import type { PropType } from 'vue'
import type { Category } from '@/store/types/docs.ts'
import type { SuitCaseFilter } from '@/store/pinia/docs'
import type { selectProject } from '@/store/types/work_project.ts'
import { courtChoices } from '@/components/LawSuitCase/components/court'
import MultiSelect from '@/components/MultiSelect/index.vue'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'

const props = defineProps({
  myProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  categoryList: { type: Array as PropType<Category[]>, default: () => [] },
  filter: { type: Object, required: true },
  caseFilter: { type: Object as PropType<SuitCaseFilter>, default: () => ({}) },
  typeNumber: { type: Number, default: 1 },
  suitCaseOptions: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'select-cate',
  'update:filter',
  'search',
  'update:caseFilter',
  'case-search',
  'case-reset',
])
</script>

<template>
  <CRow v-if="$route.name === '문서'" class="mb-4 pr-2 mr-2">
    <CCol>
      <h6 class="text-subtitle-1 mb-2">워크스페이스 선택</h6>
      <v-divider class="mt-0" />
      <IssueProjectSelector
        :model-value="filter.issue_project"
        @update:model-value="emit('update:filter', { ...filter, issue_project: $event })"
        :issue-project-list="myProjects"
      />
    </CCol>
  </CRow>

  <!-- Type 1 & 2: 문서 카테고리 및 관련사건/검색 필터 -->
  <template v-if="typeNumber === 1 || typeNumber === 2">
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
            placeholder="문서 내 검색"
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

  <!-- Type 3: 소송사건 전용 필터 -->
  <template v-else-if="typeNumber === 3">
    <!-- 사건 유형 -->
    <CRow class="mb-3 pr-2 mr-2">
      <CCol>
        <h6 class="text-subtitle-1 mb-2">사건 유형</h6>
        <v-divider class="mt-0" />
        <CFormSelect
          :value="caseFilter.sort ?? ''"
          size="sm"
          @change="emit('update:caseFilter', { ...caseFilter, sort: ($event.target as HTMLSelectElement).value, page: 1 })"
        >
          <option value="">전체 유형</option>
          <option value="1">민사</option>
          <option value="2">형사</option>
          <option value="3">행정</option>
          <option value="4">신청</option>
          <option value="5">집행</option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 사건 심급 -->
    <CRow class="mb-3 pr-2 mr-2">
      <CCol>
        <h6 class="text-subtitle-1 mb-2">심급</h6>
        <v-divider class="mt-0" />
        <CFormSelect
          :value="caseFilter.level ?? ''"
          size="sm"
          @change="emit('update:caseFilter', { ...caseFilter, level: ($event.target as HTMLSelectElement).value, page: 1 })"
        >
          <option value="">전체 심급</option>
          <option value="1">1심</option>
          <option value="2">2심</option>
          <option value="3">3심</option>
          <option value="4">고소/수사</option>
          <option value="5">신청</option>
          <option value="6">항고/이의</option>
          <option value="7">압류/추심</option>
          <option value="8">정지/이의</option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 관할 법원 -->
    <CRow class="mb-3 pr-2 mr-2">
      <CCol>
        <h6 class="text-subtitle-1 mb-2">관할 법원</h6>
        <v-divider class="mt-0" />
        <CFormSelect
          :value="caseFilter.court ?? ''"
          size="sm"
          @change="emit('update:caseFilter', { ...caseFilter, court: ($event.target as HTMLSelectElement).value, page: 1 })"
        >
          <option value="">전체 법원</option>
          <option v-for="c in courtChoices" :key="c.value" :value="c.value">
            {{ c.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 진행 상태 -->
    <CRow class="mb-3 pr-2 mr-2">
      <CCol>
        <h6 class="text-subtitle-1 mb-2">진행 상태</h6>
        <v-divider class="mt-0" />
        <CFormSelect
          :value="caseFilter.in_progress === true ? 'true' : caseFilter.in_progress === false ? 'false' : ''"
          size="sm"
          @change="emit('update:caseFilter', {
            ...caseFilter,
            in_progress: ($event.target as HTMLSelectElement).value === 'true' ? true : ($event.target as HTMLSelectElement).value === 'false' ? false : '',
            page: 1
          })"
        >
          <option value="">전체 (진행+종결)</option>
          <option value="true">진행중</option>
          <option value="false">종결</option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 사건 검색 -->
    <CRow class="mb-3 pr-2 mr-2">
      <CCol>
        <h6 class="text-subtitle-1 mb-2">사건 검색</h6>
        <v-divider class="mt-0" />
        <div class="input-group mb-2">
          <CFormInput
            :model-value="caseFilter.search ?? ''"
            size="sm"
            placeholder="사건번호 / 사건명 / 당사자"
            @update:model-value="emit('update:caseFilter', { ...caseFilter, search: $event })"
            @keydown.enter="emit('case-search')"
          />
          <button
            class="btn btn-outline-secondary btn-sm"
            type="button"
            @click="emit('case-search')"
          >
            검색
          </button>
        </div>
        <div class="text-right">
          <v-btn
            size="x-small"
            variant="text"
            color="grey"
            prepend-icon="mdi-refresh"
            @click="emit('case-reset')"
          >
            필터 초기화
          </v-btn>
        </div>
      </CCol>
    </CRow>
  </template>
</template>
