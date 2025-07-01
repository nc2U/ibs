<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeMount, ref } from 'vue'
import { useStore } from '@/store'
import type { Company } from '@/store/types/settings'
import avatar2 from '@/assets/images/avatars/2.jpg'
import avatar3 from '@/assets/images/avatars/3.jpg'
import avatar4 from '@/assets/images/avatars/4.jpg'
import avatar5 from '@/assets/images/avatars/5.jpg'
import avatar6 from '@/assets/images/avatars/6.jpg'
import avatar7 from '@/assets/images/avatars/7.jpg'
import avatar8 from '@/assets/images/avatars/8.jpg'

const activeKey = ref(1)

const company = inject<ComputedRef<Company | null>>('company')

const store = useStore()
const isDark = computed(() => store.theme === 'dark')
const white = computed(() => (isDark.value ? 'dark-theme' : 'bg-white'))
const light = computed(() => (isDark.value ? 'dark-theme' : 'bg-light'))
const asideVisible = computed(() => store.asideVisible)

const active = (key: number) => key === activeKey.value

const updateActiveKey = (key: number) => (activeKey.value = key)

onBeforeMount(async () => {
  if (company) document.title = company.value?.name ?? '' + ' :: IBS'
})
</script>

<template>
  <CSidebar
    color-scheme="light"
    self-hiding="xxl"
    size="lg"
    overlaid
    position="end"
    :visible="asideVisible"
    :class="white"
  >
    <CSidebarHeader class="bg-transparent p-0">
      <CNav variant="underline">
        <CNavItem :class="{ selected: active(1) }">
          <CNavLink @click="updateActiveKey(1)">
            <CIcon icon="cil-List" alt="CoreUI Icons List" />
          </CNavLink>
        </CNavItem>
        <CNavItem :class="{ selected: active(2) }">
          <CNavLink @click="updateActiveKey(2)">
            <CIcon icon="cil-speech" alt="CoreUI Icons Speech" />
          </CNavLink>
        </CNavItem>
        <CNavItem :class="{ selected: active(3) }">
          <CNavLink @click="updateActiveKey(3)">
            <CIcon icon="cil-settings" alt="CoreUI Icons Settings" />
          </CNavLink>
        </CNavItem>
        <CNavItem class="ms-auto me-2 d-flex align-items-center">
          <CCloseButton @click="store.toggleAside" />
        </CNavItem>
      </CNav>
    </CSidebarHeader>
    <CTabContent class="border-top-1">
      <CTabPane :visible="activeKey == 1">
        <CListGroup flush>
          <CListGroupItem
            class="list-group-item border-start-4 border-start-secondary text-center fw-bold text-medium-emphasis text-uppercase small"
            :class="light"
          >
            Today
          </CListGroupItem>
          <CListGroupItem href="#" class="border-start-4 border-start-warning">
            <CAvatar :src="avatar7 as any" size="lg" class="float-end" />
            <div>Meeting with <strong>Lucas</strong></div>
            <small class="text-medium-emphasis me-3">
              <CIcon icon="cil-calendar" />
              1 - 3pm
            </small>
            <small class="text-medium-emphasis">
              <CIcon icon="cil-location-pin" />
              Palo Alto, CA
            </small>
          </CListGroupItem>
          <CListGroupItem href="#" class="border-start-4 border-start-info">
            <CAvatar :src="avatar4 as any" size="lg" class="float-end" />
            <div>Skype with <strong>Megan</strong></div>
            <small class="text-medium-emphasis me-3">
              <CIcon icon="cil-calendar" />
              4 - 5pm
            </small>
            <small class="text-medium-emphasis">
              <CIcon icon="cib-skype" />
              On-line
            </small>
          </CListGroupItem>
          <CListGroupItem
            class="border-start-4 border-start-secondary text-center fw-bold text-medium-emphasis text-uppercase small"
            :class="light"
          >
            Tomorrow
          </CListGroupItem>
          <CListGroupItem accent="danger" href="#" class="border-start-4 border-start-danger">
            <div>New UI Project - <strong>deadline</strong></div>
            <small class="text-medium-emphasis me-3">
              <CIcon icon="cil-calendar" />
              10 - 11pm
            </small>
            <small class="text-medium-emphasis">
              <CIcon icon="cil-home" />
              creativeLabs HQ
            </small>
            <div class="avatars-stack mt-2">
              <CAvatar :src="avatar2 as any" size="sm" />
              <CAvatar :src="avatar3 as any" size="sm" />
              <CAvatar :src="avatar4 as any" size="sm" />
              <CAvatar :src="avatar5 as any" size="sm" />
              <CAvatar :src="avatar6 as any" size="sm" />
            </div>
          </CListGroupItem>
          <CListGroupItem href="#" class="border-start-4 border-start-success">
            <div><strong>#10 Startups.Garden</strong> Meetup</div>
            <small class="text-medium-emphasis me-3">
              <CIcon icon="cil-calendar" />
              1 - 3pm
            </small>
            <small class="text-medium-emphasis">
              <CIcon icon="cil-location-pin" />
              Palo Alto, CA
            </small>
          </CListGroupItem>
          <CListGroupItem href="#" class="border-start-4 border-start-primary border-bottom">
            <div>
              <strong>Team meeting</strong>
            </div>
            <small class="text-medium-emphasis me-3">
              <CIcon icon="cil-calendar" />
              4 - 6pm
            </small>
            <small class="text-medium-emphasis">
              <CIcon icon="cil-home" />
              creativeLabs HQ
            </small>
            <div class="/avatars-stack mt-2">
              <CAvatar :src="avatar2 as any" size="sm" />
              <CAvatar :src="avatar3 as any" size="sm" />
              <CAvatar :src="avatar4 as any" size="sm" />
              <CAvatar :src="avatar5 as any" size="sm" />
              <CAvatar :src="avatar6 as any" size="sm" />
              <CAvatar :src="avatar7 as any" size="sm" />
              <CAvatar :src="avatar8 as any" size="sm" />
            </div>
          </CListGroupItem>
        </CListGroup>
      </CTabPane>
      <CTabPane class="p-3" :visible="activeKey == 2">
        <div class="message">
          <div class="py-3 pb-5 me-3 float-start">
            <CAvatar :src="avatar7 as any" status="success" size="md" />
          </div>
          <div>
            <small class="text-medium-emphasis">Lukasz Holeczek</small>
            <small class="text-medium-emphasis float-end mt-1">1:52 PM</small>
          </div>
          <div class="text-truncate fw-semibold">Lorem ipsum dolor sit amet</div>
          <small class="text-medium-emphasis">
            Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
            incididunt...
          </small>
        </div>

        <v-divider />

        <div class="message">
          <div class="py-3 pb-5 me-3 float-start">
            <CAvatar :src="avatar7 as any" status="success" size="md" />
          </div>
          <div>
            <small class="text-medium-emphasis">Lukasz Holeczek</small>
            <small class="text-medium-emphasis float-end mt-1">1:52 PM</small>
          </div>
          <div class="text-truncate fw-semibold">Lorem ipsum dolor sit amet</div>
          <small class="text-medium-emphasis">
            Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
            incididunt...
          </small>
        </div>

        <v-divider />

        <div class="message">
          <div class="py-3 pb-5 me-3 float-start">
            <CAvatar :src="avatar7 as any" status="success" size="md" />
          </div>
          <div>
            <small class="text-medium-emphasis">Lukasz Holeczek</small>
            <small class="text-medium-emphasis float-end mt-1">1:52 PM</small>
          </div>
          <div class="text-truncate fw-semibold">Lorem ipsum dolor sit amet</div>
          <small class="text-medium-emphasis">
            Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
            incididunt...
          </small>
        </div>

        <v-divider />

        <div class="message">
          <div class="py-3 pb-5 me-3 float-start">
            <CAvatar :src="avatar7 as any" status="success" size="md" />
          </div>
          <div>
            <small class="text-medium-emphasis">Lukasz Holeczek</small>
            <small class="text-medium-emphasis float-end mt-1">1:52 PM</small>
          </div>
          <div class="text-truncate fw-semibold">Lorem ipsum dolor sit amet</div>
          <small class="text-medium-emphasis">
            Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
            incididunt...
          </small>
        </div>

        <v-divider />

        <div class="message">
          <div class="py-3 pb-5 me-3 float-start">
            <CAvatar :src="avatar7 as any" status="success" size="md" />
          </div>
          <div>
            <small class="text-medium-emphasis">Lukasz Holeczek</small>
            <small class="text-medium-emphasis float-end mt-1">1:52 PM</small>
          </div>
          <div class="text-truncate fw-semibold">Lorem ipsum dolor sit amet</div>
          <small class="text-medium-emphasis">
            Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
            incididunt...
          </small>
        </div>
      </CTabPane>
      <CTabPane class="p-3" :visible="activeKey == 3">
        <h6>Settings</h6>
        <div>
          <div class="clearfix mt-4">
            <CFormSwitch id="Option1" size="lg" label="Option 1" default-checked />
          </div>
          <div>
            <small class="text-medium-emphasis">
              Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
              incididunt ut labore et dolore magna aliqua.
            </small>
          </div>
        </div>
        <div>
          <div class="clearfix mt-3">
            <CFormSwitch id="fOption2" size="lg" label="Option 2" />
          </div>
          <div>
            <small class="text-medium-emphasis">
              Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
              incididunt ut labore et dolore magna aliqua.
            </small>
          </div>
        </div>
        <div>
          <div class="clearfix mt-3">
            <CFormSwitch id="Option3" size="lg" label="Option 3" />
          </div>
        </div>
        <div>
          <div class="clearfix mt-3">
            <CFormSwitch id="Option4" size="lg" label="Option 4" default-checked />
          </div>
        </div>

        <v-divider />

        <h6>System Utilization</h6>
        <div class="text-uppercase mb-1 mt-4">
          <small>
            <b>CPU Usage</b>
          </small>
        </div>
        <CProgress thin color="info" :value="25" />
        <small class="text-medium-emphasis">348 Processes. 1/4 Cores.</small>
        <div class="text-uppercase mb-1 mt-2">
          <small>
            <b>Memory Usage</b>
          </small>
        </div>
        <CProgress thin color="warning" :value="70" />
        <small class="text-medium-emphasis">11444GB/16384MB</small>
        <div class="text-uppercase mb-1 mt-2">
          <small>
            <b>SSD 1 Usage</b>
          </small>
        </div>
        <CProgress thin color="danger" :value="95" />
        <small class="text-medium-emphasis">243GB/256GB</small>
        <div class="text-uppercase mb-1 mt-2">
          <small>
            <b>SSD 2 Usage</b>
          </small>
        </div>
        <CProgress thin color="success" :value="10" />
        <small class="text-medium-emphasis">25GB/256GB</small>
      </CTabPane>
    </CTabContent>
  </CSidebar>
</template>

<style lang="scss" scoped>
.selected,
.selected:hover {
  border-bottom: solid 1px #0d6efd;
}

.border-top-1 {
  border-top: 1px solid #ddd;
}
</style>
