<script lang="ts" setup>
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings'
import type { Docs } from '@/store/types/docs'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import DocsList from './components/DocsList.vue'
import Loading from '@/components/Loading/Index.vue'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const route = useRoute()

const { can, PERM } = usePerms()

const workStore = useWork()
const allProjects = computed(() => workStore.getAllProjects)

const docStore = useDocs()
const docsList = computed<Docs[]>(() => docStore.docsList)
const categoryList = computed(() => docStore.categoryList)

const typeNumber = ref<1 | 2>(1)
const types = ref([
  { value: 1, label: '일반문서' },
  { value: 2, label: '소송기록' },
])

const docsFilter = ref<DocsFilter>({
  doc_type: typeNumber.value,
  category: '',
  issue_project: '',
  ordering: '-is_pinned,-created',
  search: '',
  page: 1,
  limit: '',
})

provide('navMenu', navMenu)
provide('query', route?.query)

const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)
const fetchCategoryList = (type: number) => docStore.fetchCategoryList(type)

const getDocsList = (target: unknown) => {
  if (target === 1 || target === 2) {
    docsFilter.value.page = 1
    docsFilter.value.doc_type = target as number
    fetchCategoryList(target as 1 | 2)
    fetchDocsList(docsFilter.value)
  }
}

const selectCate = (cate: number) => {
  docsFilter.value.page = 1
  docsFilter.value.category = cate
  fetchDocsList(docsFilter.value)
}

const pageSelect = (page: number) => {
  docsFilter.value.page = page
  fetchDocsList(docsFilter.value)
}

const loading = ref<boolean>(true)
const initData = async () => {
  loading.value = true
  await workStore.fetchAllProjectList()
  await fetchCategoryList(typeNumber.value)
  await fetchDocsList(docsFilter.value)
  loading.value = false
}

onBeforeMount(initData)

watch(
  () => route.name,
  newName => {
    if (newName === '문서') {
      initData()
    }
  },
)
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-text-box-search-outline" color="primary" class="mr-2" />
            문서
          </h5>
        </CCol>
      </CRow>

      <template v-if="can(PERM.DOCS_READ)">
        <CRow class="mb-3 header">
          <CCol>
            <v-tabs v-model="typeNumber" density="compact" @update:model-value="getDocsList">
              <v-tab
                v-for="type in types"
                :value="type.value"
                :key="type.value"
                variant="tonal"
                :active="typeNumber === type.value"
              >
                {{ type.label }}
              </v-tab>
            </v-tabs>
          </CCol>
        </CRow>

        <DocsList
          :category="docsFilter.category as number"
          :category-list="categoryList"
          :docs-list="docsList"
          @select-cate="selectCate"
          @page-select="pageSelect"
        />
      </template>

      <v-alert v-else color="warning" class="mt-4" variant="tonal">
        <v-icon icon="mdi-alert-circle" class="mr-2" />
        문서를 조회할 수 있는 권한이 없습니다.
      </v-alert>
    </template>

    <template v-slot:aside>
      <CRow class="mb-4 pr-2 mr-2">
        <CCol>
          <h6 class="asideTitle">프로젝트 선택</h6>
          <v-divider class="mt-0" />
          <CFormSelect
            v-model="docsFilter.issue_project"
            size="sm"
            @change="fetchDocsList(docsFilter)"
          >
            <option value="">전체 프로젝트</option>
            <option v-for="proj in allProjects" :key="proj.pk" :value="proj.pk">
              {{ proj.label }}
            </option>
          </CFormSelect>
        </CCol>
      </CRow>

      <CRow class="mb-4 pr-2 mr-2">
        <CCol>
          <h6 class="asideTitle">문서 카테고리</h6>
          <v-divider class="mt-0" />
          <v-list density="compact" nav class="pa-0 aside-menu card-white">
            <v-list-item
              :active="docsFilter.category === '' || docsFilter.category === 0"
              @click="selectCate(0)"
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
              :active="docsFilter.category === cate.pk"
              @click="selectCate(cate.pk as number)"
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

      <CRow class="mb-3 mr-2">
        <CCol>
          <CFormInput
            v-model="docsFilter.search"
            placeholder="검색어"
            @keydown.enter="fetchDocsList(docsFilter)"
          />
        </CCol>
      </CRow>

      <CRow class="mr-2">
        <CCol class="text-right">
          <v-btn size="small" color="info" @click="fetchDocsList(docsFilter)">검색</v-btn>
        </CCol>
      </CRow>
    </template>
  </ContentBody>
</template>
