<script lang="ts" setup>
import type { Link } from '@/store/types/docs.ts'
import { AlertSecondary } from '@/utils/cssMixins.ts'

defineProps({ links: { type: Array, default: () => [] } })

const enableStore = () => 1
</script>

<template>
  <CRow>
    <CAlert :color="AlertSecondary">
      <CCol>
        <CInputGroup v-for="(link, i) in links as Link[]" :key="link.pk" class="mb-2">
          <CFormInput
            :id="`docs-link-${link.pk}`"
            v-model="(links as Link[])[i].link"
            size="sm"
            placeholder="파일 링크"
            @input="enableStore"
          />
          <CInputGroupText id="basic-addon1" class="py-0">
            <CFormCheck
              :id="`del-link-${link.pk}`"
              v-model="(links as Link[])[i].del"
              @input="enableStore"
              label="삭제"
            />
          </CInputGroupText>
        </CInputGroup>
      </CCol>
    </CAlert>
  </CRow>
</template>
