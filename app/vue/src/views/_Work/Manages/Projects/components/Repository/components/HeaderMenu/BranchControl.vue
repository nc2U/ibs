<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useGithub } from '@/store/pinia/work_github.ts'
import router from '@/router/index.js'

const props = defineProps({
  currBranch: { type: String, required: true },
  branches: { type: Array, default: () => [] },
  tags: { type: Array, default: () => [] },
})

const gitStore = useGithub()
const default_branch = computed(() => gitStore.default_branch)

const emit = defineEmits(['change-revision'])

const branch = ref('')
const tag = ref('')
const sha = ref('')

const changeBranch = (e: Event) => {
  tag.value = ''
  sha.value = ''
  if ((e.target as any).value) emit('change-revision', { branch: (e.target as any).value })
}

const changeTag = (e: Event) => {
  branch.value = ''
  sha.value = ''
  if ((e.target as any).value) emit('change-revision', { tag: (e.target as any).value })
}

const changeCommit = (e: Event) => {
  branch.value = ''
  tag.value = ''
  if ((e.target as any).value) emit('change-revision', { sha: (e.target as any).value })
}

onBeforeMount(() => {
  if (props.currBranch) branch.value = props.currBranch
  else if (default_branch.value) branch.value = default_branch.value
})
</script>

<template>
  <CCol class="row row-cols-lg-auto g-3 align-items-center mb-3">
    <CCol class="ms-auto d-flex flex-wrap align-items-center gap-2 col-12">
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
      <CFormLabel> | 브랜치 :</CFormLabel>
      <CFormSelect v-model="branch" style="width: 100px" size="sm" @change="changeBranch">
        <option value="">---------</option>
        <option v-for="(branch, i) in branches" :key="i">{{ branch }}</option>
      </CFormSelect>
      <CFormLabel> | 태그 :</CFormLabel>
      <CFormSelect v-model="tag" style="width: 100px" size="sm" @change="changeTag">
        <option value="">---------</option>
        <option v-for="(tag, i) in tags" :key="i">{{ tag }}</option>
      </CFormSelect>

      <CFormLabel> | 리비전:</CFormLabel>
      <CFormInput
        v-model="sha"
        style="width: 100px"
        size="sm"
        placeholder="sha"
        @keydown.enter="changeCommit"
      />
    </CCol>
  </CCol>
</template>
