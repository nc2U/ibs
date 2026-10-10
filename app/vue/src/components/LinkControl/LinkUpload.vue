<script lang="ts" setup>
import { ref } from 'vue'
import type { Link } from '@/store/types/docs.ts'

interface LinkItem {
  id: number
  link: string
}

const emit = defineEmits<{
  (e: 'enable-store', event: Event): void
  (e: 'link-upload', links: Link[]): void
}>()

let nextId = 1
const newLinks = ref<LinkItem[]>([{ id: nextId++, link: '' }])

const addLinkField = () => {
  newLinks.value.push({ id: nextId++, link: '' })
}

const removeLinkField = (index: number) => {
  newLinks.value.splice(index, 1)
  if (newLinks.value.length === 0) {
    newLinks.value.push({ id: nextId++, link: '' })
  }
}

const getNewLinks = () => {
  const links: Link[] = newLinks.value
    .filter(l => !!l.link.trim())
    .map(l => ({
      docs: null,
      link: l.link.trim(),
      description: '',
    }))
  emit('link-upload', links)
}

defineExpose({ getNewLinks })
</script>

<template>
  <CRow class="mb-2">
    <CCol>
      <CInputGroup v-for="(item, index) in newLinks" :key="item.id" class="mb-2">
        <CFormInput
          :id="`link-${item.id}`"
          v-model="item.link"
          placeholder="파일 링크"
          @input="emit('enable-store', $event)"
        />
        <CInputGroupText
          id="basic-addon1"
          role="button"
          style="cursor: pointer"
          @click="index + 1 === newLinks.length ? addLinkField() : removeLinkField(index)"
        >
          <v-icon
            :icon="`mdi-${index + 1 === newLinks.length ? 'plus' : 'minus'}-thick`"
            :color="index + 1 === newLinks.length ? 'primary' : 'error'"
          />
        </CInputGroupText>
      </CInputGroup>
    </CCol>
  </CRow>
</template>
