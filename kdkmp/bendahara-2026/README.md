# Arsip materi Bendahara KDKMP 2026

Arsip khusus materi pelatihan, terpisah dari pengembangan Lean. Branch: `kdkmp-bendahara-2026`. Repository ini publik; pastikan izin distribusi materi sebelum mengunggah sumber asli.

## Isi yang sudah tersimpan

- [Indeks materi UK 3–6 dan unit kompetensi LSP KSP](indeks-uk03-06-dan-kompetensi.md)
- [Indeks materi UK 7–12 dan perpajakan](indeks-uk07-12-dan-pajak.md)
- [Ekstraksi teks kelompok pertama](ekstraksi-uk03-06-dan-kompetensi.md)
- [Ekstraksi teks kelompok kedua](ekstraksi-uk07-12-dan-pajak.md)

Total sumber: 20 PPTX dan 1 PDF. File asli telah tersimpan di ChatGPT Library /KDKMP/Materi Pelatihan Bendahara 2026; **file biner asli belum tersimpan dalam GitHub**. Indeks memuat nama file dan SHA-256. Ekstraksi bukan pengganti materi visual asli; ketentuan hukum/pajak harus diperiksa sebelum diterapkan.

## Menambahkan file asli

Skrip [unggah-sumber-asli.ps1](unggah-sumber-asli.ps1) memeriksa seluruh 21 checksum sebelum menyalin ke `sumber-asli/`, commit dan push ke branch ini. Jalankan hanya bila berhak mempublikasikan materi. Diperlukan Git, akses tulis GitHub dan satu folder lokal berisi 21 file asli dengan nama yang sama.

Dari komputer Windows, dengan salinan repository yang bersih:

```powershell
git fetch origin kdkmp-bendahara-2026
git switch kdkmp-bendahara-2026
# Jika branch belum ada secara lokal: git switch --track origin/kdkmp-bendahara-2026
& .\kdkmp\bendahara-2026\unggah-sumber-asli.ps1 -SourceDir "D:\Materi KDKMP"
```

Alternatif clone awal (menghemat unduhan sejarah Lean):

```powershell
git clone --depth 1 --filter=blob:none --sparse --single-branch --branch kdkmp-bendahara-2026 https://github.com/dwijayuda/lean4.git lean4-kdkmp
cd lean4-kdkmp
git sparse-checkout set kdkmp/bendahara-2026
```
