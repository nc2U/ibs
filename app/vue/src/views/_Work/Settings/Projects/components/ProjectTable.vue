<script lang="ts" setup>
import type { PropType } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'

defineProps({
  allProjectList: { type: Array as PropType<IssueProject[]>, default: () => [] },
})
</script>

<template>
  <v-divider class="mb-0" />
  <CTable hover small striped responsive>
    <CTableHead>
      <CTableRow color="">
        <CTableHeaderCell>
          <CFormCheck />
        </CTableHeaderCell>
        <CTableHeaderCell>이름</CTableHeaderCell>
        <CTableHeaderCell>식별자</CTableHeaderCell>
        <CTableHeaderCell>설명</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="iproj in allProjectList" :key="iproj.pk">
        <CTableDataCell>
          <CFormCheck />
        </CTableDataCell>
        <CTableDataCell :class="'pl-' + iproj.depth">
          <v-icon v-if="iproj.parent" color="secondary" icon="mdi-chevron-right" />
          <router-link :to="{ name: '(개요)', params: { projId: iproj.slug } }">
            {{ iproj.name }}
          </router-link>
        </CTableDataCell>
        <CTableDataCell>{{ iproj.slug }}</CTableDataCell>
        <CTableDataCell>{{ iproj.description }}</CTableDataCell>
        <CTableDataCell class="text-right">
          <span>
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
                <CDropdownItem>
                  <router-link to="">
                    <v-icon icon="mdi-lock" color="yellow-darken-2" size="sm" />
                    잠금보관
                  </router-link>
                </CDropdownItem>
                <CDropdownItem>
                  <router-link to="">
                    <v-icon icon="mdi-content-copy" color="grey" size="sm" />
                    복사
                  </router-link>
                </CDropdownItem>
                <CDropdownItem>
                  <router-link to="">
                    <v-icon icon="mdi-trash-can-outline" color="grey" size="sm" />
                    삭제
                  </router-link>
                </CDropdownItem>
              </CDropdownMenu>
            </CDropdown>
          </span>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
