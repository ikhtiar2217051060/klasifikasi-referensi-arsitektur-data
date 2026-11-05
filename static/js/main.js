document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. DOM Elements Reference
    // -------------------------------------------------------------------------
    // Stats & Metadata Elements
    const totalSamplesEl = document.getElementById('stat-total-samples');
    const totalCategoriesEl = document.getElementById('stat-total-categories');
    const accuracyEl = document.getElementById('stat-accuracy');
    const categoriesContainer = document.getElementById('categories-list-container');
    const searchInput = document.getElementById('category-search');
    const reloadLink = document.getElementById('reload-model-link');

    // Tab Navigation
    const tabExcelBtn = document.getElementById('tab-excel-btn');
    const excelWorkspace = document.getElementById('excel-workspace-card');

    // Excel Batch Classifier Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('excel-file-input');
    const dropPrompt = document.getElementById('drop-zone-prompt');
    const filePreview = document.getElementById('selected-file-preview');
    const fileNameEl = document.getElementById('selected-file-name');
    const fileSizeEl = document.getElementById('selected-file-size');
    const btnRemoveFile = document.getElementById('btn-remove-file');
    
    const btnClassifyExcel = document.getElementById('btn-classify-excel');
    const excelSpinner = document.getElementById('excel-spinner');
    const excelBtnIcon = document.getElementById('excel-btn-icon');
    const excelBtnText = document.getElementById('excel-btn-text');

    // Batch Results Elements
    const batchResultPanel = document.getElementById('batch-result-panel');
    const batchSummaryText = document.getElementById('batch-summary-text');
    const btnDownloadResult = document.getElementById('btn-download-result');
    const categoryPillsContainer = document.getElementById('category-pills-container');

    // Toast Elements
    const toast = document.getElementById('toast-notification');
    const toastMessage = document.getElementById('toast-message');

    // State
    let categoriesData = {};
    let selectedExcelFile = null;

    // Initialize Lucide Icons
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // -------------------------------------------------------------------------
    // 2. Fetch and Populate Dashboard Metadata
    // -------------------------------------------------------------------------
    async function loadMetadata() {
        try {
            const response = await fetch('/metadata');
            if (!response.ok) throw new Error('Gagal memuat metadata model.');
            
            const data = await response.json();
            
            if (data.total_samples) {
                totalSamplesEl.textContent = data.total_samples.toLocaleString('id-ID');
            }
            if (data.num_categories) {
                totalCategoriesEl.textContent = data.num_categories;
            }
            if (data.accuracy) {
                accuracyEl.textContent = `${data.accuracy}%`;
            }
            
            categoriesData = data.categories_distribution || {};
            renderCategoryList(categoriesData);
        } catch (error) {
            console.error('Error loading metadata:', error);
            showToast('Gagal memuat statistik model dari server.', 'alert-circle');
        }
    }

    function renderCategoryList(categories) {
        categoriesContainer.innerHTML = '';
        const keys = Object.keys(categories).sort();
        
        if (keys.length === 0) {
            categoriesContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Tidak ada kategori ditemukan</div>`;
            return;
        }

        keys.forEach(key => {
            const count = categories[key];
            const item = document.createElement('div');
            item.className = 'category-item';
            item.innerHTML = `
                <span class="category-name" title="${key}">${key}</span>
                <span class="category-count">${count} data</span>
            `;
            categoriesContainer.appendChild(item);
        });
    }

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const filtered = {};
        
        Object.keys(categoriesData).forEach(key => {
            if (key.toLowerCase().includes(query)) {
                filtered[key] = categoriesData[key];
            }
        });
        
        renderCategoryList(filtered);
    });

    // -------------------------------------------------------------------------
    // 3. Tab Switching Logic
    // -------------------------------------------------------------------------
    // -------------------------------------------------------------------------
    // 4. File Drag & Drop and Selection Handling
    // -------------------------------------------------------------------------
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(2) + ' MB';
    }

    function setFile(file) {
        if (!file) return;

        const lowerName = file.name.toLowerCase();
        if (!lowerName.endsWith('.xlsx') && !lowerName.endsWith('.xls')) {
            showToast('Format file tidak didukung! Harap gunakan file .xlsx atau .xls', 'alert-triangle');
            return;
        }

        selectedExcelFile = file;
        fileNameEl.textContent = file.name;
        fileSizeEl.textContent = formatFileSize(file.size);

        dropPrompt.style.display = 'none';
        filePreview.style.display = 'block';
        btnClassifyExcel.disabled = false;

        // Reset previous result if a new file is selected
        batchResultPanel.style.display = 'none';

        if (window.lucide) window.lucide.createIcons();
    }

    function resetFileSelection() {
        selectedExcelFile = null;
        fileInput.value = '';
        dropPrompt.style.display = 'block';
        filePreview.style.display = 'none';
        btnClassifyExcel.disabled = true;
        batchResultPanel.style.display = 'none';
    }

    // Trigger file dialog on drop zone click
    dropZone.addEventListener('click', (e) => {
        if (e.target.closest('#btn-remove-file')) return;
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    });

    btnRemoveFile.addEventListener('click', (e) => {
        e.stopPropagation();
        resetFileSelection();
        showToast('Pilihan file dibatalkan.', 'info');
    });

    // Drag & drop event listeners
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files[0]) {
            setFile(dt.files[0]);
        }
    });

    // -------------------------------------------------------------------------
    // 5. Excel Batch Classification Submission
    // -------------------------------------------------------------------------
    btnClassifyExcel.addEventListener('click', async () => {
        if (!selectedExcelFile) {
            showToast('Silakan pilih file Excel terlebih dahulu!', 'alert-triangle');
            return;
        }

        // Set Loading State
        btnClassifyExcel.disabled = true;
        excelSpinner.style.display = 'inline-block';
        if (excelBtnIcon) excelBtnIcon.style.display = 'none';
        excelBtnText.textContent = 'Memproses Klasifikasi Data...';

        const formData = new FormData();
        formData.append('file', selectedExcelFile);

        try {
            const response = await fetch('/classify-excel', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Terjadi kesalahan saat memproses file Excel.');
            }

            // Populate Success Banner
            batchSummaryText.textContent = `${result.total_rows.toLocaleString('id-ID')} baris data berhasil diklasifikasikan ke kategori RAD.`;
            btnDownloadResult.href = result.download_url;
            btnDownloadResult.setAttribute('download', result.filename);

            // Render Category Summary Pills
            renderCategoryPills(result.category_counts || {});

            // Display Results Panel
            batchResultPanel.style.display = 'block';
            batchResultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            if (window.lucide) window.lucide.createIcons();

            showToast(result.message || 'Klasifikasi selesai dan file siap diunduh!', 'check-circle');

        } catch (error) {
            console.error('Classification error:', error);
            showToast(error.message, 'alert-circle');
        } finally {
            // Restore button state
            btnClassifyExcel.disabled = false;
            excelSpinner.style.display = 'none';
            if (excelBtnIcon) excelBtnIcon.style.display = 'inline-block';
            excelBtnText.textContent = 'Klasifikasikan File Excel';
            if (window.lucide) window.lucide.createIcons();
        }
    });

    // -------------------------------------------------------------------------
    // 6. Category Pills Rendering
    // -------------------------------------------------------------------------
    function renderCategoryPills(counts) {
        categoryPillsContainer.innerHTML = '';
        const sortedCats = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);

        if (sortedCats.length === 0) {
            categoryPillsContainer.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">Tidak ada kategori yang terdeteksi.</span>';
            return;
        }

        sortedCats.forEach(cat => {
            const pill = document.createElement('div');
            pill.className = 'cat-pill';
            pill.innerHTML = `
                <span class="cat-pill-name">${cat}</span>
                <span class="cat-pill-count">${counts[cat]}</span>
            `;
            categoryPillsContainer.appendChild(pill);
        });
    }

    // -------------------------------------------------------------------------
    // 8. Model Reload Link
    // -------------------------------------------------------------------------
    reloadLink.addEventListener('click', (e) => {
        e.preventDefault();
        loadMetadata();
        showToast('Statistik model diperbarui!', 'refresh-cw');
    });

    // -------------------------------------------------------------------------
    // 9. Toast Notification Utility
    // -------------------------------------------------------------------------
    let toastTimeout = null;
    function showToast(message, iconName = 'check-circle') {
        toastMessage.textContent = message;
        
        const iconContainer = toast.querySelector('i');
        if (iconContainer && window.lucide) {
            iconContainer.setAttribute('data-lucide', iconName);
            window.lucide.createIcons();
        }
        
        toast.classList.add('show');
        
        if (toastTimeout) clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            toast.classList.remove('show');
        }, 3500);
    }

    // Initial Load
    loadMetadata();
});

