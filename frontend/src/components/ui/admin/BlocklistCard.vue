<template>
  <section class="adm-card bl-card" aria-labelledby="bl-title">
    <!-- ── Kepala kartu ───────────────────────────────────────────────────── -->
    <div class="adm-card-head">
      <div class="adm-card-icon tone-accent"><ShieldAlert :size="18" /></div>
      <div class="adm-card-head-main">
        <h2 id="bl-title" class="adm-card-title">Daftar Blokir Anti-Scam</h2>
        <p class="adm-card-desc">
          Nomor WhatsApp dan IP yang diblokir dari pesanan web. Sama dengan daftar di Telegram
          (<code class="bl-code">/blokir</code>, <code class="bl-code">/bukablokir</code>, <code class="bl-code">/daftarblokir</code>):
          perubahan dari sini dan dari Telegram saling terlihat.
        </p>
      </div>
      <div class="adm-card-head-actions">
        <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" :disabled="loading || forbidden" @click="fetchList(); showAttempts && fetchAttempts()">
          <RefreshCw :size="13" :class="{ 'bl-spin': loading }" /> Muat ulang
        </button>
      </div>
    </div>

    <!-- ── Bukan owner ────────────────────────────────────────────────────── -->
    <div v-if="forbidden" class="adm-empty">
      <div class="adm-empty-icon"><Lock :size="22" /></div>
      <p class="adm-empty-title">Hanya untuk owner</p>
      <p class="adm-empty-text">Daftar blokir berisi nomor HP dan IP pelanggan, jadi hanya owner yang bisa melihat dan mengubahnya.</p>
    </div>

    <div v-else class="adm-card-body">
      <!-- ── Ringkasan ────────────────────────────────────────────────────── -->
      <div class="bl-stats" role="group" aria-label="Ringkasan daftar blokir">
        <div class="bl-stat">
          <p class="bl-stat-value">{{ summary ? summary.active : '–' }}</p>
          <p class="bl-stat-label">Blokir aktif</p>
        </div>
        <div class="bl-stat">
          <p class="bl-stat-value">{{ summary ? summary.phone : '–' }}</p>
          <p class="bl-stat-label">Nomor WA <span class="bl-faint">· ditolak total</span></p>
        </div>
        <div class="bl-stat">
          <p class="bl-stat-value">{{ summary ? summary.ip : '–' }}</p>
          <p class="bl-stat-label">IP <span class="bl-faint">· dipaksa QRIS</span></p>
        </div>
        <div class="bl-stat" :class="{ 'is-warn': summary && summary.ip_expiring_soon > 0 }">
          <p class="bl-stat-value">{{ summary ? summary.ip_expiring_soon : '–' }}</p>
          <p class="bl-stat-label">IP segera berakhir <span class="bl-faint">· ≤ {{ expiringDays }} hari</span></p>
        </div>
        <div class="bl-stat" :class="{ 'is-danger': summary && summary.attempts_7d > 0 }">
          <p class="bl-stat-value">{{ summary ? summary.attempts_7d : '–' }}</p>
          <p class="bl-stat-label">Percobaan terblokir <span class="bl-faint">· 7 hari</span></p>
        </div>
      </div>

      <!-- ── Percobaan order dari kontak terblokir ─────────────────────────── -->
      <section class="bl-attempts" aria-labelledby="bl-att-title">
        <button type="button" class="bl-att-head" :aria-expanded="showAttempts" aria-controls="bl-att-body" @click="toggleAttempts">
          <span class="bl-att-title" id="bl-att-title"><ShieldAlert :size="15" /> Percobaan order setelah diblokir</span>
          <span class="bl-faint bl-att-sub">Siapa yang masih mencoba, dari mana, dan IP barunya</span>
          <ChevronDown :size="16" class="bl-chev" :class="{ 'is-open': showAttempts }" aria-hidden="true" />
        </button>
        <div v-if="showAttempts" id="bl-att-body" class="bl-att-body">
          <div class="adm-seg" role="group" aria-label="Rentang waktu percobaan">
            <button v-for="d in ATTEMPT_DAYS" :key="d" type="button" class="adm-seg-btn" :aria-pressed="attemptDays === d" @click="setAttemptDays(d)">{{ d }} hari</button>
          </div>
          <p v-if="attemptsLoading && !attempts.length" class="adm-hint">Memuat…</p>
          <p v-else-if="attemptsError" class="adm-hint bl-err">{{ attemptsError }}</p>
          <p v-else-if="!attempts.length" class="adm-hint">Tidak ada percobaan dalam {{ attemptDays }} hari terakhir. Blokir bekerja dan belum ada yang mencoba lagi.</p>
          <ul v-else class="bl-att-list">
            <li v-for="a in attempts" :key="a.id" class="bl-att">
              <div class="bl-att-top">
                <span class="adm-badge" :class="a.kind === 'ip' ? 'adm-badge--amber' : 'adm-badge--red'">{{ a.kind === 'ip' ? 'IP → dipaksa QRIS' : 'Nomor → ditolak' }}</span>
                <span class="bl-faint">{{ fmt(a.created_at) }} · {{ ago(a.created_at) }}</span>
              </div>
              <dl class="bl-order-meta">
                <div><dt>Nama</dt><dd>{{ a.name || '–' }}</dd></div>
                <div><dt>Nomor WA</dt><dd class="adm-mono">{{ a.phone || '–' }}</dd></div>
                <div><dt>IP</dt><dd class="adm-mono">{{ a.ip || '–' }}
                  <span v-if="a.ip && a.ip_blocked" class="adm-badge adm-badge--red">sudah diblokir</span>
                  <span v-else-if="a.ip" class="adm-badge adm-badge--amber">IP baru</span>
                </dd></div>
                <div><dt>Lokasi (perkiraan)</dt><dd>{{ a.location_text || '–' }}
                  <a v-if="a.maps_url" :href="a.maps_url" target="_blank" rel="noopener noreferrer" class="bl-link">Google Maps <ExternalLink :size="11" /></a>
                </dd></div>
                <div class="bl-meta-wide"><dt>Perangkat</dt><dd>{{ a.device || '–' }} <span v-if="a.bot" class="adm-badge adm-badge--amber">Mirip bot</span></dd></div>
              </dl>
              <div class="bl-att-actions">
                <button v-if="a.ip && !a.ip_blocked" type="button" class="adm-btn adm-btn--soft adm-btn--sm" :disabled="blockingIp.has(a.ip)" @click="blockAttemptIp(a)">
                  <span v-if="blockingIp.has(a.ip)" class="adm-spinner"></span><Ban v-else :size="13" /> Blokir IP ini
                </button>
                <button v-if="a.phone" type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="query = a.phone">
                  <Search :size="13" /> Lihat nomor ini
                </button>
              </div>
            </li>
          </ul>
        </div>
      </section>

      <!-- ── Cara kerja ───────────────────────────────────────────────────── -->
      <div class="bl-note">
        <Info :size="15" class="bl-note-icon" />
        <ul>
          <li><strong>Nomor WA</strong>: pesanan web dari nomor ini ditolak total. Berlaku sampai dibuka manual.</li>
          <li>
            <strong>IP</strong>: pesanan cash dari IP ini dipaksa bayar QRIS, tidak ditolak, karena satu IP bisa dipakai banyak orang
            (WiFi kafe, kampus, data seluler). Blokir IP berakhir sendiri setelah <strong>{{ ipDays }} hari</strong> karena IP sering berganti pemilik.
          </li>
          <li>Pesanan dari kasir (POS) tidak terpengaruh blokir. Pesanan yang sudah masuk juga tidak dibatalkan otomatis.</li>
        </ul>
      </div>

      <!-- ── Tambah manual ────────────────────────────────────────────────── -->
      <form class="bl-add" novalidate @submit.prevent="addBlock">
        <p class="bl-add-title"><Plus :size="14" /> Blokir manual</p>
        <div class="bl-add-grid">
          <div class="adm-field">
            <label class="adm-label" for="bl-target">Nomor WA atau IP <span class="adm-req">*</span></label>
            <input
              id="bl-target"
              v-model="target"
              type="text"
              inputmode="text"
              autocomplete="off"
              spellcheck="false"
              class="adm-input adm-input--mono"
              placeholder="0812… atau 114.122…"
              maxlength="64"
              :disabled="adding"
              aria-describedby="bl-target-help"
            />
          </div>
          <div class="adm-field">
            <label class="adm-label" for="bl-reason">Alasan <span class="adm-opt">(opsional)</span></label>
            <input
              id="bl-reason"
              v-model="reason"
              type="text"
              autocomplete="off"
              class="adm-input"
              placeholder="Mis. order fiktif berulang"
              maxlength="255"
              :disabled="adding"
            />
          </div>
          <button type="submit" class="adm-btn adm-btn--primary bl-add-btn" :disabled="adding || !detected">
            <span v-if="adding" class="adm-spinner"></span>
            <Ban v-else :size="15" />
            {{ adding ? 'Memblokir…' : 'Blokir' }}
          </button>
        </div>
        <p id="bl-target-help" class="adm-hint bl-detect" aria-live="polite">
          <template v-if="!target.trim()">Format nomor bebas: <code class="bl-code">0812-3456-7890</code>, <code class="bl-code">+62 812 3456 7890</code>, atau <code class="bl-code">6281234567890</code>.</template>
          <template v-else-if="detected">
            Terdeteksi: <strong>{{ detected.kind === 'ip' ? 'IP' : 'Nomor WA' }}</strong>
            <span class="adm-mono">{{ detected.value }}</span>
            · {{ detected.kind === 'ip' ? 'pesanan cash dipaksa QRIS' : 'pesanan web ditolak total' }}
          </template>
          <template v-else>Belum dikenali sebagai nomor WA (9–15 digit) maupun alamat IP.</template>
        </p>
      </form>

      <!-- ── Filter ───────────────────────────────────────────────────────── -->
      <div class="adm-toolbar bl-toolbar">
        <div class="adm-seg" role="group" aria-label="Tampilan daftar">
          <button v-for="v in VIEWS" :key="v.value" type="button" class="adm-seg-btn" :aria-pressed="view === v.value" @click="view = v.value">
            {{ v.label }}<span v-if="viewCount(v.value) !== null" class="bl-seg-count">{{ viewCount(v.value) }}</span>
          </button>
        </div>
        <div class="adm-seg" role="group" aria-label="Jenis blokir">
          <button v-for="k in KINDS" :key="k.value" type="button" class="adm-seg-btn" :aria-pressed="kind === k.value" @click="kind = k.value">
            {{ k.label }}
          </button>
        </div>
        <div class="adm-search">
          <Search :size="15" class="adm-search-icon" />
          <input v-model="query" type="search" class="adm-input" placeholder="Cari nomor, IP, alasan…" aria-label="Cari di daftar blokir" />
          <button v-if="query" type="button" class="adm-search-clear" aria-label="Hapus pencarian" @click="query = ''"><X :size="14" /></button>
        </div>
      </div>

      <!-- ── Daftar ───────────────────────────────────────────────────────── -->
      <div aria-live="polite">
        <ul v-if="loading && !items.length" class="bl-list" aria-busy="true">
          <li v-for="n in 3" :key="n" class="bl-item">
            <span class="adm-skel" style="height: 16px; width: 40%"></span>
            <span class="adm-skel" style="height: 12px; width: 85%; margin-top: 12px"></span>
            <span class="adm-skel" style="height: 12px; width: 65%; margin-top: 8px"></span>
          </li>
        </ul>

        <div v-else-if="loadError" class="adm-empty">
          <div class="adm-empty-icon"><AlertTriangle :size="22" /></div>
          <p class="adm-empty-title">Gagal memuat daftar blokir</p>
          <p class="adm-empty-text">{{ loadError }}</p>
          <button type="button" class="adm-btn adm-btn--primary" @click="fetchList()">Coba lagi</button>
        </div>

        <div v-else-if="!items.length" class="adm-empty">
          <div class="adm-empty-icon"><component :is="hasFilter ? Search : ShieldCheck" :size="22" /></div>
          <p class="adm-empty-title">{{ emptyTitle }}</p>
          <p class="adm-empty-text">{{ emptyText }}</p>
        </div>

        <ul v-else class="bl-list" :class="{ 'is-refreshing': loading }">
          <li v-for="it in items" :key="it.id" class="bl-item" :class="`is-${it.status}`">
            <div class="bl-item-top">
              <span class="bl-kind" :class="it.kind === 'ip' ? 'tone-blue' : 'tone-purple'" aria-hidden="true">
                <component :is="it.kind === 'ip' ? Globe : Phone" :size="16" />
              </span>
              <div class="bl-id">
                <p class="bl-value adm-mono">{{ it.value }}</p>
                <p class="bl-sub">
                  {{ it.kind_label }}
                  <template v-if="it.names.length"> · Pemesan: {{ it.names.join(', ') }}</template>
                </p>
              </div>
              <div class="bl-badges">
                <span v-if="it.status === 'active'" class="adm-badge adm-badge--red">Diblokir</span>
                <span v-else-if="it.status === 'expired'" class="adm-badge">Kedaluwarsa</span>
                <span v-else class="adm-badge adm-badge--green">Dibuka</span>
                <span v-if="it.expiring_soon" class="adm-badge adm-badge--amber"><Clock :size="11" /> {{ it.days_left }} hari lagi</span>
              </div>
            </div>

            <dl class="bl-meta">
              <div class="bl-meta-wide">
                <dt>Dampak</dt>
                <dd>{{ it.effect }}</dd>
              </div>
              <div>
                <dt>Alasan</dt>
                <dd>{{ it.reason || '–' }}</dd>
              </div>
              <div>
                <dt>Diblokir oleh</dt>
                <dd>{{ it.blocked_by || '–' }}</dd>
              </div>
              <div>
                <dt>Waktu blokir</dt>
                <dd>{{ fmt(it.blocked_at) }} <span class="bl-faint">· {{ ago(it.blocked_at) }}</span></dd>
              </div>
              <div>
                <dt>Masa berlaku</dt>
                <dd>{{ validity(it) }}</dd>
              </div>
              <div>
                <dt>Order pemicu</dt>
                <dd><span v-if="it.order_number" class="adm-mono">{{ it.order_number }}</span><template v-else>Diblokir manual</template></dd>
              </div>
              <div>
                <dt>Pesanan dari {{ it.kind === 'ip' ? 'IP' : 'nomor' }} ini</dt>
                <dd>
                  <template v-if="it.order_count">{{ it.order_count }} pesanan <span class="bl-faint">· terakhir {{ fmt(it.last_order_at) }}</span></template>
                  <template v-else>Belum ada</template>
                </dd>
              </div>
            </dl>

            <div class="bl-trace">
              <p class="bl-trace-title"><MapPin :size="12" /> Jejak asal <span class="bl-faint">· perkiraan dari IP, bukan alamat rumah</span></p>
              <dl class="bl-meta bl-meta--trace">
                <div>
                  <dt>Perkiraan lokasi</dt>
                  <dd>
                    <template v-if="it.location && it.location.text">
                      {{ it.location.text }}
                      <a v-if="it.location.maps_url" :href="it.location.maps_url" target="_blank" rel="noopener noreferrer" class="bl-link">Lihat peta <ExternalLink :size="11" /></a>
                    </template>
                    <template v-else>–</template>
                  </dd>
                </div>
                <div>
                  <dt>Perangkat</dt>
                  <dd>
                    {{ (it.location && it.location.device) || '–' }}
                    <span v-if="it.location && it.location.bot" class="adm-badge adm-badge--amber">Mirip bot</span>
                  </dd>
                </div>
                <div>
                  <dt>Dari order</dt>
                  <dd>
                    <template v-if="it.location_order_number">
                      <span class="adm-mono">{{ it.location_order_number }}</span>
                      <span class="bl-faint">· {{ fmt(it.location_at) }}</span>
                    </template>
                    <template v-else>Belum ada order, jadi lokasi belum diketahui</template>
                  </dd>
                </div>
                <div v-if="it.other_locations && it.other_locations.length" class="bl-meta-wide">
                  <dt>Lokasi lain yang pernah terbaca</dt>
                  <dd>{{ it.other_locations.join(' · ') }}</dd>
                </div>
                <div v-if="it.related && it.related.length" class="bl-meta-wide">
                  <dt>{{ it.related_label }}</dt>
                  <dd class="adm-mono">{{ it.related.join(', ') }}</dd>
                </div>
              </dl>
            </div>

            <details v-if="it.recent_orders && it.recent_orders.length" class="bl-orders" :open="it.recent_orders.length <= 2">
              <summary class="bl-orders-sum">
                <ListOrdered :size="13" /> Pesanan terakhir
                <span class="bl-faint">· {{ it.recent_orders.length }} dari {{ it.order_count }}</span>
              </summary>
              <ul class="bl-order-list">
                <li v-for="o in it.recent_orders" :key="o.id" class="bl-order">
                  <div class="bl-order-top">
                    <router-link :to="orderLink(o)" class="bl-order-no adm-mono">{{ o.order_number }}</router-link>
                    <span class="adm-badge" :class="statusTone(o)">{{ o.status_label }}</span>
                    <span class="bl-faint">{{ fmt(o.created_at) }}</span>
                  </div>
                  <dl class="bl-order-meta">
                    <div><dt>Nama</dt><dd>{{ o.name || '–' }}</dd></div>
                    <div><dt>Nomor WA</dt><dd class="adm-mono">{{ o.phone || '–' }}</dd></div>
                    <div><dt>IP</dt><dd class="adm-mono">{{ o.ip || '–' }}</dd></div>
                    <div><dt>Total</dt><dd>{{ rupiah(o.total) }}</dd></div>
                    <div class="bl-meta-wide"><dt>Lokasi (perkiraan dari IP)</dt>
                      <dd>{{ o.location_text || '–' }}
                        <a v-if="o.maps_url" :href="o.maps_url" target="_blank" rel="noopener noreferrer" class="bl-link">Google Maps <ExternalLink :size="11" /></a>
                      </dd>
                    </div>
                    <div v-if="o.device" class="bl-meta-wide"><dt>Perangkat</dt><dd>{{ o.device }}</dd></div>
                  </dl>
                </li>
              </ul>
            </details>

            <details v-if="it.attempts && it.attempts.length" class="bl-orders bl-orders--warn">
              <summary class="bl-orders-sum">
                <ShieldAlert :size="13" /> Percobaan setelah diblokir
                <span class="bl-faint">· {{ it.attempt_count }} kali, terakhir {{ ago(it.last_attempt_at) }}</span>
              </summary>
              <ul class="bl-order-list">
                <li v-for="a in it.attempts" :key="a.id" class="bl-order">
                  <div class="bl-order-top"><span>{{ fmt(a.created_at) }}</span><span class="bl-faint">{{ a.name || 'tanpa nama' }}</span></div>
                  <dl class="bl-order-meta">
                    <div><dt>Nomor WA</dt><dd class="adm-mono">{{ a.phone || '–' }}</dd></div>
                    <div><dt>IP</dt><dd class="adm-mono">{{ a.ip || '–' }}</dd></div>
                    <div class="bl-meta-wide"><dt>Lokasi (perkiraan)</dt>
                      <dd>{{ a.location_text || '–' }}
                        <a v-if="a.maps_url" :href="a.maps_url" target="_blank" rel="noopener noreferrer" class="bl-link">Google Maps <ExternalLink :size="11" /></a>
                      </dd>
                    </div>
                  </dl>
                </li>
              </ul>
            </details>

            <div class="bl-actions">
              <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="copy(it.value)">
                <Copy :size="13" /> Salin
              </button>
              <button
                v-if="it.status === 'active'"
                type="button"
                class="adm-btn adm-btn--ghost adm-btn--sm"
                :disabled="busy.has(it.id)"
                @click="unblock(it)"
              >
                <span v-if="busy.has(it.id)" class="adm-spinner"></span>
                <RotateCcw v-else :size="13" /> Buka blokir
              </button>
              <button
                v-else
                type="button"
                class="adm-btn adm-btn--soft adm-btn--sm"
                :disabled="busy.has(it.id)"
                @click="reblock(it)"
              >
                <span v-if="busy.has(it.id)" class="adm-spinner"></span>
                <Ban v-else :size="13" /> Blokir lagi
              </button>
            </div>
          </li>
        </ul>

        <p v-if="items.length && limitNote" class="adm-hint bl-limit">{{ limitNote }}</p>
      </div>
    </div>

    <AdminConfirm :state="confirmState" @confirm="acceptConfirm" @cancel="cancelConfirm" />
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { toast } from 'vue-sonner'
import {
  ShieldAlert, ShieldCheck, Info, Plus, Ban, Search, X, Phone, Globe, Clock,
  Copy, RotateCcw, RefreshCw, AlertTriangle, Lock, MapPin, ExternalLink, ChevronDown, ListOrdered,
} from 'lucide-vue-next'
import { blocklistAPI } from '@/api/order'
import { useAdminConfirm } from '@/composables/useAdminConfirm'
import { useRouteSearch } from '@/composables/useRouteSearch'
import AdminConfirm from '@/components/ui/admin/Adminconfirm.vue'

