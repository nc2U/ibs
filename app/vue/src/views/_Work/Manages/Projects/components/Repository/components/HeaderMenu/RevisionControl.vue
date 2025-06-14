<script lang="ts" setup>
import { onBeforeMount, type PropType, ref, watch } from 'vue'
import type { Commit } from '@/store/types/work_git_repo.ts'

const props = defineProps({ commit: { type: Object as PropType<Commit>, required: true } })

const emit = defineEmits(['get-commit'])

const sha = ref('')

watch(
  () => props.commit,
  nVal => {
    if (nVal) sha.value = nVal.commit_hash
  },
)

onBeforeMount(() => {
  if (props.commit) sha.value = props.commit.commit_hash
})
</script>

<template>
  <CCol class="row row-cols-lg-auto g-3 align-items-center mb-3">
    <CCol class="ms-auto d-flex flex-wrap align-items-center gap-2 col-12">
      «
      <span v-if="!commit.prev">뒤로</span>
      <span v-else>
        <router-link to="" @click="emit('get-commit', commit.prev)">뒤로</router-link>
      </span>
      |
      <span v-if="!commit.next">다음</span>
      <span v-else>
        <router-link to="" @click="emit('get-commit', commit.next)">다음</router-link>
      </span>
      »
      <CFormInput v-model="sha" style="width: 100px" size="sm" placeholder="sha" />
      <CButton color="secondary" @click="emit('get-commit', sha)" variant="outline" size="sm">
        보기
      </CButton>
    </CCol>
  </CCol>
</template>
