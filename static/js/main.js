// Celestial Digital Portfolio & Leaderboard - Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // 1. Certificate Preview Modal Logic
    const certModalEl = document.getElementById('certificatePreviewModal');
    if (certModalEl) {
        certModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            const title = button.getAttribute('data-cert-title') || 'Certificate Document';
            const fileUrl = button.getAttribute('data-file-url');
            const fileType = button.getAttribute('data-file-type') || 'image';

            const modalTitle = certModalEl.querySelector('#certModalLabel');
            const container = certModalEl.querySelector('#certModalContainer');
            const downloadBtn = certModalEl.querySelector('#certModalDownloadBtn');

            if (modalTitle) modalTitle.textContent = title;
            if (downloadBtn && fileUrl) {
                downloadBtn.href = fileUrl;
                downloadBtn.style.display = 'inline-flex';
            }

            if (container && fileUrl) {
                container.innerHTML = '';
                if (fileType === 'pdf') {
                    const iframe = document.createElement('iframe');
                    iframe.src = fileUrl;
                    iframe.className = 'cert-modal-pdf';
                    container.appendChild(iframe);
                } else {
                    const img = document.createElement('img');
                    img.src = fileUrl;
                    img.alt = title;
                    img.className = 'cert-modal-preview';
                    container.appendChild(img);
                }
            }
        });
    }

    // 2. Admin / Faculty Approval Modal Data-Binding
    const verifyModalEl = document.getElementById('verifyActionModal');
    if (verifyModalEl) {
        verifyModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            const certId = button.getAttribute('data-cert-id');
            const title = button.getAttribute('data-cert-title');
            const student = button.getAttribute('data-student-name');
            const category = button.getAttribute('data-cert-category');
            const fileUrl = button.getAttribute('data-file-url');
            const fileType = button.getAttribute('data-file-type');
            const remarks = button.getAttribute('data-remarks') || '';

            const form = verifyModalEl.querySelector('#verifyActionForm');
            if (form) form.action = `/admin/verify/${certId}`;

            const titleSpan = verifyModalEl.querySelector('#verifyModalCertTitle');
            const studentSpan = verifyModalEl.querySelector('#verifyModalStudentName');
            const catSpan = verifyModalEl.querySelector('#verifyModalCategory');
            const remarksInput = verifyModalEl.querySelector('#verifyModalRemarks');
            const previewContainer = verifyModalEl.querySelector('#verifyModalFilePreview');
            const openNewTabBtn = verifyModalEl.querySelector('#verifyModalOpenNewTab');

            if (titleSpan) titleSpan.textContent = title;
            if (studentSpan) studentSpan.textContent = student;
            if (catSpan) catSpan.textContent = category;
            if (remarksInput) remarksInput.value = remarks;
            if (openNewTabBtn && fileUrl) openNewTabBtn.href = fileUrl;

            if (previewContainer && fileUrl) {
                previewContainer.innerHTML = '';
                if (fileType === 'pdf') {
                    previewContainer.innerHTML = `<iframe src="${fileUrl}" style="width: 100%; height: 360px; border: 1px solid #cbd5e1; border-radius: 8px;"></iframe>`;
                } else {
                    previewContainer.innerHTML = `<div class="text-center p-2"><img src="${fileUrl}" alt="${title}" style="max-height: 360px; max-width: 100%; object-fit: contain; border-radius: 8px; border: 1px solid #cbd5e1;"></div>`;
                }
            }
        });
    }

    // 3. Demo Login Autofill Helpers
    const fillAdminBtn = document.getElementById('fillAdminLogin');
    const fillFacultyBtn = document.getElementById('fillFacultyLogin');
    const fillStudentBtn = document.getElementById('fillStudentLogin');
    const fillStudent2Btn = document.getElementById('fillStudent2Login');
    const emailInput = document.getElementById('loginEmail');
    const passwordInput = document.getElementById('loginPassword');

    if (fillAdminBtn && emailInput && passwordInput) {
        fillAdminBtn.addEventListener('click', () => {
            emailInput.value = 'admin@college.edu';
            passwordInput.value = 'Admin@123';
        });
    }
    if (fillFacultyBtn && emailInput && passwordInput) {
        fillFacultyBtn.addEventListener('click', () => {
            emailInput.value = 'faculty.cs@college.edu';
            passwordInput.value = 'Faculty@123';
        });
    }
    if (fillStudentBtn && emailInput && passwordInput) {
        fillStudentBtn.addEventListener('click', () => {
            emailInput.value = 'aarav@student.edu';
            passwordInput.value = 'Student@123';
        });
    }
    if (fillStudent2Btn && emailInput && passwordInput) {
        fillStudent2Btn.addEventListener('click', () => {
            emailInput.value = 'priya@student.edu';
            passwordInput.value = 'Student@123';
        });
    }


    // 4. Mark all notifications as read
    const markAllReadBtn = document.getElementById('markAllNotificationsRead');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function (e) {
            e.preventDefault();
            fetch('/api/notifications/read-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const badge = document.getElementById('notificationCountBadge');
                    if (badge) badge.remove();
                    document.querySelectorAll('.notification-unread-dot').forEach(dot => dot.remove());
                }
            })
            .catch(err => console.error('Error marking notifications as read:', err));
        });
    }

    // 5. Client-side Table Search Filter (for fast dynamic filtering)
    const clientSearchInput = document.getElementById('clientTableSearch');
    if (clientSearchInput) {
        clientSearchInput.addEventListener('keyup', function () {
            const query = this.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.searchable-table-row');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    // 6. Auto-dismiss alerts after 6 seconds
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 6000);

    // 7. Client-side File Upload Optimization & Vercel Payload Protection (4 MB Limit)
    const MAX_ALLOWED_BYTES = 4.0 * 1024 * 1024; // 4.0 MB safe threshold for Vercel 4.5 MB limit

    function compressImageFile(file, maxWidth = 1920, maxHeight = 1920, quality = 0.85) {
        return new Promise((resolve) => {
            if (!file.type.startsWith('image/') || file.size <= 800 * 1024) {
                // No compression needed if already under 800 KB
                resolve(file);
                return;
            }

            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = function (e) {
                const img = new Image();
                img.src = e.target.result;
                img.onload = function () {
                    let width = img.width;
                    let height = img.height;

                    if (width > maxWidth || height > maxHeight) {
                        if (width > height) {
                            height = Math.round((height * maxWidth) / width);
                            width = maxWidth;
                        } else {
                            width = Math.round((width * maxHeight) / height);
                            height = maxHeight;
                        }
                    }

                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    canvas.toBlob(function (blob) {
                        if (!blob || blob.size >= file.size) {
                            resolve(file);
                        } else {
                            const compressedFile = new File([blob], file.name.replace(/\.[^/.]+$/, ".jpg"), {
                                type: 'image/jpeg',
                                lastModified: Date.now()
                            });
                            resolve(compressedFile);
                        }
                    }, 'image/jpeg', quality);
                };
                img.onerror = () => resolve(file);
            };
            reader.onerror = () => resolve(file);
        });
    }

    const uploadInputs = document.querySelectorAll('#certFileInput, #certEditFileInput, .cert-file-input');
    uploadInputs.forEach(input => {
        input.addEventListener('change', async function () {
            const file = this.files[0];
            if (!file) return;

            let feedback = this.parentElement.querySelector('.file-upload-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'file-upload-feedback mt-2 small text-center';
                this.parentElement.appendChild(feedback);
            }

            const submitBtn = this.form ? this.form.querySelector('button[type="submit"]') : null;

            // Handle images: auto-compress high-resolution smartphone / scanner photos
            if (file.type.startsWith('image/')) {
                if (file.size > 800 * 1024) {
                    const originalMB = (file.size / (1024 * 1024)).toFixed(2);
                    feedback.innerHTML = `<span class="text-primary"><i class="bi bi-arrow-repeat spin me-1"></i> Optimizing photo (${originalMB} MB) for fast upload...</span>`;
                    if (submitBtn) submitBtn.disabled = true;

                    try {
                        const optimized = await compressImageFile(file);
                        if (optimized && optimized !== file) {
                            const dt = new DataTransfer();
                            dt.items.add(optimized);
                            this.files = dt.files;
                            const newKB = (optimized.size / 1024).toFixed(0);
                            feedback.innerHTML = `<span class="text-success fw-semibold"><i class="bi bi-check-circle-fill me-1"></i> Photo optimized: ${originalMB} MB &rarr; ${newKB} KB (Ready to submit)</span>`;
                        } else {
                            feedback.innerHTML = `<span class="text-success"><i class="bi bi-check-circle me-1"></i> Ready: ${file.name}</span>`;
                        }
                    } catch (err) {
                        console.error('Image compression error:', err);
                        feedback.innerHTML = `<span class="text-success"><i class="bi bi-check-circle me-1"></i> Selected: ${file.name}</span>`;
                    } finally {
                        if (submitBtn) submitBtn.disabled = false;
                    }
                } else {
                    const sizeKB = (file.size / 1024).toFixed(0);
                    feedback.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i> Ready: ${file.name} (${sizeKB} KB)</span>`;
                    if (submitBtn) submitBtn.disabled = false;
                }
            } 
            // Handle PDFs
            else {
                if (file.size > MAX_ALLOWED_BYTES) {
                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    this.value = ''; // Prevent upload of oversized file
                    feedback.innerHTML = `<div class="alert alert-danger py-2 px-3 mb-0 text-start mt-2">
                        <i class="bi bi-exclamation-triangle-fill me-1"></i>
                        <strong>PDF is too large (${sizeMB} MB):</strong> Vercel serverless has a 4.0 MB limit. Please <a href="https://www.ilovepdf.com/compress_pdf" target="_blank" class="alert-link">compress your PDF</a> or upload an image/screenshot of your certificate.
                    </div>`;
                } else {
                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    feedback.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i> Ready: ${file.name} (${sizeMB} MB)</span>`;
                    if (submitBtn) submitBtn.disabled = false;
                }
            }
        });
    });
});
