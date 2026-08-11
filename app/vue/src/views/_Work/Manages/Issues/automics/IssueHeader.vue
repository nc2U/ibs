<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  projStatus: { type: String, default: '' },
})

const accStore = useAccount()
const workManager = computed(() => accStore.workManager)

const workStore = useWork()
const myProjects = computed(() => workStore.getMyProjects.filter(pjt => pjt.module?.issue))

const { can, PERM } = usePerms()
const canIssueCreate = computed(() => props.projStatus !== '9' && can(PERM.ISSUE_CREATE))

const route = useRoute()
const router = useRouter()
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <v-icon
          icon="mdi-clipboard-check"
          :color="route.name === '업무' ? 'primary' : 'green-darken-1'"
          size="small"
          class="mr-2"
        />
        업무
      </h5>
    </CCol>
    <CCol v-if="['업무', '(업무)'].includes(route.name as string)" class="text-right">
      <span v-if="canIssueCreate" class="mr-2 form-text">
        <TextButton
          v-if="route.name === '업무'"
          name="새 업무"
          :project-list="myProjects"
          :project-to="{ name: '(업무) - 추가' }"
        />
        <TextButton v-else name="새 업무" :to="{ name: `${String(route.name)} - 추가` }" />
      </span>

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
            <CDropdownItem
              v-if="route.params.projId"
              class="form-text"
              @click="router.push({ name: '(업무) - 보고서' })"
            >
              <router-link to="">
                <v-icon icon="mdi-chart-bar" color="amber" size="sm" class="mr-1" />요약
              </router-link>
            </CDropdownItem>
            <CDropdownItem v-if="projStatus !== '9'" class="form-text" disabled>
              <!--              <router-link to="">-->
              <v-icon
                icon="mdi-file-document-arrow-right"
                color="blue-lighten"
                size="sm"
                class="mr-1"
              />가져오기
              <!--              </router-link>-->
            </CDropdownItem>
            <CDropdownItem
              v-if="projStatus !== '9' && route.params.projId && workManager"
              class="form-text"
              @click="router.push({ name: '(설정)', query: { menu: '업무추적' } })"
            >
              <router-link to="">
                <v-icon icon="mdi-cog" color="secondary" size="sm" class="mr-1" />설정
              </router-link>
            </CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </span>
    </CCol>
  </CRow>
</template>
