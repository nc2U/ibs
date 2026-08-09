<script lang="ts" setup>
import { ref, type PropType } from 'vue'
import type { SimpleIssue } from '@/store/types/work_issue.ts'
import IssueDropDown from '@/views/_Work/Manages/Issues/components/IssueDropDown.vue'

const props = defineProps({
  issues: {
    type: Array as PropType<SimpleIssue[] | any[]>,
    default: () => [],
  },
})

const selectedRow = ref<number | null>(null)
</script>

<template>
  <div>
    <h6>연결된 업무</h6>
    <v-divider class="mb-0" />
    <CTable responsive hover small striped>
      <colgroup>
        <col style="width: 95%" />
        <col style="width: 5%" />
      </colgroup>
      <CTableBody>
        <CTableRow
          v-for="issue in props.issues"
          :key="issue.pk"
          class="table-row cursor-menu"
          :color="selectedRow === issue.pk ? 'primary' : ''"
          @click="selectedRow = issue.pk"
        >
          <CTableDataCell>
            <span>
              <router-link
                :to="{ name: '(업무) - 보기', params: { issueId: issue.pk } }"
                :class="{ closed: issue.closed }"
              >
                {{ issue.tracker?.name || '업무' }} #{{ issue.pk }}
              </router-link>
            </span>
            <span> : {{ issue.subject }}</span>
          </CTableDataCell>
          <CTableDataCell class="text-center p-0">
            <IssueDropDown :issue="issue" />
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>
  </div>
</template>
