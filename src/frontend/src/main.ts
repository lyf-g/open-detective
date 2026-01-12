import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './style.css'
import App from './App.vue'
import i18n from './i18n'
import axios from 'axios';
import { ElMessage } from 'element-plus';

axios.interceptors.response.use(
  response => response,
  error => {
    const msg = error.response?.data?.detail || error.message || 'Network Error';
    if (msg !== 'Network Error') ElMessage.error(msg);
    return Promise.reject(error);
  }
);

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(i18n)
app.mount('#app')