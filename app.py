from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import pickle
import json
import os
import io
import datetime

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')
METADATA_PATH = os.path.join(BASE_DIR, 'model_metadata.json')
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')

# Ensure export directory exists
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Global model and metadata variables
model = None
metadata = {}

def load_resources():
    global model, metadata
    
    # 1. Load Model
    if os.path.exists(MODEL_PATH):
        print(f"--> Memuat model dari {MODEL_PATH}...")
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            print("--> Model berhasil dimuat!")
        except Exception as e:
            print(f"[ERROR] Gagal memuat model: {e}")
            model = None
    else:
        print(f"[WARNING] File model '{MODEL_PATH}' tidak ditemukan. Silakan jalankan 'train_and_save.py' terlebih dahulu.")
        model = None

    # 2. Load Metadata
    if os.path.exists(METADATA_PATH):
        print(f"--> Memuat metadata dari {METADATA_PATH}...")
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            print("--> Metadata berhasil dimuat!")
        except Exception as e:
            print(f"[ERROR] Gagal memuat metadata: {e}")
            metadata = {}
    else:
        print(f"[WARNING] File metadata '{METADATA_PATH}' tidak ditemukan.")
        metadata = {}

# Load resources when Flask starts
load_resources()

def find_column(df, candidates):
    """Mencari nama kolom dalam dataframe secara case-insensitive."""
    for col in df.columns:
        if str(col).strip().lower() in candidates:
            return col
    return None

@app.route('/')
def index():
    """Render dashboard UI."""
    return render_template('index.html')

@app.route('/metadata', methods=['GET'])
def get_metadata():
    """Retrieve metadata about the model (stats, categories list, accuracy)."""
    if not metadata:
        load_resources()
    return jsonify(metadata)

@app.route('/download-template', methods=['GET'])
def download_template():
    """Mengunduh file Excel contoh/template dengan kolom Nama Data dan Definisi."""
    sample_data = [
        {
            "Nama Data": "Tingkat Pengangguran Terbuka Menurut Tingkat Pendidikan",
            "Definisi": "Persentase jumlah angkatan kerja yang sedang mencari pekerjaan atau menyiapkan usaha dibagi total angkatan kerja per jenjang pendidikan."
        },
        {
            "Nama Data": "Jumlah Puskesmas Pembantu dan Posyandu Aktif",
            "Definisi": "Banyaknya unit pelayanan kesehatan tingkat pertama dan pos pelayanan terpadu yang beroperasi aktif melayani masyarakat."
        },
        {
            "Nama Data": "Luas Kawasan Hutan Lindung Berdasarkan SK Penetapan",
            "Definisi": "Total luas area hutan yang mempunyai fungsi pokok sebagai perlindungan sistem penyangga kehidupan dan pencegah bencana alam."
        },
        {
            "Nama Data": "Penyaluran Kredit Usaha Rakyat (KUR) Sektor Mikro",
            "Definisi": "Realisasi pembiayaan modal kerja dan investasi bagi pelaku usaha mikro, kecil, dan menengah dengan subsidi bunga pemerintah."
        }
    ]
    template_df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Template_RAD')
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='template_klasifikasi_rad.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/classify-excel', methods=['POST'])
def classify_excel():
    """Menerima file Excel, mengklasifikasikan setiap baris, menyisipkan kolom hasil di sisi paling kanan, dan menyimpan file."""
    global model
    if model is None:
        return jsonify({"error": "Model Machine Learning belum dimuat di server."}), 503

    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file Excel yang diunggah."}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "File belum dipilih."}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({"error": "Format file tidak didukung. Harap unggah file Excel (.xlsx atau .xls)."}), 400

    try:
        # Baca file Excel menggunakan pandas
        df = pd.read_excel(file)

        if df.empty:
            return jsonify({"error": "File Excel yang diunggah kosong."}), 400

        # Cari kolom Nama Data dan Definisi secara fleksibel
        col_nama = find_column(df, ['nama data', 'nama_data', 'namadata', 'nama'])
        col_definisi = find_column(df, ['definisi', 'definisi data', 'deskripsi', 'keterangan'])

        if not col_nama or not col_definisi:
            found_cols = ", ".join([f"'{c}'" for c in df.columns])
            return jsonify({
                "error": f"Kolom wajib tidak lengkap. Diperlukan kolom 'Nama Data' dan 'Definisi'. Kolom yang ditemukan di file: [{found_cols}]."
            }), 400

        # Preprocessing teks: persis sesuai format pelatihan model (Nama Data diulang 2x + Definisi)
        nama_series = df[col_nama].fillna('').astype(str).str.strip()
        definisi_series = df[col_definisi].fillna('').astype(str).str.strip()
        
        teks_input = (nama_series + " ") * 2 + definisi_series

        # Batch inference seluruh baris
        predictions = model.predict(teks_input)

        # Letakkan kolom hasil klasifikasi di sisi paling kanan
        target_col_name = "Kategori RAD"
        if target_col_name in df.columns:
            df = df.drop(columns=[target_col_name])
        df[target_col_name] = predictions

        # Simpan file hasil ke folder exports
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name, _ = os.path.splitext(filename)
        output_filename = f"hasil_klasifikasi_{base_name}_{timestamp}.xlsx"
        output_filepath = os.path.join(EXPORTS_DIR, output_filename)

        with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Hasil_Klasifikasi')

        # Hitung distribusi kategori hasil klasifikasi
        category_distribution = df[target_col_name].value_counts().to_dict()

        # Siapkan preview data (maksimal 100 baris untuk kenyamanan respons UI)
        preview_df = df.head(100).fillna('')
        preview_data = preview_df.to_dict(orient='records')

        return jsonify({
            "status": "success",
            "message": f"Berhasil mengklasifikasikan {len(df)} baris data.",
            "filename": output_filename,
            "download_url": f"/download/{output_filename}",
            "total_rows": len(df),
            "category_counts": category_distribution,
            "columns": df.columns.tolist(),
            "preview_data": preview_data
        })

    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan saat memproses file Excel: {e}")
        return jsonify({"error": f"Gagal memproses file Excel: {str(e)}"}), 500

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Mengunduh file hasil klasifikasi."""
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(EXPORTS_DIR, safe_filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File tidak ditemukan atau telah kedaluwarsa."}), 404
    return send_from_directory(EXPORTS_DIR, safe_filename, as_attachment=True)

@app.route('/predict', methods=['POST'])
def predict():
    """Klasifikasi data tunggal Nama Data dan Definisi (opsional/backward compatibility)."""
    global model
    if model is None:
        return jsonify({"error": "Model belum dimuat di server."}), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Data input kosong."}), 400

        nama_data = data.get('nama_data', '').strip()
        definisi = data.get('definisi', '').strip()

        if not nama_data or not definisi:
            return jsonify({"error": "Nama data dan definisi harus diisi."}), 400

        teks_input = [(nama_data + " ") * 2 + definisi]
        prediction = model.predict(teks_input)
        kategori_terprediksi = prediction[0]

        return jsonify({
            "status": "success",
            "nama_data": nama_data,
            "definisi": definisi,
            "kategori": kategori_terprediksi
        })

    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan saat prediksi tunggal: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

