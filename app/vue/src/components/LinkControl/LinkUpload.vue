<script lang="ts" setup>
import { computed, ref } from 'vue'
import type { Link } from '@/store/types/docs.ts'

const emit = defineEmits(['enable-store', 'link-upload'])

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const newLinkNum = ref(1)
const newLinkRange = computed(() => range(0, newLinkNum.value))
const newLinks = ref<Array<Link | null>>([null])

const ctlLinkNum = (n: number) => {
  if (n + 1 >= newLinkNum.value) {
    // 링크 필드 추가
    newLinkNum.value++
    newLinks.value.push(null)
  } else {
    // 마지막 전 요소 삭제 시, 마지막 것도 비움
    if (n === newLinks.value.length - 2) newLinks.value[n + 1] = null

    newLinks.value.splice(n, 1)
    newLinkNum.value--
  }
}

const getNewLinks = () => {
  const links = newLinks.value.filter(l => l !== null)
  emit('link-upload', [...links])
}

defineExpose({ getNewLinks })
</script>

<template>
  <CRow class="mb-2">
    <CCol>
      <CInputGroup v-for="lNum in newLinkRange" :key="`ln-${lNum}`" class="mb-2">
        <CFormInput
          :id="`link-${lNum}`"
          v-model="newLinks[lNum]"
          placeholder="파일 링크"
          @input="emit('enable-store', $event)"
        />
        <CInputGroupText id="basic-addon1" @click="ctlLinkNum(lNum)">
          <v-icon
            :icon="`mdi-${lNum + 1 < newLinkNum ? 'minus' : 'plus'}-thick`"
            :color="lNum + 1 < newLinkNum ? 'error' : 'primary'"
          />
        </CInputGroupText>
      </CInputGroup>
    </CCol>
  </CRow>
</template>
