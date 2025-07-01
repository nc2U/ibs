<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, ref, watch } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { colorLight } from '@/utils/cssMixins'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import type { Company } from '@/store/types/settings'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const company = inject<ComputedRef<Company | null>>('company')
const comName = computed(() => company?.value?.name)
const sideNavCAll = () => cBody.value.toggle()

const searchWord = ref('')
const searchCond = ref({
  all: true,
  subOnly: false,
  issue: false,
  news: false,
  document: false,
  changeSet: false,
  wiki: false,
  text: false,
  project: false,

  opened: false,
  attatch: '1' as '1' | '2' | '3',
})

const visible = ref(false)

const [route, router] = [useRoute(), useRouter()]

const goSearch = () => router.replace({ name: '전체검색', query: { q: searchWord.value } })

watch(route, nVal => {
  if (nVal.query.q) searchWord.value = nVal.query.q as string
})

onBeforeMount(() => {
  if (route.query.q) searchWord.value = route.query.q as string
})

onBeforeRouteLeave((to, from, next) => {
  to.query = {}
  next()
})
</script>

<template>
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="false">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>검색</h5>
        </CCol>
      </CRow>

      <CCard :color="colorLight">
        <CCardBody>
          <CRow>
            <CCol sm="12" md="8" lg="6" xl="3">
              <CFormInput v-model="searchWord" @keydown.enter="goSearch" />
            </CCol>
            <CCol class="pt-2">
              <CFormCheck v-model="searchCond.all" inline label="모든 단어" id="all-word" />

              <CFormCheck
                v-model="searchCond.subOnly"
                inline
                label="제목에서만 찾기"
                id="only-subject"
              />
            </CCol>
          </CRow>

          <CRow class="mt-3 m-1">
            <CCard class="mt-3" :color="colorLight">
              <CCardBody>
                <CFormCheck v-model="searchCond.issue" inline label="업무" id="issue-search" />
                <CFormCheck v-model="searchCond.news" inline label="공지" id="news-search" />
                <CFormCheck v-model="searchCond.document" inline label="문서" id="docs-search" />
                <CFormCheck
                  v-model="searchCond.changeSet"
                  inline
                  label="변경묶음"
                  id="cng-search"
                />
                <CFormCheck v-model="searchCond.wiki" inline label="위키 페이지" id="wiki-search" />
                <CFormCheck v-model="searchCond.text" inline label="글" id="text-search" />
                <CFormCheck v-model="searchCond.project" inline label="프로젝트" id="proj-search" />
              </CCardBody>
            </CCard>
          </CRow>

          <CRow class="mt-3">
            <CCol class="pointer mb-0" @click="visible = !visible">
              <v-icon :icon="visible ? 'mdi-chevron-down' : 'mdi-chevron-right'" size="sm" />
              옵션
            </CCol>
            <CCollapse :visible="visible">
              <v-divider class="mx-1" />
              <CRow class="mt-2 pl-1" color="light">
                <CCol>
                  <CFormCheck v-model="searchCond.opened" label="열린 업무만" id="opened-only" />
                </CCol>
              </CRow>

              <CRow class="mt-1 pl-1">
                <CCol>
                  <CFormCheck
                    v-model="searchCond.attatch"
                    value="1"
                    type="radio"
                    inline
                    name="attatch"
                    id="attatch1"
                    label="첨부는 검색하지 않음"
                  />
                  <CFormCheck
                    v-model="searchCond.attatch"
                    value="2"
                    type="radio"
                    inline
                    name="attatch"
                    id="attatch2"
                    label="첨부파일명과 설명만 검색"
                  />
                  <CFormCheck
                    v-model="searchCond.attatch"
                    value="3"
                    type="radio"
                    inline
                    name="attatch"
                    id="attatch3"
                    label="첨부만 검색"
                  />
                </CCol>
              </CRow>
            </CCollapse>
          </CRow>
        </CCardBody>
      </CCard>

      <CRow class="mt-2">
        <CCol>
          <v-btn color="primary" variant="outlined" size="small" @click="goSearch">검색</v-btn>
        </CCol>
      </CRow>

      <CRow v-if="route.query.q">
        <CCol>
          <CRow class="mt-4">
            <CCol>
              <h5>결과 (0)</h5>
            </CCol>
          </CRow>

          <CRow class="mt-2">
            <CCol> 결과들 ... (구현 중)</CCol>
          </CRow>
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
