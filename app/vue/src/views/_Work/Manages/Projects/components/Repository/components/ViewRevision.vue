<script lang="ts" setup>
import RevisionMenu from './HeaderMenu/RevisionMenu.vue'
import PathTree from './atomics/PathTree.vue'
import { bgLight, btnLight } from '@/utils/cssMixins.ts'

defineProps({ sha: { type: String, required: true } })

const emit = defineEmits(['goto-back'])
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ sha.substring(0, 8) }}</h5>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      Austin Kho 이(가)
      <router-link to="">5일</router-link>
      전에 추가함
    </CCol>

    <CCol>
      <RevisionMenu />
    </CCol>
  </CRow>

  <v-divider />

  <CRow class="pl-5">
    <CCol>
      <ul class="pl-5">
        <li>ID {{ sha }}</li>
        <li>상위 {{ 'ㅁㄴㅇㄹㅁㄴㅇㄹ' }}</li>
        <li>하위 {{ 'ㅁㄴㅇㄹㅁㄴㅇㄹ' }}</li>
      </ul>
    </CCol>
  </CRow>

  <CRow class="mb-5">
    <CCol> commit message</CCol>
  </CRow>

  <CRow class="mb-5">
    <CCol>
      <h6>연결된 업무</h6>
    </CCol>
  </CRow>

  <CNav variant="tabs" class="mb-5">
    <CNavItem>
      <CNavLink active>변경사항들</CNavLink>
    </CNavItem>
    <CNavItem>
      <CNavLink>차이점보기</CNavLink>
    </CNavItem>
  </CNav>

  <PathTree />

  <v-btn @click="emit('goto-back')" :color="btnLight" size="small" class="my-5">목록으로</v-btn>
</template>
