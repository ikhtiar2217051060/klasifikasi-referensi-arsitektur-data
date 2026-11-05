import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# ==============================================================================
# 1. STOPWORDS KHUSUS BAHASA INDONESIA & DATASET
# ==============================================================================
# Kata hubung umum + kata umum dataset yang tidak membawa makna spesifik kategori
STOPWORDS_ID = [
    'dan', 'yang', 'mengenai', 'dengan', 'untuk', 'pada', 'atau', 'dalam', 
    'dari', 'adalah', 'ke', 'secara', 'serta', 'oleh', 'ini', 'itu', 
    'banyaknya', 'jumlah', 'persentase', 'tingkat'
]

# ==============================================================================
# 2. LOAD & CLEAN DATASET
# ==============================================================================
print("--> Membaca dataset...")
df = pd.read_excel('data_bersih2.xlsx').dropna(subset=['Nama Data', 'Definisi', 'Kategori RAD'])

# Bersihkan whitespace di kolom kategori
df['Kategori RAD'] = df['Kategori RAD'].astype(str).str.strip()

# Filtering: Hanya ambil kategori yang memiliki minimal 2 data agar `stratify` berjalan
v_counts = df['Kategori RAD'].value_counts()
valid_categories = v_counts[v_counts >= 2].index
kategori_terbuang = v_counts[v_counts < 2]

if not kategori_terbuang.empty:
    print("\n[INFO] Kategori berikut dieleminasi karena hanya ada 1 data (tidak cukup untuk split train/test):")
    for kat, val in kategori_terbuang.items():
        print(f" - {kat}: {val} data")

df_clean = df[df['Kategori RAD'].isin(valid_categories)].copy()

# ==============================================================================
# 3. FEATURE ENGINEERING (PENGGABUNGAN TEKS)
# ==============================================================================
# Trik: Mengulang 'Nama Data' 2 kali memberi bobot lebih tinggi pada judul dibanding definisi
df_clean['teks_lengkap'] = (df_clean['Nama Data'].astype(str) + " ") * 2 + df_clean['Definisi'].astype(str)

X = df_clean['teks_lengkap']
y = df_clean['Kategori RAD']

# ==============================================================================
# 4. SPLIT DATA (80% Train, 20% Test)
# ==============================================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n--> Data Latih: {len(X_train)} baris | Data Uji: {len(X_test)} baris")

# ==============================================================================
# 5. PIPELINE MODEL (TF-IDF + LinearSVC)
# ==============================================================================
# LinearSVC adalah pilihan terbaik & sangat cepat untuk klasifikasi teks berkategori banyak
model_pipeline = make_pipeline(
    TfidfVectorizer(
        ngram_range=(1, 2),        # Mengambil uni-gram dan bi-gram
        stop_words=STOPWORDS_ID,   # Filter kata non-informatif
        sublinear_tf=True          # Mengurangi efek penalti kata berulang
    ),
    LinearSVC(class_weight='balanced', random_state=42, dual='auto') # Menyeimbangkan kelas minoritas
)

# Training Model
model_pipeline.fit(X_train, y_train)

# ==============================================================================
# 6. EVALUASI MODEL
# ==============================================================================
y_pred = model_pipeline.predict(X_test)

print("\n==================================================")
print(f"AKURASI MODEL: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("==================================================")
print(classification_report(y_test, y_pred, zero_division=0))

# ==============================================================================
# 7. FUNGSI PREDIKSI UNTUK DATA BARU
# ==============================================================================
def prediksi_kategori(nama_data: str, definisi: str) -> str:
    """Fungsi helper untuk memprediksi kategori RAD dari Nama Data & Definisi baru."""
    # Format persis seperti saat training
    teks_input = [(nama_data + " ") * 2 + definisi]
    prediksi = model_pipeline.predict(teks_input)
    return prediksi[0]

# --- CONTOH PENGGUNAAN UJI DATA BARU ---
print("==================================================")
print("TEST PREDIKSI DATA BARU")
print("==================================================")

sample_nama = "Tingkat Pengangguran Terbuka Menurut Tingkat Pendidikan"
sample_definisi = "Persentase jumlah angkatan kerja yang sedang mencari pekerjaan atau menyiapkan usaha dibagi total angkatan kerja per jenjang pendidikan"

kategori_hasil = prediksi_kategori(sample_nama, sample_definisi)

print(f"Nama Data    : {sample_nama}")
print(f"Definisi     : {sample_definisi}")
print(f"Hasil Prediksi RAD -> [{kategori_hasil}]")