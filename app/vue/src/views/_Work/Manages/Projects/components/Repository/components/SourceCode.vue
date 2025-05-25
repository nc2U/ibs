<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { elapsedTime, humanizeFileSize } from '@/utils/baseMixins.ts'
import type { GitData, Tree } from '@/store/types/work_github.ts'

const props = defineProps({
  branches: { type: Array as PropType<GitData[]>, default: () => [] },
  tags: { type: Array as PropType<GitData[]>, default: () => [] },
  defaultBranch: { type: String, default: 'master' },
  masterTree: { type: Array as PropType<Tree[]>, default: () => [] },
})

const branchFold = ref(false)
const tagFold = ref(false)
const masterFold = ref(false)

const getLatestBranch = (branches: GitData[]) => {
  if (branches.length === 0) return
  return branches.reduce((last, curr) => {
    const lastDate = new Date(last.commit.date)
    const currDate = new Date(curr.commit.date)
    return lastDate > currDate ? last : curr
  })
}

const last_branch = computed(() => getLatestBranch(props.branches))
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <span><router-link to="">Git 저장소</router-link></span>
        <!--        <span v-if="1 == 2">/ <router-link to="">branches</router-link></span>-->
        <!--        <span v-if="1 == 2">/ <router-link to="">aaa</router-link></span>-->
      </h5>
    </CCol>
  </CRow>
  <CRow class="mb-5">
    <CCol>
      <CTable hover striped small responsive>
        <colgroup>
          <col style="width: 25%" />
          <col style="width: 8%" />
          <col style="width: 10%" />
          <col style="width: 8%" />
          <col style="width: 14%" />
          <col style="width: 35%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>이름</CTableHeaderCell>
            <CTableHeaderCell>크기</CTableHeaderCell>
            <CTableHeaderCell>리비전</CTableHeaderCell>
            <CTableHeaderCell>마지막 수정일</CTableHeaderCell>
            <CTableHeaderCell>저자</CTableHeaderCell>
            <CTableHeaderCell>설명</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow>
            <CTableDataCell>
              <v-icon
                :icon="`mdi-chevron-${branchFold ? 'down' : 'right'}`"
                size="16"
                class="pointer mr-1"
                @click="branchFold = !branchFold"
              />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">branches</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to="">{{ last_branch?.commit.sha }}</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right">
              {{ elapsedTime(last_branch?.commit.date ?? 20000) }}
            </CTableDataCell>
            <CTableDataCell class="text-center">{{ last_branch?.commit.author }}</CTableDataCell>
            <CTableDataCell>{{ last_branch?.commit.message }}</CTableDataCell>
          </CTableRow>
          <CTableRow v-if="branchFold" v-for="branch in branches as any[]" :key="branch">
            <CTableDataCell class="pl-5">
              <v-icon icon="mdi-chevron-right" size="16" class="pointer mr-1" />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">{{ branch.name }}</router-link>
            </CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to="">{{ branch.commit.sha }}</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right">
              {{ elapsedTime(branch.commit.date) }}
            </CTableDataCell>
            <CTableDataCell class="text-center">{{ branch.commit.author }}</CTableDataCell>
            <CTableDataCell>{{ branch.commit.message }}</CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableDataCell>
              <v-icon
                :icon="`mdi-chevron-${tagFold ? 'down' : 'right'}`"
                size="16"
                class="pointer mr-1"
                @click="tagFold = !tagFold"
              />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">tags</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to=""></router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center"></CTableDataCell>
            <CTableDataCell></CTableDataCell>
          </CTableRow>
          <CTableRow v-if="tagFold" v-for="(tag, i) in tags" :key="i">
            <CTableDataCell class="pl-5">
              <v-icon icon="mdi-chevron-right" size="16" class="pointer mr-1" />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">{{ tag.name }}</router-link>
            </CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableDataCell>
              <v-icon
                :icon="`mdi-chevron-${masterFold ? 'down' : 'right'}`"
                size="16"
                class="pointer mr-1"
                @click="masterFold = !masterFold"
              />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">{{ defaultBranch }}</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to=""></router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center"></CTableDataCell>
            <CTableDataCell></CTableDataCell>
          </CTableRow>
          <CTableRow v-if="masterFold" v-for="tree in masterTree" :key="tree.sha">
            <CTableDataCell class="pl-5">
              <span v-if="tree.type === 'tree'">
                <v-icon icon="mdi-chevron-right" size="16" class="pointer mr-1" />
                <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              </span>
              <span v-if="tree.type === 'blob'" class="pl-5">
                <v-icon
                  :icon="`mdi-file-${tree.path.endsWith('.txt') ? 'document-' : ''}outline`"
                  color="secondary"
                  size="16"
                  class="pointer mr-1 mdi-thin"
                />
              </span>
              <router-link to="">{{ tree.path }}</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right">
              {{ humanizeFileSize((tree as any)?.size) }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to="">10232</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right">1달 전</CTableDataCell>
            <CTableDataCell class="text-center">Austin Kho</CTableDataCell>
            <CTableDataCell>#127 asdfasdf adsf</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
