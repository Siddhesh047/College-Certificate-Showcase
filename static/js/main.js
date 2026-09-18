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
});
