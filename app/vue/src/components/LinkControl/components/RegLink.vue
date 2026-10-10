<script lang="ts" setup>
import { ref, watch } from 'vue'
import type { Link } from '@/store/types/docs.ts'

interface Props {
  link: Link
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'enable-store', event: Event): void
  (e: 'link-change', payload: { pk: number; link: string }): void
  (e: 'link-delete', payload: { pk: number; del: boolean }): void
}>()

const linkData = ref<Link>({
  ...props.link,
  del: props.link.del ?? false,
})

watch(
  () => props.link,
  newLink => {
    if (newLink) {
      linkData.value = {
        ...newLink,
        del: newLink.del ?? false,
      }
    }
  },
  { deep: true },
)

const linkChange = (event: Event, pk?: null | number) => {
  if (typeof pk === 'number') {
    const el = event.target as HTMLInputElement
    emit('link-change', { pk, link: el.value })
    emit('enable-store', event)
  }
}

const handleDeleteChange = () => {
  if (typeof props.link.pk === 'number') {
    emit('link-delete', { pk: props.link.pk, del: linkData.value.del ?? false })
  }
}
</script>

<template>
  <CFormInput
    v-model="linkData.link"
    :id="`docs-link-${link.pk}`"
    size="sm"
    placeholder="파일 링크"
    @input="linkChange($event, link.pk)"
  />

  <CInputGroupText id="basic-addon1" class="py-0">
    <CFormCheck
      v-model="linkData.del"
      :id="`del-link-${link.pk}`"
      label="삭제"
      @change="handleDeleteChange"
    />
  </CInputGroupText>
</template>
