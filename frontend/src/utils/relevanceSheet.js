// src/utils/relevanceSheet.js
//
// Lembar penilaian relevansi untuk evaluasi rekomendasi menu (Precision@3).
// Modul MURNI: menerima indeks dari recommender.js, mengembalikan teks CSV.
//
// Cara pakai di penelitian:
//   1. Ekspor lembar ini (satu baris = satu menu rekomendasi untuk satu menu acuan).
//   2. Beberapa penilai mengisi kolom Penilai_n: 1 = relevan, 0 = tidak relevan.
//   3. Precision@3 satu menu acuan = (jumlah nilai 1 pada 3 baris) / 3, lalu dirata-rata
//      semua menu acuan dan semua penilai.
//
// Skor cosine ditaruh di kolom paling kanan dan diberi label supaya penilai tidak
// terpengaruh angka saat menilai.
import { similarTo } from "@/utils/recommender"

const SEP = ";" // Excel dengan locale Indonesia memakai titik koma sebagai pemisah kolom
const BOM = "\uFEFF" // supaya Excel membaca UTF-8 dengan benar

// Cegah CSV injection: sel yang diawali = + - @ dianggap rumus oleh Excel.
const cell = (value) => {
  let s = value == null ? "" : String(value)
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s
  if (/[";\n\r]/.test(s)) s = `"${s.replace(/"/g, '""')}"`
  return s
}

const row = (cols) => cols.map(cell).join(SEP)

/**
 * @param index  hasil buildIndex(menus)
 * @param opts.limit   jumlah rekomendasi per menu acuan (default 3 = Precision@3)
 * @param opts.raters  jumlah kolom penilai (default 3)
 * @returns { csv, referenceCount, rowCount }
 */
export const buildRelevanceSheet = (index, { limit = 3, raters = 3 } = {}) => {
  const refs = [...index.docs.values()]
    .map((d) => d.menu)
    // Acuan = menu yang memang tampil ke pelanggan (aktif, tersedia, bukan secret),
    // sama dengan yang dipakai modal detail menu.
    .filter((m) => m.is_active !== false && m.is_available !== false && !m.is_secret)
    .sort((a, b) =>
      String(a.category_name || "").localeCompare(String(b.category_name || ""), "id") ||
      String(a.name).localeCompare(String(b.name), "id"),
    )

  const raterHeaders = Array.from({ length: raters }, (_, i) => `Penilai_${i + 1} (1=relevan, 0=tidak)`)
  const lines = [
    row([
      "No", "Menu acuan", "Kategori acuan", "Peringkat",
      "Menu rekomendasi", "Kategori rekomendasi",
      ...raterHeaders,
      "Skor cosine (jangan ditampilkan ke penilai)", "Kata sama",
    ]),
  ]

  let no = 0
  let rowCount = 0
  for (const ref of refs) {
    no += 1
    const recs = similarTo(index, ref.id, { limit })
    // Menu tanpa hasil tetap dicatat: ini bagian dari evaluasi (cakupan rekomendasi).
    if (!recs.length) {
      lines.push(row([no, ref.name, ref.category_name, "-", "(tidak ada rekomendasi)", "", ...raterHeaders.map(() => ""), "", ""]))
      rowCount += 1
      continue
    }
    recs.forEach((r, i) => {
      lines.push(row([
        no, ref.name, ref.category_name, i + 1,
        r.menu.name, r.menu.category_name,
        ...raterHeaders.map(() => ""),
        r.score.toFixed(3), r.reason.join(", "),
      ]))
      rowCount += 1
    })
  }

  return { csv: BOM + lines.join("\r\n"), referenceCount: refs.length, rowCount }
}

// Picu unduhan file di browser.
export const downloadText = (text, filename, mime = "text/csv;charset=utf-8") => {
  const url = URL.createObjectURL(new Blob([text], { type: mime }))
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
