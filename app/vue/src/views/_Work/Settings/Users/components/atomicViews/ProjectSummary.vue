<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { IssueProject } from '@/store/types/work_project'
import { useRoute } from 'vue-router'
import { dateFormat } from '@/utils/baseMixins'

const props = defineProps({
  projectResults: { type: Array as PropType<IssueProject[]>, default: () => [] },
})

const route = useRoute()
const userId = computed(() => Number(route.params.userId))

interface FlatProjectRow {
  proj: IssueProject
  level: number
}

const flattenedProjects = computed<FlatProjectRow[]>(() => {
  const rows: FlatProjectRow[] = []
  const visited = new Set<number>()
  const walk = (nodes: IssueProject[], level: number) => {
    for (const node of nodes) {
      if (node.pk && visited.has(node.pk)) continue
      if (node.pk) visited.add(node.pk)
      rows.push({ proj: node, level })
      if (node.sub_projects?.length) {
        walk(node.sub_projects, level + 1)
      }
    }
  }
  walk(props.projectResults, 0)
  return rows
})

const getMemberInfo = (members: any[]) => {
  const member = members.find(m => Number(m.user?.pk) === userId.value)
  return {
    roleNames: member?.roles?.map((r: any) => r.name).join(', ') || '-',
    created: member?.created ? dateFormat(member.created, '/') : '-',
  }
}

const statusBadge = (status?: string) => {
  if (status === '9') return '[잠금보관]'
  if (status && status !== '1') return '[닫힘]'
  return ''
}
</script>

<template>
  <CRow class="mb-3">
    <CCol>
      <v-divider class="mb-0" />
      <CTable small striped hover responsive>
        <CTableHead class="text-center">
          <CTableRow>
            <CTableHeaderCell>워크스페이스</CTableHeaderCell>
            <CTableHeaderCell>역할</CTableHeaderCell>
            <CTableHeaderCell class="text-center">등록시각</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="{ proj, level } in flattenedProjects" :key="proj.pk">
            <CTableDataCell class="text-start">
              <span :style="{ paddingLeft: `${level * 16}px` }">
                <v-icon
                  v-if="level > 0"
                  icon="mdi-chevron-right"
                  color="secondary"
                  size="small"
                  class="me-1"
                />
                <router-link
                  v-if="proj.status !== '9'"
                  :to="{ name: '(개요)', params: { projId: proj.slug } }"
                  :class="{ 'text-muted': proj.status !== '1' }"
                >
                  {{ proj.name }}
                </router-link>
                <span v-else class="text-muted">{{ proj.name }}</span>
                <span v-if="statusBadge(proj.status)" class="text-caption text-grey ms-2">
                  {{ statusBadge(proj.status) }}
                </span>
              </span>
            </CTableDataCell>
            <CTableDataCell>
              {{ getMemberInfo(proj.all_members ?? []).roleNames }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              {{ getMemberInfo(proj.all_members ?? []).created }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