const { state: confirmState, ask, accept: acceptConfirm, cancel: cancelConfirm } = useAdminConfirm()

const VIEWS = [
  { value: 'active', label: 'Aktif' },
  { value: 'history', label: 'Riwayat' },
  { value: 'all', label: 'Semua' },
]
const KINDS = [
  { value: '', label: 'Semua jenis' },
  { value: 'phone', label: 'Nomor WA' },
  { value: 'ip', label: 'IP' },
]
const HISTORY_LIMIT = 100   // sama dengan HISTORY_LIMIT di backend
const LIST_LIMIT = 500      // sama dengan LIST_LIMIT di backend

const view = ref('active')
const kind = ref('')
const query = ref('')
useRouteSearch(query) // ?q=<nomor|IP> dari pencarian global Ctrl+K supaya langsung tersaring
const items = ref([])
const summary = ref(null)
const loading = ref(false)
const loadError = ref('')
const forbidden = ref(false)
const busy = ref(new Set())

const target = ref('')
const reason = ref('')
const adding = ref(false)

const ipDays = computed(() => summary.value?.ip_block_days ?? 90)
const expiringDays = computed(() => summary.value?.expiring_soon_days ?? 14)
const hasFilter = computed(() => !!query.value.trim() || !!kind.value)

const viewCount = (v) => {
  if (!summary.value) return null
  if (v === 'active') return summary.value.active
  if (v === 'history') return summary.value.history
  return summary.value.active + summary.value.history
}

