import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { vMaska } from 'maska'
import { CIcon } from '@coreui/icons-vue'
import { iconsSet as icons } from '@/assets/icons'
import { loadFonts } from '@/plugins/webfontloader'
import ganttastic from '@infectoone/vue-ganttastic'
import Cookies from 'js-cookie'
import CoreuiVue from '@coreui/vue'
import vuetify from '@/plugins/vuetify'
import router from '@/router'
import '@/styles/style.scss'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

const accStore = useAccount()
const cookie = Cookies.get('accessToken')
const init = () => accStore.loginByToken(cookie)

init().then(() =>
  loadFonts().then(() => {
    app.use(router)
    app.use(vuetify)
    app.use(CoreuiVue, [])
    app.use(ganttastic)
    app.provide('icons', icons)
    app.component('CIcon', CIcon)
    app.directive('maska', vMaska)
    app.mount('#app')
  }),
)
