# Klasifikasi Referensi Arsitektur Data (RAD) SPBE Menggunakan SVM & TF-IDF

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Machine Learning](https://img.shields.io/badge/ML-SVM%20%7C%20TF--IDF-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Repositori ini berisi kode sumber dan dokumentasi untuk aplikasi *Machine Learning* yang memprediksi dan mengklasifikasikan data ke dalam **Referensi Arsitektur Data (RAD)** sesuai standar **Peraturan Presiden Nomor 132 Tahun 2022 tentang Arsitektur Sistem Pemerintahan Berbasis Elektronik (SPBE) Nasional**.

Klasifikasi dilakukan dengan memproses gabungan fitur teks dari kolom **"nama"** dan **"definisi"** data menggunakan ekstraksi fitur **TF-IDF (Term Frequency-Inverse Document Frequency)** dan algoritma pemodelan **Support Vector Machine (SVM)**.

---

## 📌 Latar Belakang

Sesuai dengan **Perpres No. 132 Tahun 2022**, Referensi Arsitektur Data (RAD) merupakan kerangka acuan yang digunakan untuk mengelompokkan dan mengklasifikasikan data berdasarkan kategori tertentu. Tujuannya adalah agar data pemerintah/instansi dapat:
1. Lebih mudah ditelusuri (*discoverable*),
2. Dipahami konteksnya (*understandable*), dan
3. Digunakan secara optimal (*interoperable* & *reusable*).

Proses klasifikasi data secara manual membutuhkan waktu yang lama dan rentan terhadap inkonsistensi. Proyek ini bertujuan untuk me-otomatisasi proses tersebut menggunakan pendekatan NLP (*Natural Language Processing*) dan *Machine Learning*.

---

## 🚀 Fitur Utama

- **Text Preprocessing**: Pembersihan teks (case folding, penghapusan tanda baca/angka), *stopword removal* bahasa Indonesia, dan *stemming* (optional).
- **Feature Extraction**: Mengubah kombinasi teks dari kolom `nama` dan `definisi` menjadi vektor angka menggunakan `TF-IDF Vectorizer`.
- **Classification Model**: Pelatihan dan evaluasi model menggunakan **Support Vector Machine (SVM)** yang terbukti efektif untuk data teks berdimensi tinggi.
- **Model Evaluation**: Laporan performa model menggunakan *Accuracy*, *Precision*, *Recall*, *F1-Score*, dan *Confusion Matrix*.
- **Inference Pipeline**: Antarmuka/fungsi prediksi untuk mengklasifikasikan masukan data baru secara langsung.

---
