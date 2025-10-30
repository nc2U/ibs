import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { loadFonts } from '@/plugins/webfontloader'
import { vMaska } from 'maska/vue'
import { CIcon } from '@coreui/icons-vue'
import { iconsSet as icons } from '@/assets/icons'
import router from '@/router'
import Cookies from 'js-cookie'
import CoreuiVue from '@coreui/vue'
import vuetify from '@/plugins/vuetify'
import ganttastic from '@infectoone/vue-ganttastic'
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
    app.use(CoreuiVue, [])
    app.use(ganttastic)
    app.provide('icons', icons)
    app.component('CIcon', CIcon)
    app.directive('maska', vMaska)
    app.mount('#app')

    // 앱 마운트 후 초기화
    const accStore = useAccount()
    const cookie = Cookies.get('accessToken')

    if (cookie) {
      try {
        await accStore.loginByToken(cookie)
      } catch (error) {
        console.error('Login by token failed:', error)
        await router.push({ name: 'Login' })
      }
    }
  } catch (error) {
    console.error('App initialization failed:', error)
  }
})()
