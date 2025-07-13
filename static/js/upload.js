// Upload JavaScript for EduRAG Platform

// Upload form handling
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }
});

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
        showAlert('Please select a valid file.', 'error');
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
            
            // Reload uploaded materials
            loadUploadedMaterials();
            
            // Enable chat if this is the first upload
            enableChat();
            
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

// Load uploaded materials
async function loadUploadedMaterials() {
    try {
        const response = await fetch('/api/textbooks/');
        const materials = await response.json();
        
        uploadedMaterials = materials.results || materials;
        displayUploadedMaterials(uploadedMaterials);
        
    } catch (error) {
        console.error('Error loading materials:', error);
        displayUploadedMaterials([]);
    }
}

function displayUploadedMaterials(materials) {
    const container = document.getElementById('uploadedMaterialsList');
    if (!container) return;
    
    if (materials.length === 0) {
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
            <div class="material-item" data-id="${material.id}">
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
    const extension = filename.split('.').pop().toLowerCase();
    switch (extension) {
        case 'pdf': return '📄';
        case 'docx': return '📝';
        case 'txt': return '📄';
        default: return '📁';
    }
}

// Material actions
function viewMaterial(materialId) {
    const material = uploadedMaterials.find(m => m.id === materialId);
    if (material) {
        showAlert(`Viewing: ${material.title}\nSubject: ${material.subject.name}\nGrade: ${material.grade.level}\nStatus: ${material.processing_status}`, 'info');
    }
}

function deleteMaterial(materialId) {
    showConfirm('Are you sure you want to delete this material? This action cannot be undone.', async () => {
        try {
            const response = await fetch(`/api/textbooks/${materialId}/`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showAlert('Material deleted successfully!', 'success');
                loadUploadedMaterials();
            } else {
                showAlert('Failed to delete material. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showAlert('Failed to delete material. Please try again.', 'error');
        }
    });
}

// Enable chat when materials are available
function enableChat() {
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const uploadPrompt = document.getElementById('uploadPrompt');
    
    if (questionInput && askBtn) {
        questionInput.disabled = false;
        askBtn.disabled = false;
        
        if (uploadPrompt) {
            uploadPrompt.style.display = 'none';
        }
    }
}

// Manage subjects and grades
function openManageModal() {
    openModal('manageModal');
}

function closeManageModal() {
    closeModal('manageModal');
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
            // Reload page to update dropdowns
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
            // Reload page to update dropdowns
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

// Utility function to get CSRF token
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

// Auto-refresh materials status
let materialsRefreshInterval;

function startMaterialsRefresh() {
    materialsRefreshInterval = setInterval(() => {
        loadUploadedMaterials();
    }, 10000); // Refresh every 10 seconds
}

function stopMaterialsRefresh() {
    if (materialsRefreshInterval) {
        clearInterval(materialsRefreshInterval);
    }
}

// Start auto-refresh when page loads
document.addEventListener('DOMContentLoaded', function() {
    startMaterialsRefresh();
});

// Stop auto-refresh when page unloads
window.addEventListener('beforeunload', function() {
    stopMaterialsRefresh();
}); 