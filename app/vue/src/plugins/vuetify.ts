// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Vuetify
import { createVuetify } from 'vuetify'
import { ko } from 'vuetify/locale'

const myCustomLightTheme = {
  dark: false,
  colors: {
    secondary: '#CCCDCE',
    danger: '#B00020',
  },
}

export default createVuetify({
  locale: {
    locale: 'ko',
    fallback: 'en',
    messages: { ko },
  },
  theme: {
    defaultTheme: 'myCustomLightTheme',
    themes: {
      myCustomLightTheme,
    },
  },
})
