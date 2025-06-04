<script lang="ts" setup>
import router from '@/router/index.js'
</script>

<template>
  <CCol class="row row-cols-lg-auto g-3 align-items-center">
    <CCol class="ms-auto d-flex align-items-center gap-2">
      <CCol col="3">
        <span class="pointer">
          <v-icon icon="mdi-chart-bar" color="blue" size="sm" class="mr-2" />
          <router-link to="">통계</router-link>
        </span>
        <CDropdown color="secondary" variant="input-group" placement="bottom-end">
          <CDropdownToggle
            :caret="false"
            color="light"
            variant="ghost"
            size="sm"
            shape="rounded-pill"
          >
            <v-icon icon="mdi-dots-horizontal" class="pointer" color="grey-darken-1" />
            <v-tooltip activator="parent" location="top">Actions</v-tooltip>
          </CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem @click="router.push({ name: '(설정)', query: { menu: '저장소' } })">
              <v-icon icon="mdi mdi-cog" size="sm" class="mr-2" />
              <router-link to="#">설정</router-link>
            </CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </CCol>
      <CFormLabel> | 브랜치(Branch):</CFormLabel>
      <CFormSelect style="width: 100px" size="sm">
        <option value="">---------</option>
        <option value="1">master</option>
        <option value="2">develop</option>
        <option value="3">gh-pages</option>
      </CFormSelect>

      <CFormLabel> | 태그(Tag):</CFormLabel>
      <CFormSelect style="width: 100px" size="sm">
        <option value="">---------</option>
        <option value="1">v0.8</option>
      </CFormSelect>

      <CFormLabel> | 리비전:</CFormLabel>
      <CFormInput style="width: 100px" size="sm" placeholder="sha" />
    </CCol>
  </CCol>
</template>
