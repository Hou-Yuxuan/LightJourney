<template>
  <div class="register-page">
    <div class="register-card">
      <h1 class="register-card__title">
        <el-icon class="register-card__icon"><MapLocation /></el-icon>
        创建账号
      </h1>
      <p class="register-card__subtitle">加入 LightJourney，开始智能规划旅行</p>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent="handleRegister">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名（2-20位字母数字下划线）" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码（6-30位）" show-password />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="register-card__btn" @click="handleRegister">
            注 册
          </el-button>
        </el-form-item>
      </el-form>

      <p class="register-card__link">
        已有账号？<router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MapLocation } from '@element-plus/icons-vue'
import { register, login } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const form = reactive({ username: '', password: '', confirmPassword: '' })
const loading = ref(false)

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]{2,20}$/, message: '2-20位字母、数字或下划线', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度为6-30位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    // 注册
    await register(form.username, form.password)
    // 注册成功自动登录
    const res = await login(form.username, form.password)
    const { access_token, username } = res.data.data
    userStore.setAuth(access_token, username)
    ElMessage.success('注册成功')
    router.push('/trips')
  } catch (err) {
    const msg = err.response?.data?.message || err.message || '注册失败'
    if (msg && msg !== 'success') {
      ElMessage.error(msg)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background-color: #ECEEF1;
  background-image:
    linear-gradient(rgba(91, 124, 153, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(91, 124, 153, 0.07) 1px, transparent 1px),
    linear-gradient(45deg, rgba(91, 124, 153, 0.05) 1px, transparent 1px),
    radial-gradient(circle, rgba(91, 124, 153, 0.1) 1px, transparent 1px);
  background-size:
    48px 48px,
    48px 48px,
    96px 96px,
    24px 24px;
  background-position:
    0 0,
    0 0,
    0 0,
    12px 12px;
}

/* 地形色块图层 */
.register-page::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(ellipse 600px 500px at 15% 10%, rgba(130, 155, 130, 0.18), transparent 70%),
    radial-gradient(ellipse 450px 400px at 80% 20%, rgba(120, 150, 175, 0.15), transparent 70%),
    radial-gradient(ellipse 500px 350px at 30% 50%, rgba(155, 175, 150, 0.14), transparent 70%),
    radial-gradient(ellipse 550px 400px at 75% 75%, rgba(185, 170, 150, 0.16), transparent 70%),
    radial-gradient(ellipse 400px 300px at 10% 85%, rgba(145, 160, 145, 0.12), transparent 70%),
    radial-gradient(ellipse 350px 250px at 50% 5%, rgba(175, 180, 170, 0.10), transparent 70%);
}

.register-card {
  position: relative;
  z-index: 1;
  width: 380px;
  padding: var(--spacing-xl);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 20px rgba(91, 124, 153, 0.08);
}
.register-card__title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  font-size: 24px;
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs);
  letter-spacing: 1px;
}
.register-card__icon {
  font-size: 26px;
  color: var(--color-accent);
}
.register-card__subtitle {
  text-align: center;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-lg);
}
.register-card__btn {
  width: 100%;
}
.register-card__link {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.register-card__link a {
  color: var(--color-accent);
  font-weight: var(--font-weight-medium);
}
</style>
