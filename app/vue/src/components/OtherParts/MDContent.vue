<script lang="ts" setup>
import { markdownRender } from '@/utils/helper.ts'

defineProps({ content: { type: String, default: '' } })
</script>

<template>
  <div v-html="markdownRender(content)" class="post-content" />
</template>

<style lang="scss" scoped>
.post-content {
  min-height: 200px;
  line-height: 1.6;
}
</style>
