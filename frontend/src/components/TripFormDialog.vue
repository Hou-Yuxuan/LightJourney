<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑行程' : '新建行程'"
    width="520px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="城市" prop="city">
        <el-input v-model="form.city" placeholder="如：成都" />
      </el-form-item>
      <el-form-item label="日期" prop="date">
        <el-date-picker
          v-model="form.date"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="开始" prop="start_time">
            <el-time-picker
              v-model="form.start_time"
              placeholder="开始时间"
              format="HH:mm"
              value-format="HH:mm"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结束" prop="end_time">
            <el-time-picker
              v-model="form.end_time"
              placeholder="结束时间"
              format="HH:mm"
              value-format="HH:mm"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="行程标题" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="行程描述（选填）" />
      </el-form-item>

      <!-- 图片上传 -->
      <el-form-item label="图片">
        <div
          class="image-upload"
          :class="{ 'image-upload--has': imagePreview, 'image-upload--uploading': uploading }"
          @click="!uploading && triggerUpload()"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            style="display:none"
            @change="handleFile"
          />
          <template v-if="uploading">
            <el-icon :size="24" class="image-upload__spin"><Loading /></el-icon>
            <span class="image-upload__text">上传中...</span>
          </template>
          <template v-else-if="imagePreview">
            <img :src="imagePreview" class="image-upload__preview" />
            <div class="image-upload__overlay">
              <el-icon :size="20"><EditPen /></el-icon>
            </div>
          </template>
          <template v-else>
            <el-icon :size="28" class="image-upload__icon"><Plus /></el-icon>
            <span class="image-upload__text">点击或拖拽上传图片</span>
          </template>
        </div>
        <el-button v-if="imagePreview" link type="danger" size="small" @click="clearImage" style="margin-top:4px">
          移除图片
        </el-button>
      </el-form-item>

      <el-form-item label="预算">
        <el-input-number v-model="form.budget" :min="0" :precision="2" :step="10" style="width: 100%" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, EditPen, Loading } from '@element-plus/icons-vue'
import { createTrip, updateTrip } from '../api/trips'
import api from '../api'

const props = defineProps({
  visible: { type: Boolean, default: false },
  trip: { type: Object, default: null },
})

const emit = defineEmits(['update:visible', 'saved'])

const isEdit = ref(false)
const loading = ref(false)
const uploading = ref(false)
const formRef = ref(null)
const fileInput = ref(null)
const imagePreview = ref('')
const pendingFile = ref(null)  // 待上传的文件

const defaultForm = () => ({
  city: '',
  date: '',
  start_time: '',
  end_time: '',
  title: '',
  description: '',
  image_url: '',
  budget: 0,
})

const form = reactive(defaultForm())

const validateTimeRange = (_rule, _value, callback) => {
  if (form.start_time && form.end_time && form.end_time <= form.start_time) {
    callback(new Error('结束时间必须晚于开始时间'))
  } else {
    callback()
  }
}

const rules = {
  city: [{ required: true, message: '请输入城市', trigger: 'blur' }],
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    { validator: validateTimeRange, trigger: 'change' },
  ],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

// ---- 图片上传 ----
function triggerUpload() {
  fileInput.value?.click()
}

function clearImage() {
  imagePreview.value = ''
  form.image_url = ''
  pendingFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function uploadFile(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await api.post('/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  if (res.data.code !== 200) {
    throw new Error(res.data.message || '上传失败')
  }
  return res.data.data.url
}

async function handleFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 10MB')
    return
  }

  // 预览
  const reader = new FileReader()
  reader.onload = (ev) => { imagePreview.value = ev.target.result }
  reader.readAsDataURL(file)

  // 上传
  uploading.value = true
  try {
    const url = await uploadFile(file)
    form.image_url = url
    pendingFile.value = null
  } catch (err) {
    ElMessage.error(err.message || '图片上传失败')
    imagePreview.value = ''
  } finally {
    uploading.value = false
  }
}

function handleDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请拖入图片文件')
    return
  }
  const fakeE = { target: { files: [file] } }
  handleFile(fakeE)
}

// ---- 弹窗初始化 ----
watch(() => props.visible, (val) => {
  if (!val) return
  Object.assign(form, defaultForm())
  formRef.value?.clearValidate()
  imagePreview.value = ''
  pendingFile.value = null
  uploading.value = false

  if (props.trip?.id) {
    isEdit.value = true
    Object.assign(form, {
      city: props.trip.city || '',
      date: props.trip.date || '',
      start_time: props.trip.start_time || '',
      end_time: props.trip.end_time || '',
      title: props.trip.title || '',
      description: props.trip.description || '',
      image_url: props.trip.image_url || '',
      budget: props.trip.budget ?? 0,
    })
    if (props.trip.image_url) {
      imagePreview.value = props.trip.image_url
    }
  } else if (props.trip) {
    // 预填模式（有字段但无 id）
    isEdit.value = false
    if (props.trip.date) form.date = props.trip.date
  } else {
    isEdit.value = false
  }
})

// ---- 提交 ----
const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (uploading.value) {
    ElMessage.warning('图片正在上传，请稍候')
    return
  }

  // 构建提交数据（排除不必要的字段）
  const payload = {
    city: form.city,
    date: form.date,
    start_time: form.start_time,
    end_time: form.end_time,
    title: form.title,
    description: form.description,
    image_url: form.image_url,
    budget: form.budget,
  }

  loading.value = true
  try {
    if (isEdit.value && props.trip?.id) {
      // 只发送变更的字段
      const changes = {}
      for (const [k, v] of Object.entries(payload)) {
        if (v !== (props.trip[k] ?? (k === 'budget' ? 0 : ''))) {
          changes[k] = v
        }
      }
      if (Object.keys(changes).length > 0) {
        await updateTrip(props.trip.id, changes)
        ElMessage.success('行程更新成功')
      } else {
        ElMessage.info('没有变更')
      }
    } else {
      await createTrip(payload)
      ElMessage.success('行程创建成功')
    }
    emit('update:visible', false)
    emit('saved')
  } catch {
    // 拦截器已处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.image-upload {
  width: 100%;
  height: 120px;
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  position: relative;
  transition: var(--transition-fast);
  background: #fafbfc;
}
.image-upload:hover {
  border-color: var(--color-accent);
  background: #f5f8f4;
}
.image-upload--has {
  padding: 0;
  border-style: solid;
}
.image-upload--uploading {
  cursor: wait;
  opacity: 0.7;
}
.image-upload__icon {
  color: var(--text-secondary);
}
.image-upload__spin {
  color: var(--color-accent);
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.image-upload__text {
  margin-top: 4px;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.image-upload__preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.image-upload__overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: var(--transition-fast);
}
.image-upload--has:hover .image-upload__overlay {
  opacity: 1;
}
</style>
