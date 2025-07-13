// Upload JavaScript for EduRAG Platform

// Global variables
let uploadedMaterials = [];

// Upload form handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Upload.js initializing...');
    
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
        console.log('✅ Upload form listener attached');
    }
    
    // Load initial materials
    loadUploadedMaterials();
    
    // Start polling for processing status
    startProcessingPolling();
    
    console.log('✅ Upload.js initialized');
});

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// File validation function
function validateFile(file) {
    const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const maxSize = 200 * 1024 * 1024; // 200MB
    
    if (!file) {
        return { isValid: false, message: 'No file selected' };
    }
    
    if (!allowedTypes.includes(file.type)) {
        return { isValid: false, message: 'Invalid file type. Please upload PDF, DOCX, or TXT files only.' };
    }
    
    if (file.size > maxSize) {
        return { isValid: false, message: 'File size too large. Maximum size is 200MB.' };
    }
    
    return { isValid: true, message: 'File is valid' };
}

async function handleUpload(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const file = formData.get('file');
    const title = formData.get('title');
    const subjectId = formData.get('subject_id');
    const gradeId = formData.get('grade_id');
    
    // Validate form
    if (!file || !title || !subjectId || !gradeId) {
        showAlert('Please fill in all required fields.', 'error');
        return;
    }
    
    // Validate file
    const validation = validateFile(file);
    if (!validation.isValid) {
        showAlert(validation.message, 'error');
        return;
    }
    
    // Show loading
    showLoading('Uploading your content...');
    
    try {
        const response = await fetch('/api/upload-content/', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            hideLoading();
            showAlert('Content uploaded successfully! Processing will begin shortly.', 'success');
            
            // Reset form
            e.target.reset();
            document.getElementById('fileValidation').style.display = 'none';
            
            // Add the new material to the list immediately with processing status
            addMaterialToList(result);
            
            // Start polling for this specific material
            pollMaterialStatus(result.id);
            
            // Enable chat if this is the first upload
            enableChat();
            
            // Refresh the textbook dropdown in chat
            if (typeof refreshTextbookDropdown === 'function') {
                refreshTextbookDropdown();
            }
            
        } else {
            hideLoading();
            showAlert(result.error || 'Upload failed. Please try again.', 'error');
        }
        
    } catch (error) {
        hideLoading();
        console.error('Upload error:', error);
        showAlert('Upload failed. Please check your connection and try again.', 'error');
    }
}

// Add material to list immediately after upload
function addMaterialToList(material) {
    const container = document.getElementById('uploadedMaterialsList');
    if (!container) return;
    
    // Remove empty state if it exists
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const statusClass = getStatusClass(material.processing_status);
    const statusIcon = getStatusIcon(material.processing_status);
    const fileIcon = getFileIcon(material.file);
    
    const materialHtml = `
        <div class="material-item" data-id="${material.id}" data-status="${material.processing_status}">
            <div class="material-info">
                <div class="material-icon">${fileIcon}</div>
                <div class="material-details">
                    <div class="material-title">${material.title}</div>
                    <div class="material-meta">
                        <span>${material.subject.name}</span>
                        <span>Grade ${material.grade.level}</span>
                        <span>${formatDate(material.uploaded_at)}</span>
                    </div>
                </div>
            </div>
            <div class="material-status">
                <span class="status-badge ${statusClass}">
                    ${statusIcon} ${material.processing_status}
                </span>
            </div>
            <div class="material-actions">
                <button class="material-action-btn" onclick="viewMaterial('${material.id}')">View</button>
                <button class="material-action-btn delete" onclick="deleteMaterial('${material.id}')">Delete</button>
            </div>
        </div>
    `;
    
    // Insert at the beginning of the list
    container.insertAdjacentHTML('afterbegin', materialHtml);
}

