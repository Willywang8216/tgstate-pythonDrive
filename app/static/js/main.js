document.addEventListener('DOMContentLoaded', () => {
    // --- Global Variables ---
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const progressArea = document.getElementById('progress-area');
    const uploadedArea = document.getElementById('uploaded-area');
    const searchInput = document.getElementById('file-search');
    
    // --- Search Functionality ---
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            // Select both file list items and image grid cards
            const items = document.querySelectorAll('.file-item, .image-card');
            items.forEach(item => {
                const name = (item.dataset.filename || '').toLowerCase();
                if (name.includes(term)) {
                    item.style.display = ''; // Reset to default (grid or flex)
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // --- Upload Logic ---
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (event) => {
            event.preventDefault();
            uploadArea.classList.add('active');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('active');
        });

        uploadArea.addEventListener('drop', (event) => {
            event.preventDefault();
            uploadArea.classList.remove('active');
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                handleFiles(files);
            }
        });

        fileInput.addEventListener('change', ({ target }) => {
            if (target.files.length > 0) {
                handleFiles(target.files);
            }
        });
    }

    // Queue system for uploads
    const uploadQueue = [];
    let isUploading = false;

    function handleFiles(files) {
        // Clear previous progress if needed, or keep history? 
        // Let's keep history for this session but maybe clear if it gets too long?
        // For now, simple behavior:
        progressArea.innerHTML = ''; 
        // uploadedArea.innerHTML = ''; // Optional: keep uploaded history
        
        for (const file of files) {
            uploadQueue.push(file);
        }
        processQueue();
    }

    function processQueue() {
        if (isUploading || uploadQueue.length === 0) return;
        
        isUploading = true;
        const file = uploadQueue.shift();
        uploadFile(file).then(() => {
            isUploading = false;
            processQueue();
        });
    }

    function uploadFile(file) {
        return new Promise((resolve) => {
            const formData = new FormData();
            formData.append('file', file, file.name);
            
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/upload', true);
            const fileId = `temp-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;

            // Initial Progress UI
            const progressHTML = `
                <div class="upload-row" id="progress-${fileId}">
                    <div class="content">
                        <i class="fas fa-file-upload text-muted"></i>
                        <div class="details">
                            <span class="name">${file.name}</span>
                            <div class="progress-bar"><div class="progress" style="width: 0%"></div></div>
                        </div>
                    </div>
                </div>`;
            progressArea.insertAdjacentHTML('beforeend', progressHTML);
            const progressBar = document.querySelector(`#progress-${fileId} .progress`);

            xhr.upload.onprogress = ({ loaded, total }) => {
                const percent = Math.floor((loaded / total) * 100);
                if (progressBar) progressBar.style.width = `${percent}%`;
            };

            xhr.onload = () => {
                const progressRow = document.getElementById(`progress-${fileId}`);
                if (progressRow) progressRow.remove();

                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    const fileUrl = response.url;
                    const successHTML = `
                        <div class="upload-row">
                            <div class="content">
                                <i class="fas fa-check-circle" style="color: var(--success-color)"></i>
                                <div class="details">
                                    <span class="name">${file.name}</span>
                                    <span class="status"><a href="${fileUrl}" target="_blank">${fileUrl}</a></span>
                                </div>
                            </div>
                            <button class="action-btn" onclick="copyLink('${fileUrl}')" data-tooltip="Copy"><i class="fas fa-copy"></i></button>
                        </div>`;
                    uploadedArea.insertAdjacentHTML('afterbegin', successHTML);
                } else {
                    let errorMsg = "Upload Failed";
                    try {
                        const parsed = JSON.parse(xhr.responseText);
                        const detail = parsed && parsed.detail;
                        if (typeof detail === 'string') {
                            errorMsg = detail;
                        } else if (detail && typeof detail === 'object') {
                            errorMsg = detail.message || errorMsg;
                        } else if (parsed && parsed.message) {
                            errorMsg = parsed.message;
                        }
                    } catch (e) {}
                    
                    const errorHTML = `
                        <div class="upload-row" style="border-color: var(--danger-color)">
                            <div class="content">
                                <i class="fas fa-exclamation-circle" style="color: var(--danger-color)"></i>
                                <div class="details">
                                    <span class="name">${file.name}</span>
                                    <span class="status" style="color: var(--danger-color)">${errorMsg}</span>
                                </div>
                            </div>
                        </div>`;
                    uploadedArea.insertAdjacentHTML('afterbegin', errorHTML);
                }
                resolve();
            };

            xhr.onerror = () => {
                const progressRow = document.getElementById(`progress-${fileId}`);
                if (progressRow) progressRow.remove();
                // Handle network error UI...
                resolve();
            };

            xhr.send(formData);
        });
    }

    // --- Batch Actions ---
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const batchDeleteBtn = document.getElementById('batch-delete-btn');
    const copyLinksBtn = document.getElementById('copy-links-btn');
    const selectionCounter = document.getElementById('selection-counter');
    const formatOptions = document.querySelectorAll('.format-option');

    function updateBatchControls() {
        const checkboxes = document.querySelectorAll('.file-checkbox');
        const checked = document.querySelectorAll('.file-checkbox:checked');
        const count = checked.length;
        
        if (selectionCounter) selectionCounter.textContent = count > 0 ? `${count} selected` : '';
        if (batchDeleteBtn) batchDeleteBtn.disabled = count === 0;
        if (copyLinksBtn) copyLinksBtn.disabled = count === 0;
        if (selectAllCheckbox) selectAllCheckbox.checked = (count > 0 && count === checkboxes.length);

        // Highlight selected rows
        document.querySelectorAll('.file-item, .image-card').forEach(row => {
            const cb = row.querySelector('.file-checkbox');
            if (cb && cb.checked) row.classList.add('selected'); // Add CSS class if needed for highlight
            else row.classList.remove('selected');
        });
    }

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', (e) => {
            document.querySelectorAll('.file-checkbox').forEach(cb => {
                cb.checked = e.target.checked;
            });
            updateBatchControls();
        });
    }

    // Delegation for dynamic checkboxes
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('file-checkbox')) {
            updateBatchControls();
        }
    });

    // Format selection (Image Hosting)
    if (formatOptions) {
        formatOptions.forEach(opt => {
            opt.addEventListener('click', () => {
                formatOptions.forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
            });
        });
    }

    // Batch Copy
    if (copyLinksBtn) {
        copyLinksBtn.addEventListener('click', () => {
            const checked = document.querySelectorAll('.file-checkbox:checked');
            if (checked.length === 0) return;

            const activeFormatBtn = document.querySelector('.format-option.active');
            const format = activeFormatBtn ? activeFormatBtn.dataset.format : 'url';
            
            const links = Array.from(checked).map(cb => {
                const item = cb.closest('.file-item, .image-card');
                const url = window.location.origin + item.dataset.fileUrl;
                const name = item.dataset.filename;

                if (format === 'markdown') return `![${name}](${url})`;
                if (format === 'html') return `<img src="${url}" alt="${name}">`;
                return url;
            });

            navigator.clipboard.writeText(links.join('\n')).then(() => {
                showToast(`Copied ${links.length} links!`);
            });
        });
    }

    // Batch Delete
    if (batchDeleteBtn) {
        batchDeleteBtn.addEventListener('click', () => {
            const checked = document.querySelectorAll('.file-checkbox:checked');
            if (checked.length === 0) return;

            if (!confirm(`Delete ${checked.length} files?`)) return;

            const fileIds = Array.from(checked).map(cb => cb.dataset.fileId);
            
            fetch('/api/batch_delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_ids: fileIds })
            })
            .then(res => res.json())
            .then(data => {
                // Remove elements
                if (data.deleted) {
                    data.deleted.forEach(item => {
                         // The ID might be the object or string depending on backend
                         const id = item.details?.file_id || item; 
                         removeFileElement(id);
                    });
                    showToast(`Deleted ${data.deleted.length} files.`);
                }
                updateBatchControls();
            });
        });
    }

    // --- SSE & Realtime Updates ---
    const fileListContainer = document.getElementById('file-list-disk');
    if (fileListContainer) {
        let eventSource = null;

        const connectSSE = () => {
            if (eventSource) {
                eventSource.close();
            }
            eventSource = new EventSource('/api/file-updates');

            eventSource.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                const action = msg && msg.action ? msg.action : 'add';
                if (action === 'delete') {
                    removeFileElement(msg.file_id);
                    updateBatchControls();
                    return;
                }
                addNewFileElement(msg);
            };

            eventSource.onerror = () => {
                try { eventSource.close(); } catch (_) {}
                setTimeout(connectSSE, 5000);
            };
        };

        connectSSE();
    }

    function formatDateValue(value) {
        if (!value) return '';
        const d = new Date(value);
        if (!isNaN(d.getTime())) return d.toISOString().split('T')[0];
        const s = String(value);
        return s.split(' ')[0].split('T')[0];
    }

    function addNewFileElement(file) {
        // Determine if we are in list view (index) or grid view (image)
        const isGridView = document.querySelector('.image-grid') !== null;
        const container = document.getElementById('file-list-disk');
        
        // Remove empty state if exists
        const emptyState = container.querySelector('div[style*="text-align: center"]');
        if (emptyState) emptyState.remove();

        const formattedSize = (file.filesize / (1024 * 1024)).toFixed(2) + " MB";
        const formattedDate = formatDateValue(file.upload_date);
        const safeId = file.file_id.replace(':', '-');
         const fileUrl = `/d/${file.file_id}/${encodeURIComponent(file.filename)}`;

        let html = '';
        if (isGridView) {
             html = `
                <div class="image-card file-item-disk" id="file-item-${safeId}" data-file-id="${file.file_id}" data-file-url="${fileUrl}" data-filename="${file.filename}">
                    <div class="image-thumb-wrapper">
                        <img src="${fileUrl}" loading="lazy" class="image-thumb" alt="${file.filename}">
                         <div style="position: absolute; top: 8px; left: 8px;">
                            <input type="checkbox" class="file-checkbox" data-file-id="${file.file_id}">
                        </div>
                    </div>
                    <div class="image-info">
                        <div class="image-name" title="${file.filename}">${file.filename}</div>
                        <div class="image-meta">${formattedSize}</div>
                    </div>
                    <div class="image-actions">
                        <button class="action-btn copy-link-btn" data-tooltip="Copy" onclick="copyLink('${fileUrl}')"><i class="fas fa-link"></i></button>
                        <button class="action-btn delete" data-tooltip="Delete" onclick="deleteFile('${file.file_id}')"><i class="fas fa-trash-alt"></i></button>
                    </div>
                </div>`;
        } else {
            html = `
                <div class="file-item" id="file-item-${safeId}" data-file-id="${file.file_id}" data-file-url="${fileUrl}" data-filename="${file.filename}">
                    <div class="col-checkbox">
                        <input type="checkbox" class="file-checkbox" data-file-id="${file.file_id}">
                    </div>
                    <div class="col-name">
                        <i class="fas fa-file-alt"></i>
                        <span title="${file.filename}">${file.filename}</span>
                    </div>
                    <div class="col-size">${formattedSize}</div>
                    <div class="col-date">${formattedDate}</div>
                    <div class="col-actions">
                        <a href="${fileUrl}" class="action-btn" data-tooltip="Download"><i class="fas fa-download"></i></a>
                        <button class="action-btn copy-link-btn" data-tooltip="Copy Link" onclick="copyLink('${fileUrl}')"><i class="fas fa-link"></i></button>
                        <button class="action-btn delete" data-tooltip="Delete" onclick="deleteFile('${file.file_id}')"><i class="fas fa-trash-alt"></i></button>
                    </div>
                </div>`;
        }

        // Insert at top
        container.insertAdjacentHTML('afterbegin', html);
    }

    // --- Global Helpers ---
    window.copyLink = (path) => {
        const url = window.location.origin + path;
        navigator.clipboard.writeText(url).then(() => {
            showToast('Link copied!');
        });
    };

    window.deleteFile = (fileId) => {
        if (!confirm('Delete this file?')) return;
        fetch(`/api/files/${fileId}`, { method: 'DELETE' })
            .then(async (res) => {
                let data = null;
                try { data = await res.json(); } catch (e) {}
                return { ok: res.ok, data };
            })
            .then(({ ok, data }) => {
                if (ok && data && data.status === 'ok') {
                    removeFileElement(fileId);
                    showToast('File deleted.');
                    updateBatchControls();
                } else {
                    const msg = data?.detail?.message || data?.message || 'Delete failed.';
                    showToast(msg, 'error');
                }
            });
    };

    function removeFileElement(fileId) {
        const el = document.getElementById(`file-item-${fileId.replace(':', '-')}`);
        if (el) el.remove();
        
        // Check if empty
        const container = document.getElementById('file-list-disk');
        if (container && container.children.length === 0) {
            container.innerHTML = `
                <div style="padding: 40px; text-align: center; color: var(--text-tertiary);">
                    <i class="fas fa-folder-open" style="font-size: 48px; margin-bottom: 16px;"></i>
                    <p>No files found</p>
                </div>`;
        }
    }

    function showToast(msg, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = msg;
        document.body.appendChild(toast);
        // Trigger reflow
        toast.offsetHeight;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});
