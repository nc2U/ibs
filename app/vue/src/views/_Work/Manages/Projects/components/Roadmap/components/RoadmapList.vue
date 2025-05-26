<script lang="ts" setup>
import { onBeforeMount, type PropType } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Version } from '@/store/types/work_project.ts'
import Roadmap from './Roadmap.vue'

defineProps({ versionList: { type: Array as PropType<Version[]>, default: () => [] } })

const [route, router] = [useRoute(), useRouter()]
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>로드맵</h5>
    </CCol>

    <CCol class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link :to="{ name: '(로드맵) - 추가' }" class="ml-1"> 새 버전 </router-link>
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
              @click="router.push({ name: '(설정)', query: { menu: '버전' } })"
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

  <Roadmap v-for="ver in versionList" :key="ver.pk" :version="ver" />
</template>
