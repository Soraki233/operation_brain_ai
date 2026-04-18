import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import './styles/global.less'
import 'highlight.js/styles/atom-one-dark.css'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.mount('#app')