// ── Pengenalan input (hanya untuk pratinjau; server tetap yang memvalidasi) ──────────────
const IPV4 = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/
const detect = (raw) => {
  const t = String(raw || '').trim()
  if (!t) return null
  if (IPV4.test(t)) return { kind: 'ip', value: t }
  if (t.includes(':') && /^[0-9a-f:.]+$/i.test(t)) return { kind: 'ip', value: t.toLowerCase() }
  if (!/^[\d\s+\-().]+$/.test(t)) return null
  let digits = t.replace(/\D/g, '')
  if (digits.startsWith('62')) digits = '0' + digits.slice(2)
  else if (digits.startsWith('8')) digits = '0' + digits
  return digits.length >= 9 && digits.length <= 15 ? { kind: 'phone', value: digits } : null
}
const detected = computed(() => detect(target.value))

// ── Format tanggal (WIB) ─────────────────────────────────────────────────────────────────
const dtf = new Intl.DateTimeFormat('id-ID', {
  timeZone: 'Asia/Jakarta', day: 'numeric', month: 'short', year: 'numeric',
  hour: '2-digit', minute: '2-digit', hour12: false,
})
const fmt = (iso) => (iso ? `${dtf.format(new Date(iso))} WIB` : '–')
const rupiah = (v) => 'Rp ' + Math.round(Number(v) || 0).toLocaleString('id-ID')
const wibDay = (iso) => new Date(iso).toLocaleDateString('en-CA', { timeZone: 'Asia/Jakarta' })   // YYYY-MM-DD
// Tautan ke pesanan di halaman Pesanan (tanggal + nomor order, sama dengan hasil pencarian global).
const orderLink = (o) => `/admin/orders?date=${wibDay(o.created_at)}&q=${encodeURIComponent(o.order_number)}`
const statusTone = (o) => {
  if (o.status_label === 'Selesai') return 'adm-badge--green'
  if (o.status_label === 'Dibatalkan' || o.status_label === 'Batal otomatis') return 'adm-badge--red'
  return 'adm-badge--amber'
}

