import pandas as pd
import pickle
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score

# Stopwords
STOPWORDS_ID = [
    'dan', 'yang', 'mengenai', 'dengan', 'untuk', 'pada', 'atau', 'dalam', 
    'dari', 'adalah', 'ke', 'secara', 'serta', 'oleh', 'ini', 'itu', 
    'banyaknya', 'jumlah', 'persentase', 'tingkat'
]

def main():
    print("--> Membaca dataset...")
    dataset_path = 'data_bersih2.xlsx'
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset {dataset_path} tidak ditemukan!")
        return

    df = pd.read_excel(dataset_path).dropna(subset=['Nama Data', 'Definisi', 'Kategori RAD'])
    df['Kategori RAD'] = df['Kategori RAD'].astype(str).str.strip()

    # Filtering Kategori dengan minimal 2 data
    v_counts = df['Kategori RAD'].value_counts()
    valid_categories = v_counts[v_counts >= 2].index
    
    df_clean = df[df['Kategori RAD'].isin(valid_categories)].copy()
    df_clean['teks_lengkap'] = (df_clean['Nama Data'].astype(str) + " ") * 2 + df_clean['Definisi'].astype(str)

    X = df_clean['teks_lengkap']
    y = df_clean['Kategori RAD']

    # Split data untuk evaluasi performa
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("--> Melatih model untuk evaluasi...")
    eval_pipeline = make_pipeline(
        TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=STOPWORDS_ID,
            sublinear_tf=True
        ),
        LinearSVC(class_weight='balanced', random_state=42, dual='auto')
    )
    eval_pipeline.fit(X_train, y_train)
    
    # Evaluasi akurasi
    y_pred = eval_pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    accuracy_percentage = round(accuracy * 100, 2)
    print(f"--> Akurasi Evaluasi: {accuracy_percentage}%")

    # Ambil statistik dataset
    categories_distribution = df_clean['Kategori RAD'].value_counts().to_dict()
    total_samples = len(df_clean)
    num_categories = len(categories_distribution)

    # Melatih model akhir pada SELURUH data bersih agar model lebih optimal untuk web
    print("--> Melatih model akhir pada seluruh dataset...")
    final_pipeline = make_pipeline(
        TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=STOPWORDS_ID,
            sublinear_tf=True
        ),
        LinearSVC(class_weight='balanced', random_state=42, dual='auto')
    )
    final_pipeline.fit(X, y)

    # Simpan model
    model_file = 'model.pkl'
    print(f"--> Menyimpan model ke {model_file}...")
    with open(model_file, 'wb') as f:
        pickle.dump(final_pipeline, f)

    # Simpan metadata training untuk visualisasi frontend
    metadata = {
        "accuracy": accuracy_percentage,
        "total_samples": total_samples,
        "num_categories": num_categories,
        "categories_distribution": categories_distribution,
        "stopwords_used": STOPWORDS_ID
    }
    
    metadata_file = 'model_metadata.json'
    print(f"--> Menyimpan metadata ke {metadata_file}...")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
        
    print("--> Selesai!")

if __name__ == "__main__":
    main()
