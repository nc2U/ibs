<script lang="ts" setup>
import { type PropType } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { Version } from '@/store/types/work_project.ts'
import RoadmapItem from './RoadmapItem.vue'
import TopButton from '../../../../../components/atomics/TopButton.vue'

defineProps({ versionList: { type: Array as PropType<Version[]>, default: () => [] } })

const { can, PERM } = usePerms()
const [route, router] = [useRoute(), useRouter()]
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>로드맵</h5>
    </CCol>

    <CCol class="text-right">
      <span v-if="can(PERM.PROJECT_VERSION)" class="mr-2 form-text">
        <TopButton name="새 단계" :to="{ name: '(로드맵) - 추가' }" />
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
              @click="router.push({ name: '(설정)', query: { menu: '단계' } })"
            >
              <router-link to="">
                <v-icon icon="mdi-cog" color="grey" size="sm" class="mr-2" />
                설정
              </router-link>
            </CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </span>
    </CCol>
  </CRow>

  <RoadmapItem v-for="ver in versionList" :key="ver.pk" :version="ver" />
</template>
