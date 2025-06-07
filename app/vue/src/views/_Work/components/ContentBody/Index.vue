<script lang="ts" setup>
import { computed, inject, provide, ref } from 'vue'
import { useStore } from '@/store'
import { type RouteRecordName, useRoute, useRouter } from 'vue-router'

const props = defineProps({ aside: { type: Boolean, default: true } })

const visible = ref(false)

const query = inject('query') as Record<string, any>
const navMenu = inject('navMenu')

const [route, router] = [useRoute(), useRouter()]

const isDark = computed(() => useStore().theme === 'dark')
const baseColor = computed(() => (isDark.value ? '#fff' : '#333'))
const bgColor = computed(() => (isDark.value ? '#24252F' : '#fefefe'))

const goToMenu = (menu: string) => {
  router.push({ name: menu as RouteRecordName, query: { ...query } })
  visible.value = false
}
const toggle = () => (visible.value = !visible.value)
provide('doingToggle', toggle)
defineExpose({ toggle })
</script>

<template>
  <CRow class="flex-grow-1">
    <CCol class="text-body main p-4 px-lg-5 mx-3">
      <slot> Under Construction!</slot>
    </CCol>

    <CCol v-if="aside" class="text-body p-4 d-none d-xl-block col-lg-2">
      <slot name="aside"> Under Construction!</slot>
    </CCol>

    <COffcanvas placement="end" class="p-2" :visible="visible" @hide="() => (visible = !visible)">
      <COffcanvasHeader>
        <COffcanvasTitle>
          <CFormInput placeholder="검색" />
        </COffcanvasTitle>
        <CCloseButton class="text-reset" @click="() => (visible = false)" />
      </COffcanvasHeader>

      <v-divider />

      <COffcanvasBody class="p-0">
        <v-card class="mx-auto mb-5 pointer" max-width="500" border flat>
          <v-list density="compact" :base-color="baseColor" :bg-color="bgColor">
            <v-list-item
              v-for="(menu, i) in navMenu"
              :key="i"
              :active="
                (route.name as string).includes(menu) || (route.meta as any).title.includes(menu)
              "
              @click="goToMenu(menu as string)"
            >
              {{ (menu as string).replace(/^\((.*)\)$/, '$1') }}
            </v-list-item>
          </v-list>
        </v-card>

        <v-divider />

        <slot name="aside">
          Content for the offcanvas goes here. You can place just about any Bootstrap component or
          custom elements here.
        </slot>
      </COffcanvasBody>
    </COffcanvas>
  </CRow>
</template>

<style lang="scss" scoped>
.main {
  background: #ffffff;
  border-right: 1px solid #ddd !important;
}

.dark-theme .main {
  background: #1c1d26;
  border-right: 1px solid #333 !important;
}

.active {
  font-weight: bold;
  background: #e5e7eb;
}

.dark-theme .active {
  background: #32333d;
}
</style>
