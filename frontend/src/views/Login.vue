<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type FormInst, type FormRules } from 'naive-ui'
import {
  NForm,
  NFormItem,
  NInput,
  NButton,
  NCheckbox,
  NSpace,
} from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { login, type LoginParams } from '@/api/auth'

const router = useRouter()
const message = useMessage()
const userStore = useUserStore()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const rememberMe = ref(false)

const formData = reactive<LoginParams>({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度为 6-32 个字符', trigger: 'blur' },
  ],
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const res = await login(formData) as any
    userStore.setToken(res.token)
    userStore.setUsername(res.username)
    message.success('登录成功')
    router.push('/')
  } catch {
    message.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

function goRegister() {
  router.push('/register')
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-left">
        <div class="brand-area">
          <img src="@/assets/logo.png" alt="OpsBrain AI" class="brand-logo" />
          <h1 class="brand-title">运行智脑</h1>
          <p class="brand-subtitle">OpsBrain AI - 智能运维管理平台</p>
          <div class="brand-features">
            <div class="feature-item">
              <div class="feature-dot blue"></div>
              <span>智能监控与预警</span>
            </div>
            <div class="feature-item">
              <div class="feature-dot green"></div>
              <span>自动化运维流程</span>
            </div>
            <div class="feature-item">
              <div class="feature-dot blue"></div>
              <span>数据驱动决策</span>
            </div>
            <div class="feature-item">
              <div class="feature-dot green"></div>
              <span>绿色节能管理</span>
            </div>
          </div>
        </div>
      </div>

      <div class="login-right">
        <div class="login-form-wrapper">
          <h2 class="form-title">欢迎登录</h2>
          <p class="form-subtitle">登录您的账户以继续使用</p>

          <NForm ref="formRef" :model="formData" :rules="rules" label-placement="left" size="large" class="login-form">
            <NFormItem path="username" :show-label="false">
              <NInput v-model:value="formData.username" placeholder="请输入用户名" @keyup.enter="handleLogin">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </template>
              </NInput>
            </NFormItem>

            <NFormItem path="password" :show-label="false">
              <NInput v-model:value="formData.password" type="password" show-password-on="click" placeholder="请输入密码"
                @keyup.enter="handleLogin">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </template>
              </NInput>
            </NFormItem>

            <div class="form-options">
              <NCheckbox v-model:checked="rememberMe">记住我</NCheckbox>
              <a href="javascript:void(0)" class="forgot-link">忘记密码？</a>
            </div>

            <NButton type="primary" block strong :loading="loading" class="submit-btn" @click="handleLogin">
              登 录
            </NButton>

            <NSpace justify="center" class="register-link">
              <span class="hint-text">还没有账户？</span>
              <a href="javascript:void(0)" @click="goRegister">立即注册</a>
            </NSpace>
          </NForm>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e3f2fd 0%, #e8f5e9 50%, #f5f7fa 100%);
  overflow: hidden;
}

.login-container {
  display: flex;
  width: 900px;
  min-height: 540px;
  background: @bg-white;
  border-radius: @border-radius-xl;
  box-shadow: @shadow-lg;
  overflow: hidden;
}

.login-left {
  flex: 1;
  background: @gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
    top: -80px;
    right: -80px;
  }

  &::after {
    content: '';
    position: absolute;
    width: 200px;
    height: 200px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.04);
    bottom: -60px;
    left: -40px;
  }
}

.brand-area {
  text-align: center;
  color: #fff;
  position: relative;
  z-index: 1;
}

.brand-logo {
  width: 188px;
  height: 188px;
  margin-bottom: 20px;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: 2px;
}

.brand-subtitle {
  font-size: 14px;
  opacity: 0.85;
  margin-bottom: 36px;
}

.brand-features {
  text-align: left;
  display: inline-block;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  font-size: 14px;
  opacity: 0.9;
}

.feature-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &.blue {
    background: #bbdefb;
  }

  &.green {
    background: #c8e6c9;
  }
}

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.login-form-wrapper {
  width: 100%;
  max-width: 360px;
}

.form-title {
  font-size: 26px;
  font-weight: 700;
  color: @text-primary;
  margin-bottom: 8px;
}

.form-subtitle {
  font-size: 14px;
  color: @text-secondary;
  margin-bottom: 32px;
}

.login-form {
  :deep(.n-form-item) {
    margin-bottom: 20px;
  }

  :deep(.n-input) {
    --n-height: 44px !important;
  }

  :deep(.n-input__prefix) {
    color: @text-placeholder;
    margin-right: 8px;
  }
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.forgot-link {
  font-size: 13px;
  color: @primary-blue;

  &:hover {
    color: @primary-blue-hover;
  }
}

.submit-btn {
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  background: @gradient-primary !important;
  border: none !important;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
    background: @gradient-primary-hover !important;
  }
}

.register-link {
  margin-top: 24px;
  font-size: 14px;

  .hint-text {
    color: @text-secondary;
  }

  a {
    color: @primary-blue;
    font-weight: 500;
  }
}

@media (max-width: 768px) {
  .login-container {
    width: 95%;
    flex-direction: column;
    min-height: auto;
  }

  .login-left {
    padding: 32px 24px;
    min-height: 200px;
  }

  .brand-features {
    display: none;
  }

  .login-right {
    padding: 32px 24px;
  }
}
</style>
