<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type FormInst, type FormRules, type FormItemRule } from 'naive-ui'
import {
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSpace,
} from 'naive-ui'
import { register, sendSmsCode, type RegisterParams } from '@/api/auth'

const router = useRouter()
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const smsLoading = ref(false)
const smsCooldown = ref(0)
let cooldownTimer: ReturnType<typeof setInterval> | null = null

const formData = reactive<RegisterParams>({
  username: '',
  phone: '',
  smsCode: '',
  password: '',
  confirmPassword: '',
})

function validatePasswordSame(_rule: FormItemRule, value: string): boolean {
  return value === formData.password
}

function validatePhone(_rule: FormItemRule, value: string): boolean {
  return /^1[3-9]\d{9}$/.test(value)
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' },
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { validator: validatePhone, message: '请输入有效的手机号', trigger: 'blur' },
  ],
  smsCode: [
    { required: true, message: '请输入短信验证码', trigger: 'blur' },
    { len: 6, message: '验证码为 6 位数字', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度为 6-32 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: validatePasswordSame,
      message: '两次输入的密码不一致',
      trigger: 'blur',
    },
  ],
}

function startCooldown() {
  smsCooldown.value = 60
  cooldownTimer = setInterval(() => {
    smsCooldown.value--
    if (smsCooldown.value <= 0) {
      clearInterval(cooldownTimer!)
      cooldownTimer = null
    }
  }, 1000)
}

async function handleSendSms() {
  if (smsCooldown.value > 0 || smsLoading.value) return

  try {
    await formRef.value?.validate(undefined, (rule) => rule?.key === 'phone')
  } catch {
    return
  }

  smsLoading.value = true
  try {
    await sendSmsCode(formData.phone)
    message.success('验证码已发送')
    startCooldown()
  } catch {
    message.error('验证码发送失败，请稍后重试')
  } finally {
    smsLoading.value = false
  }
}

async function handleRegister() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await register(formData)
    message.success('注册成功，请登录')
    router.push('/login')
  } catch {
    message.error('注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function goLogin() {
  router.push('/login')
}

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})
</script>

<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-left">
        <div class="brand-area">
          <img src="@/assets/logo.png" alt="OpsBrain AI" class="brand-logo" />
          <h1 class="brand-title">运行智脑</h1>
          <p class="brand-subtitle">OpsBrain AI - 智能运维管理平台</p>
          <div class="brand-desc">
            <p>加入我们，开启智能运维新时代</p>
            <p>让 AI 为您的运维保驾护航</p>
          </div>
        </div>
      </div>

      <div class="register-right">
        <div class="register-form-wrapper">
          <h2 class="form-title">创建账户</h2>
          <p class="form-subtitle">填写以下信息注册新账户</p>

          <NForm ref="formRef" :model="formData" :rules="rules" label-placement="left" size="large"
            class="register-form">
            <NFormItem path="username" :show-label="false">
              <NInput v-model:value="formData.username" placeholder="请输入用户名">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </template>
              </NInput>
            </NFormItem>

            <NFormItem path="phone" :show-label="false">
              <NInput v-model:value="formData.phone" placeholder="请输入手机号" maxlength="11">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
                    <line x1="12" y1="18" x2="12.01" y2="18" />
                  </svg>
                </template>
              </NInput>
            </NFormItem>

            <NFormItem path="smsCode" :show-label="false">
              <div class="sms-code-row">
                <NInput v-model:value="formData.smsCode" placeholder="请输入短信验证码" maxlength="6"
                  class="sms-code-input">
                  <template #prefix>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  </template>
                </NInput>
                <NButton :disabled="smsCooldown > 0" :loading="smsLoading" class="sms-btn"
                  @click="handleSendSms">
                  {{ smsCooldown > 0 ? `${smsCooldown}s` : '获取验证码' }}
                </NButton>
              </div>
            </NFormItem>

            <NFormItem path="password" :show-label="false">
              <NInput v-model:value="formData.password" type="password" show-password-on="click" placeholder="请输入密码">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </template>
              </NInput>
            </NFormItem>

            <NFormItem path="confirmPassword" :show-label="false">
              <NInput v-model:value="formData.confirmPassword" type="password" show-password-on="click"
                placeholder="请再次输入密码" @keyup.enter="handleRegister">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                </template>
              </NInput>
            </NFormItem>

            <NButton type="primary" block strong :loading="loading" class="submit-btn" @click="handleRegister">
              注 册
            </NButton>

            <NSpace justify="center" class="login-link">
              <span class="hint-text">已有账户？</span>
              <a href="javascript:void(0)" @click="goLogin">返回登录</a>
            </NSpace>
          </NForm>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.register-page {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f5e9 0%, #e3f2fd 50%, #f5f7fa 100%);
  overflow: hidden;
}

.register-container {
  display: flex;
  width: 900px;
  min-height: 580px;
  background: @bg-white;
  border-radius: @border-radius-xl;
  box-shadow: @shadow-lg;
  overflow: hidden;
}

.register-left {
  flex: 1;
  background: linear-gradient(135deg, @primary-green, @primary-blue);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 250px;
    height: 250px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
    bottom: -60px;
    right: -60px;
  }

  &::after {
    content: '';
    position: absolute;
    width: 180px;
    height: 180px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.04);
    top: -40px;
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

.brand-desc {
  p {
    font-size: 14px;
    opacity: 0.85;
    line-height: 2;
  }
}

.register-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.register-form-wrapper {
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
  margin-bottom: 28px;
}

.register-form {
  :deep(.n-form-item) {
    margin-bottom: 18px;
  }

  :deep(.n-input) {
    --n-height: 44px !important;
  }

  :deep(.n-input__prefix) {
    color: @text-placeholder;
    margin-right: 8px;
  }
}

.sms-code-row {
  display: flex;
  width: 100%;
  gap: 10px;

  .sms-code-input {
    flex: 1;
  }

  .sms-btn {
    flex-shrink: 0;
    height: 44px;
    min-width: 110px;
    font-size: 13px;
  }
}

.submit-btn {
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  margin-top: 8px;
  background: linear-gradient(135deg, @primary-green, @primary-blue) !important;
  border: none !important;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
  }
}

.login-link {
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
  .register-container {
    width: 95%;
    flex-direction: column;
    min-height: auto;
  }

  .register-left {
    padding: 32px 24px;
    min-height: 180px;
  }

  .brand-desc {
    display: none;
  }

  .register-right {
    padding: 32px 24px;
  }
}
</style>
