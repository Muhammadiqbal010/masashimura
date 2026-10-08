<template>
  <div class="imgf" :class="{ 'imgf--stack': stack }">
    <button
      type="button"
      class="imgf-thumb"
      :style="{ aspectRatio: ratio, width: thumbWidth }"
      :aria-label="`${modelValue ? 'Ganti' : 'Pilih'} foto: ${label}`"
      @click="inputEl.click()"
    >
      <img v-if="modelValue" :src="modelValue" alt="" loading="lazy" />
      <span v-else class="imgf-empty"><ImagePlus :size="20" /><span>Belum ada foto</span></span>
      <span class="imgf-overlay"><Pencil :size="13" /> Ganti</span>
    </button>

    <div class="imgf-side">
      <p class="imgf-url adm-mono" :title="modelValue || ''">
        {{ modelValue || 'URL terisi otomatis setelah foto diupload' }}
      </p>
      <div class="imgf-actions">
        <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="inputEl.click()">
          <Upload :size="13" /> {{ modelValue ? 'Ganti foto' : 'Pilih foto' }}
        </button>
        <button
          v-if="modelValue && removable"
          type="button"
          class="adm-btn adm-btn--ghost adm-btn--sm"
          @click="emit('clear')"
        >
          <Trash2 :size="13" /> Hapus
        </button>
      </div>
      <p v-if="hint" class="adm-hint">{{ hint }}</p>
    </div>

    <input ref="inputEl" type="file" accept="image/*" hidden @change="onChange" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ImagePlus, Pencil, Upload, Trash2 } from 'lucide-vue-next'

defineProps({
  modelValue: { type: String, default: null }, // URL foto saat ini
  label: { type: String, default: 'foto' },
  ratio: { type: String, default: '1 / 1' },
  thumbWidth: { type: String, default: '6.5rem' },
  hint: { type: String, default: '' },
  removable: Boolean,
  stack: Boolean, // thumbnail di atas, bukan di samping
})
const emit = defineEmits(['pick', 'clear'])

const inputEl = ref(null)
const onChange = (e) => {
  const file = e.target.files?.[0]
  e.target.value = '' // supaya file yang sama bisa dipilih lagi
  if (file) emit('pick', file)
}
</script>

<style scoped>
.imgf {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem;
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  background: var(--surface-2);
}
.imgf--stack { flex-direction: column; align-items: stretch; text-align: center; }
.imgf--stack .imgf-thumb { align-self: center; }
.imgf--stack .imgf-actions { justify-content: center; }

.imgf-thumb {
  position: relative;
  flex-shrink: 0;
  max-width: 100%;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--border-strong);
  border-radius: var(--r-sm);
  background: rgb(var(--ink) / 0.05);
  color: var(--text-faint);
  cursor: pointer;
}
.imgf-thumb img { display: block; width: 100%; height: 100%; object-fit: cover; }
.imgf-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.3rem;
  width: 100%; height: 100%; padding: 0.5rem;
  font-size: 0.68rem; line-height: 1.3; text-align: center;
}
.imgf-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center; gap: 0.3rem;
  background: rgb(0 0 0 / 0.55); color: #fff;
  font-size: 0.72rem; font-weight: 600;
  opacity: 0; transition: opacity 0.15s;
}
.imgf-thumb:hover .imgf-overlay, .imgf-thumb:focus-visible .imgf-overlay { opacity: 1; }
@media (hover: none) { .imgf-overlay { display: none; } }

.imgf-side { display: flex; flex-direction: column; gap: 0.5rem; flex: 1; min-width: 0; }
.imgf-url {
  margin: 0; padding: 0.45rem 0.65rem;
  border: 1px solid var(--border); border-radius: var(--r-sm);
  background: rgb(var(--ink) / 0.03); color: var(--text-dim);
  font-size: 0.7rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.imgf-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }

@media (max-width: 480px) {
  .imgf { flex-direction: column; align-items: stretch; }
  .imgf-thumb { align-self: center; }
  .imgf-actions .adm-btn { flex: 1; }
}
</style>