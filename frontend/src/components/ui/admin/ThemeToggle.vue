<template>
  <!-- Switch tema admin. Taruh di AdminSidebar (footer) — lihat catatan di bawah.
       variant="row"  → baris penuh: ikon + label + switch (sidebar terbuka / drawer mobile)
       variant="icon" → tombol ikon kecil (sidebar ciut / top bar mobile) -->
  <button
    type="button"
    role="switch"
    class="tt"
    :class="[`tt--${variant}`, { 'is-dark': isDark }]"
    :aria-checked="isDark"
    :aria-label="`Mode gelap ${isDark ? 'aktif' : 'nonaktif'}. Klik untuk pindah ke mode ${isDark ? 'terang' : 'gelap'}`"
    :title="isDark ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'"
    @click="toggleTheme"
  >
    <template v-if="variant === 'row'">
      <span class="tt-lead">
        <span class="tt-icon" aria-hidden="true">
          <Moon v-if="isDark" :size="16" />
          <Sun v-else :size="16" />
        </span>
        <span class="tt-text">
          <span class="tt-label">Tampilan</span>
          <span class="tt-value">{{ isDark ? 'Mode gelap' : 'Mode terang' }}</span>
        </span>
      </span>

      <span class="tt-track" aria-hidden="true">
        <Sun :size="12" class="tt-glyph tt-glyph--sun" />
        <Moon :size="12" class="tt-glyph tt-glyph--moon" />
        <span class="tt-thumb" />
      </span>
    </template>

    <template v-else>
      <Moon v-if="isDark" :size="17" aria-hidden="true" />
      <Sun v-else :size="17" aria-hidden="true" />
    </template>
  </button>
</template>

<script setup>
import { Sun, Moon } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'

defineProps({
  variant: { type: String, default: 'row', validator: (v) => ['row', 'icon'].includes(v) },
})

const { isDark, toggleTheme } = useTheme()
</script>

<style scoped>
.tt {
  font-family: var(--font-body, 'Inter', system-ui, sans-serif);
  color: var(--text-2);
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.tt:hover { background: var(--surface-hover); color: var(--text); }

/* ── Row ── */
.tt--row {
  display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
  width: 100%; min-height: 48px; padding: 0.55rem 0.65rem;
  border-radius: var(--r-md); text-align: left;
}
.tt-lead { display: flex; align-items: center; gap: 0.65rem; min-width: 0; }
.tt-icon {
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 32px; height: 32px; border-radius: var(--r-sm);
  background: rgb(var(--ink) / 0.06); color: var(--amber-soft);
}
.tt.is-dark .tt-icon { color: var(--blue-soft); }
.tt-text { display: flex; flex-direction: column; min-width: 0; line-height: 1.25; }
.tt-label { font-size: 0.66rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint); }
.tt-value { font-size: 0.8125rem; font-weight: 600; color: var(--text); white-space: nowrap; }

/* switch track: ikon matahari (kiri) & bulan (kanan), thumb geser */
.tt-track {
  position: relative; flex-shrink: 0; width: 48px; height: 26px;
  border: 1px solid var(--border-strong); border-radius: 99px;
  background: rgb(var(--ink) / 0.08);
  transition: background 0.2s, border-color 0.2s;
}
.tt.is-dark .tt-track { background: rgb(var(--ink) / 0.14); }
.tt-glyph { position: absolute; top: 50%; transform: translateY(-50%); color: var(--text-faint); }
.tt-glyph--sun  { left: 6px; }
.tt-glyph--moon { right: 6px; }
.tt-thumb {
  position: absolute; top: 2px; left: 2px; width: 20px; height: 20px; border-radius: 50%;
  background: var(--amber); box-shadow: 0 1px 3px rgb(0 0 0 / 0.3);
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1), background 0.2s;
}
.tt.is-dark .tt-thumb { transform: translateX(22px); background: var(--text); }
.tt:not(.is-dark) .tt-glyph--sun,
.tt.is-dark .tt-glyph--moon { color: var(--bg); z-index: 1; }   /* ikon yang "tertutup" thumb tetap kebaca */
.tt:not(.is-dark) .tt-glyph--sun { color: #fff; }

/* ── Icon ── */
.tt--icon {
  display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 40px; height: 40px; padding: 0; border-radius: var(--r-md);
  border-color: var(--border); color: var(--text-dim);
}
.tt--icon svg { transition: transform 0.25s; }
.tt--icon:hover svg { transform: rotate(15deg); }

@media (prefers-reduced-motion: reduce) {
  .tt-thumb, .tt--icon svg { transition: none; }
}
</style>