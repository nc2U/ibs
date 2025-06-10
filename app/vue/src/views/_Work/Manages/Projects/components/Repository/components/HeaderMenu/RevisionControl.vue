<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'

const props = defineProps({ commitHash: { type: String, default: null } })

const emit = defineEmits(['get-commit'])

const sha = ref('')

onBeforeMount(() => {
  if (props.commitHash) sha.value = props.commitHash
})
</script>

<template>
  <CCol class="row row-cols-lg-auto g-3 align-items-center mb-3">
    <CCol class="ms-auto d-flex flex-wrap align-items-center gap-2 col-12">
      <CFormLabel> << 뒤로</CFormLabel>
      |

      <CFormLabel> 다음 >></CFormLabel>
      <CFormInput v-model="sha" style="width: 100px" size="sm" placeholder="sha" />
      <CButton color="secondary" @click="emit('get-commit', sha)" variant="outline" size="sm">
        보기
      </CButton>
    </CCol>
  </CCol>
</template>