// Poll material status until processing is complete
async function pollMaterialStatus(materialId) {
    const maxAttempts = 60; // 5 minutes with 5-second intervals
    let attempts = 0;
    
    const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
            const response = await fetch(`/api/textbooks/${materialId}/`);
            if (response.ok) {
                const material = await response.json();
                
                // Update the material item in the list
                updateMaterialStatus(materialId, material.processing_status);
                
                // If processing is complete or failed, stop polling
                if (material.processing_status === 'completed' || material.processing_status === 'failed') {
                    clearInterval(pollInterval);
                    
                    if (material.processing_status === 'completed') {
                        showAlert(`Processing completed for: ${material.title}`, 'success');
                        // Refresh textbook dropdown when processing completes
                        if (typeof refreshTextbookDropdown === 'function') {
                            refreshTextbookDropdown();
                        }
                        // Reload materials list to show updated status
                        loadUploadedMaterials();
                    } else if (material.processing_status === 'failed') {
                        showAlert(`Processing failed for: ${material.title}`, 'error');
                        // Reload materials list to show updated status
                        loadUploadedMaterials();
                    }
                }
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
        
        // Stop polling after max attempts
        if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            console.log('Polling timeout for material:', materialId);
        }
    }, 5000); // Poll every 5 seconds
}

// Update material status in the UI
function updateMaterialStatus(materialId, status) {
    const materialItem = document.querySelector(`[data-id="${materialId}"]`);
    if (materialItem) {
        const statusBadge = materialItem.querySelector('.status-badge');
        if (statusBadge) {
            const statusClass = getStatusClass(status);
            const statusIcon = getStatusIcon(status);
            
            statusBadge.className = `status-badge ${statusClass}`;
            statusBadge.innerHTML = `${statusIcon} ${status}`;
        }
        
        // Update data attribute
        materialItem.setAttribute('data-status', status);
    }
}

// Start polling for all processing materials
function startProcessingPolling() {
    const processingMaterials = document.querySelectorAll('[data-status="processing"], [data-status="pending"]');
    processingMaterials.forEach(material => {
        const materialId = material.getAttribute('data-id');
        if (materialId) {
            pollMaterialStatus(materialId);
        }
    });
}

// Load uploaded materials
async function loadUploadedMaterials() {
    try {
        console.log('📚 Loading uploaded materials...');
        const response = await fetch('/api/textbooks/');
        const materials = await response.json();
        
        console.log('📚 API response:', materials);
        
        uploadedMaterials = materials.results || materials;
        console.log('📚 Processed materials:', uploadedMaterials);
        
        displayUploadedMaterials(uploadedMaterials);
        
        // Start polling for processing materials
        startProcessingPolling();
        
        // Refresh textbook dropdown
        if (typeof refreshTextbookDropdown === 'function') {
            refreshTextbookDropdown();
        }
        
    } catch (error) {
        console.error('❌ Error loading materials:', error);
        displayUploadedMaterials([]);
    }
}

