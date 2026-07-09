<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-card__title">
        <el-icon class="login-card__icon"><MapLocation /></el-icon>
        LightJourney
      </h1>
      <p class="login-card__subtitle">AI 驱动的旅行行程管理</p>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-card__btn" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <p class="login-card__link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MapLocation } from '@element-plus/icons-vue'
import { login } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const form = reactive({ username: '', password: '' })
const loading = ref(false)

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login(form.username, form.password)
    const { access_token, username } = res.data.data
    userStore.setAuth(access_token, username)
    ElMessage.success('登录成功')
    router.push('/trips')
  } catch (err) {
    // 不重复弹窗：拦截器已在非 auth 页处理了 401，此处仅处理登录/注册页的 401
    const msg = err.response?.data?.message || err.message || '登录失败'
    if (msg && msg !== 'success') {
      ElMessage.error(msg)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  /* 底基色 */
  background-color: #ECEEF1;
  /* 网格 + 散点纹理 */
  background-image:
    /* 主网格 */
    linear-gradient(rgba(91, 124, 153, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(91, 124, 153, 0.07) 1px, transparent 1px),
    /* 对角等高线 */
    linear-gradient(45deg, rgba(91, 124, 153, 0.05) 1px, transparent 1px),
    /* 散点 */
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
.login-page::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    /* 左上——森林高地区 */
    radial-gradient(ellipse 600px 500px at 15% 10%, rgba(130, 155, 130, 0.18), transparent 70%),
    /* 右上——湖泊蓝区 */
    radial-gradient(ellipse 450px 400px at 80% 20%, rgba(120, 150, 175, 0.15), transparent 70%),
    /* 中左——草甸浅绿 */
    radial-gradient(ellipse 500px 350px at 30% 50%, rgba(155, 175, 150, 0.14), transparent 70%),
    /* 右下——暖棕盆地区 */
    radial-gradient(ellipse 550px 400px at 75% 75%, rgba(185, 170, 150, 0.16), transparent 70%),
    /* 左下——低地灰绿 */
    radial-gradient(ellipse 400px 300px at 10% 85%, rgba(145, 160, 145, 0.12), transparent 70%),
    /* 顶部中央——高地微光 */
    radial-gradient(ellipse 350px 250px at 50% 5%, rgba(175, 180, 170, 0.10), transparent 70%);
}

.login-card {
  position: relative;
  z-index: 1;
  width: 380px;
  padding: var(--spacing-xl);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 20px rgba(91, 124, 153, 0.08);
}

.login-card__title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  font-size: 24px;
  font-weight: var(--font-weight-medium);
  color: var(--color-accent);
  margin: 0 0 var(--spacing-xs);
  letter-spacing: 1px;
}

.login-card__icon {
  font-size: 26px;
}

.login-card__subtitle {
  text-align: center;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-lg);
}

.login-card__btn {
  width: 100%;
}

.login-card__link {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.login-card__link a {
  color: var(--color-accent);
  font-weight: var(--font-weight-medium);
}
</style>
