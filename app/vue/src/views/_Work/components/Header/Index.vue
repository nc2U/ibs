<script lang="ts" setup>
import { ref, computed, type PropType, watch } from 'vue'
import { useStore } from '@/store'
import { useRoute } from 'vue-router'
import type { SimpleProject } from '@/store/types/work'
import HeaderSearch from './components/Search.vue'
import HeaderNav from './components/HeaderNav.vue'

defineProps({
  pageTitle: { type: String, default: '' },
  navMenu: { type: Array, default: () => ['Base Menu'] },
  familyTree: { type: Array as PropType<SimpleProject[]>, default: () => [] },
})

const visible = ref(false)

const isDark = computed(() => useStore().theme === 'dark')
const backGround = computed(() => (isDark.value ? 'bg-blue-grey-darken-5' : 'bg-indigo-lighten-5'))

const emit = defineEmits(['side-nav-call'])
const sideNavCall = () => emit('side-nav-call')

const route = useRoute()
watch(route, () => (visible.value = false))
</script>

<template>
  <CRow class="mb-0" :class="backGround">
    <CCol>
      <CRow class="px-3">
        <CCol class="mb-2 p-4 col-9 col-md-6 col-lg-7 col-xl-9">
          <CRow v-if="!!familyTree.length" class="d-none d-lg-block">
            <CCol>
              <span v-for="p in familyTree" :key="p.pk">
                <span v-if="p.visible" class="mr-1 text-blue-grey">
                  <router-link :to="{ name: route.name ?? '(개요)', params: { projId: p.slug } }">
                    {{ p.name }}
                  </router-link>
                  »
                </span>
              </span>
            </CCol>
          </CRow>

          <CRow>
            <CCol class="text-body d-none d-lg-block">
              <strong class="title pl-1"> {{ pageTitle }}</strong>
            </CCol>

            <CCol
              class="text-body d-xl-none"
              :class="{ pointer: !!familyTree.length }"
              @click="visible = !visible"
            >
              <v-icon
                v-if="!!familyTree.length"
                :icon="visible ? 'mdi-chevron-up' : 'mdi-chevron-down'"
                color=""
              />
              <strong class="title pl-1"> {{ pageTitle }}</strong>
              <CCollapse v-if="!!familyTree.length" :visible="visible">
                <CCard class="mt-3">
                  <CCardBody>
                    <span v-for="p in familyTree" :key="p.pk" class="mr-1 text-blue-grey">
                      <router-link :to="{ name: '(개요)', params: { projId: p.slug } }">
                        {{ p.name }}
                      </router-link>
                      »
                    </span>
                  </CCardBody>
                </CCard>
              </CCollapse>
            </CCol>
          </CRow>
        </CCol>

        <CCol class="text-body d-xl-none text-right p-3">
          <v-app-bar-nav-icon @click="sideNavCall" />
        </CCol>
        <CCol class="d-none d-lg-block text-right">
          <HeaderSearch />
        </CCol>
      </CRow>

      <CRow class="d-none d-lg-block">
        <CCol>
          <HeaderNav :menus="navMenu" />
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
strong.title {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 20px;
  color: #5e636a;
}

.dark-theme .title {
  color: #ddd;
}
</style>
