<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { usePerms } from '@/composables/usePerms.ts'

defineProps({
  projectMembers: {
    type: Object as PropType<{ [key: string]: { pk: number; username: string }[] }>,
    default: () => null,
  },
})

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const { canViewUser } = usePerms()
</script>

<template>
  <CCard :color="isDark ? '' : 'light'" class="mb-3">
    <CCardBody>
      <CCardSubtitle class="mb-2">
        <v-icon icon="mdi-account-multiple-check" size="sm" class="mr-1" />
        구성원
      </CCardSubtitle>
      <CCardText>
        <div v-for="(val, key) in projectMembers" :key="key">
          {{ key }} :

          <span v-for="(u, i) in val" :key="u.pk">
            <router-link
              v-if="canViewUser(u.pk)"
              :to="{ name: '사용자 - 보기', params: { userId: u.pk } }"
            >
              {{ u.username }}
            </router-link>
            <span v-else>{{ u.username }}</span>
            <span v-if="Number(i) + 1 < val.length">, </span>
          </span>
        </div>
      </CCardText>
    </CCardBody>
  </CCard>
</template>
