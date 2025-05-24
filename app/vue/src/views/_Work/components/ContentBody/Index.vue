<script lang="ts" setup>
import { inject, provide, ref } from 'vue'
import { type RouteRecordName, useRoute, useRouter } from 'vue-router'

const props = defineProps({ aside: { type: Boolean, default: true } })

const visible = ref(false)

const query = inject('query')
const navMenu = inject('navMenu')

const [route, router] = [useRoute(), useRouter()]

const goToMenu = (menu: string) => {
  router.push({ name: menu as RouteRecordName, query: query.value })
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

    <COffcanvas
      placement="end"
      class="p-2"
      :visible="visible"
      @hide="
        () => {
          visible = !visible
        }
      "
    >
      <COffcanvasHeader>
        <COffcanvasTitle>
          <CFormInput placeholder="검색" />
        </COffcanvasTitle>
        <CCloseButton
          class="text-reset"
          @click="
            () => {
              visible = false
            }
          "
        />
      </COffcanvasHeader>

      <v-divider />

      <COffcanvasBody class="p-0">
        <CRow class="lg-3">
          <CCol class="d-grid gap-2">
            <CNavbarNav vertical role="group" aria-label="Vertical button group" class="m-0">
              <CNavItem v-for="(menu, i) in navMenu" :key="i">
                <CNavLink
                  @click="goToMenu(menu as string)"
                  :active="
                    (route.name as string).includes(menu) ||
                    (route.meta as any).title.includes(menu)
                  "
                  class="pl-3"
                >
                  {{ menu }}
                </CNavLink>
              </CNavItem>
            </CNavbarNav>
          </CCol>
        </CRow>

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
