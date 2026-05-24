import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { loadFonts } from '@/plugins/webfontloader'
import { vMaska } from 'maska/vue'
import { CIcon } from '@coreui/icons-vue'
import { iconsSet as icons } from '@/assets/icons'
import router from '@/router'
import CoreuiVue from '@coreui/vue'
import vuetify from '@/plugins/vuetify'
import '@/styles/style.scss'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
;(async () => {
  try {
    await loadFonts()
    app.use(router)
    app.use(vuetify)
    app.use(CoreuiVue)
    app.provide('icons', icons)
    app.component('CIcon', CIcon)
    app.directive('maska', vMaska)
    app.mount('#app')
  } catch (error) {
    console.error('App initialization failed:', error)
  }
})()
