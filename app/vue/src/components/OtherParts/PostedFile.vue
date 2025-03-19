<script lang="ts" setup>
defineProps({ file: { type: Object, required: true } })
</script>

<template>
  <td>
    <v-icon icon="mdi-paperclip" size="sm" class="mr-2" />
    <router-link to="#">a.html</router-link>
    <span>(151 KB)</span>
    <v-icon icon="mdi-download" class="ml-1 pointer" color="secondary" />
  </td>
  <td class="px-2">test file</td>
  <td class="text-secondary">
    <span>austin kho, 2025/03/19 13:33</span>
    <v-icon icon="mdi-trash-can" class="ml-1 pointer" color="secondary" size="sm" />
  </td>
</template>