const ago = (iso) => {
  if (!iso) return ''
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 1) return 'baru saja'
  if (mins < 60) return `${mins} menit lalu`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} jam lalu`
  const days = Math.floor(hours / 24)
  return days < 60 ? `${days} hari lalu` : `${Math.floor(days / 30)} bulan lalu`
}

const validity = (it) => {
  if (it.status === 'lifted') return `Dibuka ${fmt(it.unblocked_at)}`
  if (it.kind === 'phone') return 'Tanpa batas waktu, sampai dibuka manual'
  if (it.status === 'expired') return `Berakhir ${fmt(it.expires_at)}`
  return `Sampai ${fmt(it.expires_at)} (${it.days_left} hari lagi)`
}

// ── Teks kosong & catatan batas ──────────────────────────────────────────────────────────
const emptyTitle = computed(() => {
  if (hasFilter.value) return 'Tidak ada yang cocok'
  if (view.value === 'history') return 'Belum ada riwayat'
  return 'Daftar blokir kosong'
})
const emptyText = computed(() => {
  if (hasFilter.value) return 'Ubah kata kunci atau filter jenis, atau pindah ke tab Riwayat / Semua.'
  if (view.value === 'history') return 'Blokir yang dibuka atau kedaluwarsa akan tercatat di sini.'
  return 'Belum ada nomor atau IP yang diblokir. Blokir bisa dibuat dari tombol di notifikasi Telegram atau lewat form di atas.'
})
const limitNote = computed(() => {
  if (view.value === 'history' && items.value.length >= HISTORY_LIMIT) return `Menampilkan ${HISTORY_LIMIT} riwayat terbaru.`
  if (view.value !== 'history' && items.value.length >= LIST_LIMIT) return `Menampilkan ${LIST_LIMIT} blokir terbaru. Persempit dengan pencarian.`
  return ''
})

// ── Pengambilan data ─────────────────────────────────────────────────────────────────────
let seq = 0
const errText = (e, fallback) => e?.response?.data?.detail || (e?.response ? fallback : 'Periksa koneksi lalu coba lagi.')

async function fetchList() {
  const mine = ++seq                       // abaikan respons lama kalau filter sudah berganti
  loading.value = true
  loadError.value = ''
  try {
    const params = { view: view.value }
    if (kind.value) params.kind = kind.value
    if (query.value.trim()) params.q = query.value.trim()
    const { data } = await blocklistAPI.list(params)
    if (mine !== seq) return
    items.value = data.results || []
    summary.value = data.summary || null
  } catch (e) {
    if (mine !== seq) return
    if (e?.response?.status === 403) forbidden.value = true
    else loadError.value = errText(e, 'Server menolak permintaan ini.')
    items.value = []
  } finally {
    if (mine === seq) loading.value = false
  }
}

let timer = null
watch([view, kind], () => fetchList())
watch(query, () => {
  clearTimeout(timer)
  timer = setTimeout(fetchList, 300)
})
onMounted(fetchList)
onBeforeUnmount(() => clearTimeout(timer))

// ── Percobaan order setelah diblokir ─────────────────────────────────────────────────────
const ATTEMPT_DAYS = [7, 30, 90]
const showAttempts = ref(false)
const attemptDays = ref(7)
const attempts = ref([])
const attemptsLoading = ref(false)
const attemptsError = ref('')
const blockingIp = ref(new Set())
let attemptSeq = 0

async function fetchAttempts() {
  const mine = ++attemptSeq
  attemptsLoading.value = true
  attemptsError.value = ''
  try {
    const { data } = await blocklistAPI.attempts({ days: attemptDays.value })
    if (mine !== attemptSeq) return
    attempts.value = data.results || []
  } catch (e) {
    if (mine !== attemptSeq) return
    attemptsError.value = errText(e, 'Gagal memuat percobaan.')
    attempts.value = []
  } finally {
    if (mine === attemptSeq) attemptsLoading.value = false
  }
}
function toggleAttempts() {
  showAttempts.value = !showAttempts.value
  if (showAttempts.value) fetchAttempts()
}
function setAttemptDays(d) {
  attemptDays.value = d
  fetchAttempts()
}
async function blockAttemptIp(a) {
  const next = new Set(blockingIp.value)
  next.add(a.ip)
  blockingIp.value = next
  try {
    const { data } = await blocklistAPI.add(a.ip, `Percobaan dari nomor terblokir ${a.phone || ''}`.trim())
    data.created ? toast.success(data.message) : toast.info(data.message)
    await Promise.all([fetchAttempts(), fetchList()])
  } catch (e) {
    toast.error(errText(e, 'Gagal memblokir IP.'))
  } finally {
    const done = new Set(blockingIp.value)
    done.delete(a.ip)
    blockingIp.value = done
  }
}

// ── Aksi ─────────────────────────────────────────────────────────────────────────────────
const setBusy = (id, on) => {
  const next = new Set(busy.value)
  on ? next.add(id) : next.delete(id)
  busy.value = next
}

async function addBlock() {
  if (!detected.value || adding.value) return
  adding.value = true
  try {
    const { data } = await blocklistAPI.add(target.value.trim(), reason.value.trim())
    data.created ? toast.success(data.message) : toast.info(data.message)
    target.value = ''
    reason.value = ''
    if (view.value === 'history') view.value = 'active'   // watcher memuat ulang
    else await fetchList()
  } catch (e) {
    toast.error(errText(e, 'Gagal memblokir.'))
  } finally {
    adding.value = false
  }
}

async function unblock(it) {
  const what = it.kind === 'ip' ? `IP ${it.value}` : `nomor ${it.value}`
  const ok = await ask({
    title: `Buka blokir ${what}?`,
    message: it.kind === 'ip'
      ? 'Pesanan cash dari IP ini tidak lagi dipaksa bayar QRIS. Bisa diblokir lagi kapan saja.'
      : 'Nomor ini bisa memesan lewat web lagi. Bisa diblokir lagi kapan saja.',
    confirmText: 'Ya, buka blokir',
    danger: true,
  })
  if (!ok) return
  setBusy(it.id, true)
  try {
    const { data } = await blocklistAPI.unblock(it.id)
    toast.success(data.message)
    await fetchList()
  } catch (e) {
    toast.error(errText(e, 'Gagal membuka blokir.'))
  } finally {
    setBusy(it.id, false)
  }
}

async function reblock(it) {
  setBusy(it.id, true)
  try {
    const { data } = await blocklistAPI.add(it.value, it.reason || '')
    toast.success(data.message)
    await fetchList()
  } catch (e) {
    toast.error(errText(e, 'Gagal memblokir ulang.'))
  } finally {
    setBusy(it.id, false)
  }
}

async function copy(value) {
  try {
    await navigator.clipboard.writeText(value)
    toast.success('Disalin')
  } catch {
    toast.error('Tidak bisa menyalin, salin manual dari layar.')
  }
}
</script>

<style scoped>
.bl-faint { color: var(--text-faint); font-weight: 400; }
.bl-code {
  padding: 1px 6px; border-radius: 4px;
  background: rgb(var(--ink) / 0.07); color: var(--text-2);
  font-family: var(--font-mono); font-size: 0.75rem; white-space: nowrap;
}
.bl-spin { animation: bl-spin 0.9s linear infinite; }
@keyframes bl-spin { to { transform: rotate(360deg); } }

/* ── Ringkasan ─────────────────────────────────────────────────── */
.bl-stats { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0.65rem; }
.bl-stat {
  padding: 0.8rem 0.95rem; min-width: 0;
  border: 1px solid var(--border); border-radius: var(--r-md);
  background: rgb(var(--ink) / 0.03);
}
.bl-stat.is-warn { background: var(--tint-amber); border-color: var(--line-amber); }
.bl-stat.is-danger { background: var(--tint-red, rgb(220 38 38 / 0.1)); border-color: var(--line-red, rgb(220 38 38 / 0.4)); }
.bl-stat-value {
  margin: 0; font-family: var(--font-display); font-size: 1.4rem; font-weight: 700; line-height: 1;
  color: var(--text); font-variant-numeric: tabular-nums;
}
.bl-stat-label { margin: 0.35rem 0 0; font-size: 0.78rem; line-height: 1.4; color: var(--text-dim); }

/* ── Catatan cara kerja ────────────────────────────────────────── */
.bl-note {
  display: flex; align-items: flex-start; gap: 0.65rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--line-blue); border-radius: var(--r-md); background: var(--tint-blue);
}
.bl-note-icon { flex-shrink: 0; margin-top: 2px; color: var(--blue-soft); }
.bl-note ul { margin: 0; padding-left: 1.05rem; display: flex; flex-direction: column; gap: 0.3rem; }
.bl-note li { font-size: 0.78rem; line-height: 1.6; color: var(--text-dim); }
.bl-note strong { color: var(--text); }

/* ── Form tambah ───────────────────────────────────────────────── */
.bl-add {
  display: flex; flex-direction: column; gap: 0.6rem;
  padding: 0.9rem 1rem; border: 1px dashed var(--border-strong); border-radius: var(--r-md);
}
.bl-add-title {
  display: flex; align-items: center; gap: 0.4rem; margin: 0;
  font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-faint);
}
.bl-add-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto; gap: 0.75rem; align-items: end; }
.bl-add-btn { min-height: 42px; }
.bl-detect { margin: 0; }
.bl-detect strong { color: var(--text); }

/* ── Filter ────────────────────────────────────────────────────── */
.bl-toolbar .adm-search { flex: 1 1 16rem; max-width: none; }
.bl-seg-count {
  min-width: 1.25rem; padding: 0 0.35rem; border-radius: 99px;
  background: rgb(var(--ink) / 0.1); font-size: 0.6875rem; line-height: 1.3; font-variant-numeric: tabular-nums;
}
.adm-seg-btn[aria-pressed='true'] .bl-seg-count { background: rgb(255 255 255 / 0.22); }

/* ── Daftar ────────────────────────────────────────────────────── */
.bl-list { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 0.7rem; transition: opacity 0.15s; }
.bl-list.is-refreshing { opacity: 0.6; }
.bl-item {
  padding: 0.95rem 1.05rem; min-width: 0;
  border: 1px solid var(--border); border-left: 3px solid var(--red-soft);
  border-radius: var(--r-md); background: var(--surface);
}
.bl-item.is-expired, .bl-item.is-lifted { border-left-color: var(--border-strong); }
.bl-item.is-expired .bl-value, .bl-item.is-lifted .bl-value { color: var(--text-dim); }

.bl-item-top { display: flex; align-items: center; gap: 0.75rem; min-width: 0; }
.bl-kind {
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 34px; height: 34px; border-radius: var(--r-sm);
}
.bl-id { flex: 1; min-width: 0; }
.bl-value { margin: 0; font-size: 1rem; font-weight: 700; color: var(--text); overflow-wrap: anywhere; }
.bl-sub { margin: 0.15rem 0 0; font-size: 0.78rem; color: var(--text-dim); overflow-wrap: anywhere; }
.bl-badges { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 0.35rem; flex-shrink: 0; }

.bl-meta {
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.7rem 1.25rem;
  margin: 0.85rem 0 0; padding-top: 0.85rem; border-top: 1px solid var(--border);
}
.bl-meta > div { min-width: 0; }
.bl-meta-wide { grid-column: 1 / -1; }
.bl-meta dt {
  margin: 0 0 0.15rem; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--text-faint);
}
.bl-meta dd { margin: 0; font-size: 0.8125rem; line-height: 1.5; color: var(--text-2); overflow-wrap: anywhere; }

.bl-trace { margin-top: 0.85rem; padding: 0.7rem 0.85rem; border-radius: var(--r-sm); background: rgb(var(--ink) / 0.03); }
.bl-trace-title {
  display: flex; align-items: center; gap: 0.35rem; margin: 0;
  font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint);
}
.bl-meta--trace { margin-top: 0.6rem; padding-top: 0; border-top: 0; }
.bl-link { display: inline-flex; align-items: center; gap: 0.2rem; margin-left: 0.4rem; color: var(--blue-soft); font-size: 0.75rem; text-decoration: none; }
.bl-link:hover { text-decoration: underline; }

.bl-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 0.5rem; margin-top: 0.85rem; }
.bl-limit { margin: 0.6rem 0 0; text-align: center; }

/* ── Responsif ─────────────────────────────────────────────────── */
@media (max-width: 760px) {
  .bl-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bl-meta { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .bl-add-grid { grid-template-columns: 1fr; }
  .bl-add-btn { width: 100%; }
  .bl-item-top { flex-wrap: wrap; }
  .bl-badges { justify-content: flex-start; flex-basis: 100%; }
  .bl-meta { grid-template-columns: 1fr; }
  .bl-actions .adm-btn { flex: 1 1 auto; justify-content: center; }
  .bl-toolbar .adm-seg { width: 100%; }
  .bl-toolbar .adm-seg .adm-seg-btn { flex: 1; }
}

/* ── Percobaan terblokir ── */
.bl-err { color: var(--red-soft, #f87171); }
.bl-attempts { border: 1px solid var(--border, rgb(var(--ink) / 0.1)); border-radius: var(--r-md, 12px); overflow: hidden; }
.bl-att-head {
  width: 100%; display: flex; align-items: center; gap: 0.6rem; padding: 0.75rem 0.9rem; min-height: 48px;
  background: transparent; border: 0; color: var(--text); text-align: left; cursor: pointer; font: inherit;
}
.bl-att-head:hover { background: rgb(var(--ink) / 0.04); }
.bl-att-head:focus-visible { outline: 2px solid var(--blue-soft, #60a5fa); outline-offset: -2px; }
.bl-att-title { display: inline-flex; align-items: center; gap: 0.4rem; font-weight: 700; font-size: 0.875rem; }
.bl-att-sub { flex: 1; min-width: 0; font-size: 0.75rem; }
.bl-chev { flex-shrink: 0; transition: transform 0.2s; }
.bl-chev.is-open { transform: rotate(180deg); }
.bl-att-body { display: flex; flex-direction: column; gap: 0.7rem; padding: 0 0.9rem 0.9rem; }
.bl-att-list { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 0.6rem; }
.bl-att { padding: 0.7rem 0.8rem; border-radius: var(--r-sm, 8px); background: rgb(var(--ink) / 0.03); border-left: 3px solid var(--red-soft, #f87171); }
.bl-att-top { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; font-size: 0.75rem; }
.bl-att-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.6rem; }

/* ── Pesanan terakhir per blokir ── */
.bl-orders { margin-top: 0.75rem; border: 1px solid var(--border, rgb(var(--ink) / 0.1)); border-radius: var(--r-sm, 8px); }
.bl-orders--warn { border-color: var(--line-red, rgb(220 38 38 / 0.35)); }
.bl-orders-sum {
  display: flex; align-items: center; gap: 0.4rem; padding: 0.55rem 0.8rem; min-height: 44px; cursor: pointer;
  font-size: 0.8125rem; font-weight: 600; color: var(--text); list-style: none;
}
.bl-orders-sum::-webkit-details-marker { display: none; }
.bl-orders-sum:focus-visible { outline: 2px solid var(--blue-soft, #60a5fa); outline-offset: -2px; }
.bl-order-list { margin: 0; padding: 0 0.8rem 0.8rem; list-style: none; display: flex; flex-direction: column; gap: 0.55rem; }
.bl-order { padding: 0.6rem 0.7rem; border-radius: var(--r-sm, 8px); background: rgb(var(--ink) / 0.03); min-width: 0; }
.bl-order-top { display: flex; flex-wrap: wrap; align-items: center; gap: 0.45rem; font-size: 0.75rem; }
.bl-order-no { font-weight: 700; color: var(--blue-soft, #60a5fa); text-decoration: none; padding: 0.15rem 0; }
.bl-order-no:hover { text-decoration: underline; }
.bl-order-meta { margin: 0.45rem 0 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.4rem 0.8rem; }
.bl-order-meta > div { min-width: 0; }
.bl-order-meta dt { font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-faint); }
.bl-order-meta dd { margin: 0; font-size: 0.8125rem; line-height: 1.5; color: var(--text-2); overflow-wrap: anywhere; }

@media (max-width: 900px) {
  .bl-stats { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .bl-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bl-att-sub { display: none; }
  .bl-order-meta { grid-template-columns: minmax(0, 1fr); }
}
</style>