function displayUploadedMaterials(materials) {
    console.log('📚 Displaying materials:', materials);
    const container = document.getElementById('uploadedMaterialsList');
    if (!container) {
        console.error('❌ Container not found: uploadedMaterialsList');
        return;
    }
    
    console.log('📚 Container found, materials count:', materials.length);
    
    if (materials.length === 0) {
        console.log('📚 No materials, showing empty state');
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-text">No materials uploaded yet</div>
                <div class="empty-state-hint">Upload your first study material to get started</div>
            </div>
        `;
        return;
    }
    
    let html = '';
    materials.forEach(material => {
        const statusClass = getStatusClass(material.processing_status);
        const statusIcon = getStatusIcon(material.processing_status);
        const fileIcon = getFileIcon(material.file);
        
        html += `
            <div class="material-item" data-id="${material.id}" data-status="${material.processing_status}">
                <div class="material-info">
                    <div class="material-icon">${fileIcon}</div>
                    <div class="material-details">
                        <div class="material-title">${material.title}</div>
                        <div class="material-meta">
                            <span>${material.subject.name}</span>
                            <span>Grade ${material.grade.level}</span>
                            <span>${formatDate(material.uploaded_at)}</span>
                        </div>
                    </div>
                </div>
                <div class="material-status">
                    <span class="status-badge ${statusClass}">
                        ${statusIcon} ${material.processing_status}
                    </span>
                </div>
                <div class="material-actions">
                    <button class="material-action-btn" onclick="viewMaterial('${material.id}')">View</button>
                    <button class="material-action-btn delete" onclick="deleteMaterial('${material.id}')">Delete</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Utility functions
function getStatusClass(status) {
    switch (status) {
        case 'pending': return 'pending';
        case 'processing': return 'processing';
        case 'completed': return 'completed';
        case 'failed': return 'failed';
        default: return 'pending';
    }
}

function getStatusIcon(status) {
    switch (status) {
        case 'pending': return '⏳';
        case 'processing': return '🔄';
        case 'completed': return '✅';
        case 'failed': return '❌';
        default: return '⏳';
    }
}

function getFileIcon(filename) {
    if (!filename) return '📄';
    
    const extension = filename.split('.').pop().toLowerCase();
    switch (extension) {
        case 'pdf': return '📕';
        case 'docx': return '📘';
        case 'txt': return '📄';
        default: return '📄';
    }
}

function viewMaterial(materialId) {
    console.log('Viewing material:', materialId);
}

async function deleteMaterial(materialId) {
    if (!confirm('Are you sure you want to delete this material?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/textbooks/${materialId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (response.ok) {
            showAlert('Material deleted successfully!', 'success');
            loadUploadedMaterials(); // Reload the list
        } else {
            showAlert('Failed to delete material.', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showAlert('Failed to delete material.', 'error');
    }
}

function enableChat() {
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const uploadPrompt = document.getElementById('uploadPrompt');
    
    if (questionInput) questionInput.disabled = false;
    if (askBtn) askBtn.disabled = false;
    if (uploadPrompt) uploadPrompt.style.display = 'none';
}

function openManageModal() {
    const modal = document.getElementById('manageModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
    }
}

function closeManageModal() {
    const modal = document.getElementById('manageModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

async function addSubject() {
    const nameInput = document.getElementById('newSubjectName');
    const name = nameInput.value.trim();
    
    if (!name) {
        showAlert('Please enter a subject name.', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/subjects/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ name: name })
        });
        
        if (response.ok) {
            showAlert('Subject added successfully!', 'success');
            nameInput.value = '';
            location.reload();
        } else {
            const result = await response.json();
            showAlert(result.error || 'Failed to add subject.', 'error');
        }
    } catch (error) {
        console.error('Add subject error:', error);
        showAlert('Failed to add subject. Please try again.', 'error');
    }
}

async function addGrade() {
    const levelInput = document.getElementById('newGradeLevel');
    const level = parseInt(levelInput.value);
    
    if (!level || level < 1 || level > 12) {
        showAlert('Please enter a valid grade level (1-12).', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/grades/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ level: level })
        });
        
        if (response.ok) {
            showAlert('Grade added successfully!', 'success');
            levelInput.value = '';
            location.reload();
        } else {
            const result = await response.json();
            showAlert(result.error || 'Failed to add grade.', 'error');
        }
    } catch (error) {
        console.error('Add grade error:', error);
        showAlert('Failed to add grade. Please try again.', 'error');
    }
}

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// showAlert function is defined in base.js

// showLoading and hideLoading functions are defined in base.js

function startMaterialsRefresh() {
    // Refresh materials every 30 seconds
    setInterval(loadUploadedMaterials, 30000);
}

function stopMaterialsRefresh() {
    // Stop refreshing materials
    clearInterval(materialsRefreshInterval);
}

// Make functions globally available
window.viewMaterial = viewMaterial;
window.deleteMaterial = deleteMaterial;
window.openManageModal = openManageModal;
window.closeManageModal = closeManageModal;
window.addSubject = addSubject;
window.addGrade = addGrade; 