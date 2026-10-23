<!--
  BundleSection.vue — bagian "Paket" di halaman Menu pelanggan.
  Harga yang tampil = harga web dari server. Label hemat berwarna emas (bukan merah) dan
  hanya muncul bila paket benar-benar lebih murah dari harga normalnya.
-->
<template>
  <section v-if="bundles.length" class="mb-10" aria-labelledby="bundle-heading">
    <div class="mb-4 flex items-end justify-between gap-3">
      <h2 id="bundle-heading" class="font-sora text-2xl font-semibold tracking-tight text-[#111113]">Paket</h2>
      <span class="text-sm text-[#55555D]">{{ bundles.length }} paket</span>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <article
        v-for="b in bundles"
        :key="b.id"
        class="flex flex-col justify-between gap-4 rounded-3xl border-2 border-[#111113] bg-white p-5 shadow-[6px_6px_0_#111113]"
        :class="{ 'opacity-60': b.unavailable_reason }"
      >
        <div class="space-y-3">
          <div class="flex items-start justify-between gap-3">
            <h3 class="font-sora text-lg font-semibold leading-snug text-[#111113]">{{ b.name }}</h3>
            <span
              v-if="b.savings > 0"
              class="flex-shrink-0 rounded-full border-2 border-[#111113] bg-[#F4C542] px-2.5 py-1 text-xs font-extrabold text-[#111113]"
            >Hemat {{ rp(b.savings) }}</span>
          </div>

          <ul class="space-y-1 text-sm text-[#3F3F46]">
            <li v-for="c in b.contents" :key="c.menu">{{ c.quantity }}× {{ c.name }}</li>
          </ul>
          <p v-if="b.description" class="text-sm leading-relaxed text-[#55555D]">{{ b.description }}</p>
        </div>

        <div class="flex items-end justify-between gap-3">
          <div>
            <p v-if="b.normal_price" class="text-xs text-[#6B6B73] line-through">{{ rp(b.normal_price) }}</p>
            <p class="font-sora text-xl font-semibold tabular-nums text-[#111113]">{{ rp(b.price) }}</p>
          </div>

          <p v-if="b.unavailable_reason" class="text-sm font-medium text-[#D92B22]">{{ b.unavailable_reason }}</p>

          <div
            v-else-if="cartStore.quantityOfBundle(b.id) > 0"
            class="flex items-center rounded-full border border-[#111113]/15 bg-[#111113]/[0.03] p-1"
          >
            <button
              type="button"
              :aria-label="'Kurangi ' + b.name"
              class="flex h-9 w-9 items-center justify-center rounded-full text-[#111113] transition-colors hover:bg-[#111113]/10"
              @click="cartStore.updateBundleQuantity(b.id, -1)"
            ><Minus :size="14" /></button>
            <span class="min-w-[1.75rem] text-center text-sm font-semibold tabular-nums text-[#111113]">{{ cartStore.quantityOfBundle(b.id) }}</span>
            <button
              type="button"
              :aria-label="'Tambah ' + b.name"
              class="flex h-9 w-9 items-center justify-center rounded-full bg-[#D92B22] text-outline text-white transition-colors hover:bg-[#B8201A]"
              @click="cartStore.updateBundleQuantity(b.id, 1)"
            ><Plus :size="14" /></button>
          </div>

          <button
            v-else
            type="button"
            class="inline-flex min-h-[44px] items-center gap-2 rounded-full bg-[#D92B22] px-5 text-sm font-semibold text-outline text-white transition-colors hover:bg-[#B8201A]"
            @click="add(b)"
          ><Plus :size="15" /> Tambah</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { Plus, Minus } from "lucide-vue-next"
import { toast } from "vue-sonner"
import { bundleAPI } from "@/api"
import { useCartStore } from "@/stores/cart"

const cartStore = useCartStore()
const bundles = ref([])

const rp = (v) => "Rp" + Math.round(Number(v) || 0).toLocaleString("id-ID")

const add = (b) => {
  const res = cartStore.addBundle(b)
  if (!res.ok) toast.error(res.error)
}

onMounted(async () => {
  try {
    const { data } = await bundleAPI.getPublic()
    bundles.value = Array.isArray(data) ? data : data?.results || []
    // Keranjang tersimpan di HP: samakan dengan paket terbaru (dihapus / habis / harga berubah).
    const r = cartStore.reconcileBundles(bundles.value)
    if (r.removed.length || r.soldOut.length) {
      toast.info(`Paket dikeluarkan dari keranjang: ${[...r.removed, ...r.soldOut].join(", ")}.`)
    } else if (r.repriced.length) {
      toast.info(`Harga paket berubah: ${r.repriced.join(", ")}.`)
    }
  } catch {
    bundles.value = []   // paket gagal dimuat tidak boleh mengganggu daftar menu
  }
})
</script>