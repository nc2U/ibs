<script lang="ts" setup>
defineProps({
  name: { type: String, default: '새 아이템' },
  to: { type: Object, default: undefined },
  icon: { type: String, default: 'mdi-plus-circle' },
  color: { type: String, default: 'primary' },
  iconColor: { type: String, default: 'success' },
})
</script>

<template>
  <v-btn
    :to="to"
    :prepend-icon="icon"
    :color="color"
    variant="text"
    size="small"
    style="text-decoration: none"
  >
    <template v-slot:prepend>
      <v-icon :color="iconColor"></v-icon>
    </template>
    {{ name }}
  </v-btn>
</template>
