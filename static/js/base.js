// Base JavaScript for EduRAG Platform

// Global variables
let currentPersona = 'helpful_tutor';
let auditMode = false;
let uploadedMaterials = [];

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showAlert(message, type = 'info') {
    Swal.fire({
        title: type.charAt(0).toUpperCase() + type.slice(1),
        text: message,
        icon: type,
        confirmButtonColor: '#2563eb',
        confirmButtonText: 'OK'
    });
}

function showConfirm(message, callback) {
    Swal.fire({
        title: 'Confirm',
        text: message,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#2563eb',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes',
        cancelButtonText: 'No'
    }).then((result) => {
        if (result.isConfirmed) {
            callback();
        }
    });
}

function showLoading(message = 'Processing...') {
    Swal.fire({
        title: message,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
}

function hideLoading() {
    Swal.close();
}

// File validation
function validateFile(file) {
    const maxSize = 200 * 1024 * 1024; // 200MB
    const allowedTypes = ['.txt', '.pdf', '.docx'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    const validation = {
        isValid: true,
        errors: [],
        warnings: []
    };
    
    // Check file type
    if (!allowedTypes.includes(fileExtension)) {
        validation.isValid = false;
        validation.errors.push('File type not supported. Please upload PDF, DOCX, or TXT files.');
    }
    
    // Check file size
    if (file.size > maxSize) {
        validation.isValid = false;
        validation.errors.push('File size exceeds 200MB limit.');
    } else if (file.size > 50 * 1024 * 1024) { // 50MB warning
        validation.warnings.push('Large file detected. Upload may take longer.');
    }
    
    return validation;
}

function displayFileValidation(validation, file) {
    const validationDiv = document.getElementById('fileValidation');
    validationDiv.style.display = 'block';
    
    let html = '';
    let className = '';
    
    if (!validation.isValid) {
        className = 'invalid';
        html = '<strong>❌ File validation failed:</strong><ul>';
        validation.errors.forEach(error => {
            html += `<li>${error}</li>`;
        });
        html += '</ul>';
    } else if (validation.warnings.length > 0) {
        className = 'warning';
        html = '<strong>⚠️ File validation warnings:</strong><ul>';
        validation.warnings.forEach(warning => {
            html += `<li>${warning}</li>`;
        });
        html += '</ul>';
    } else {
        className = 'valid';
        html = `<strong>✅ File validated successfully</strong><br>`;
        html += `<div class="file-info">`;
        html += `<span class="file-info-icon">📄</span>`;
        html += `<span class="file-info-text">${file.name} (${formatFileSize(file.size)})</span>`;
        html += `</div>`;
    }
    
    validationDiv.className = `file-validation ${className}`;
    validationDiv.innerHTML = html;
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('EduRAG Platform initialized');
    
    // Initialize file upload area
    initializeFileUpload();
    
    // Initialize persona selector
    initializePersonaSelector();
    
    // Initialize audit mode toggle
    initializeAuditMode();
    
    // Load initial data
    loadUploadedMaterials();
    
    // Set up keyboard shortcuts
    setupKeyboardShortcuts();
});

// File upload initialization
function initializeFileUpload() {
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('contentFile');
    
    if (fileUploadArea && fileInput) {
        // Click to upload
        fileUploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Drag and drop
        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('dragover');
        });
        
        fileUploadArea.addEventListener('dragleave', () => {
            fileUploadArea.classList.remove('dragover');
        });
        
        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        });
        
        // File selection
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }
}

function handleFileSelect(file) {
    const validation = validateFile(file);
    displayFileValidation(validation, file);
    
    // Update upload button state
    const uploadBtn = document.querySelector('#uploadForm button[type="submit"]');
    if (uploadBtn) {
        uploadBtn.disabled = !validation.isValid;
    }
}

// Persona selector initialization
function initializePersonaSelector() {
    const personaBtns = document.querySelectorAll('.persona-btn');
    
    personaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            personaBtns.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            btn.classList.add('active');
            
            // Update current persona
            currentPersona = btn.dataset.persona;
            
            console.log('Persona changed to:', currentPersona);
        });
    });
}

// Audit mode initialization
function initializeAuditMode() {
    const auditToggle = document.getElementById('auditModeToggle');
    const auditInfo = document.getElementById('auditInfo');
    const auditStatus = document.getElementById('auditStatus');
    
    if (auditToggle) {
        auditToggle.addEventListener('change', () => {
            auditMode = auditToggle.checked;
            
            if (auditMode) {
                auditInfo.style.display = 'block';
                auditStatus.className = 'status-indicator status-online';
            } else {
                auditInfo.style.display = 'none';
                auditStatus.className = 'status-indicator status-offline';
            }
            
            console.log('Audit mode:', auditMode ? 'enabled' : 'disabled');
        });
    }
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter to submit question
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const questionInput = document.getElementById('questionInput');
            const askBtn = document.getElementById('askBtn');
            
            if (questionInput && askBtn && !askBtn.disabled) {
                e.preventDefault();
                askQuestion();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                closeModal(modal.id);
            });
        }
    });
}

// Export functions
function exportChat() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        const messages = chatMessages.querySelectorAll('.message');
        let exportText = 'EduRAG Chat Export\n';
        exportText += 'Generated: ' + new Date().toLocaleString() + '\n\n';
        
        messages.forEach(message => {
            const isUser = message.classList.contains('user');
            const isAssistant = message.classList.contains('assistant');
            const isSystem = message.classList.contains('system');
            
            let prefix = '';
            if (isUser) prefix = 'You: ';
            else if (isAssistant) prefix = 'EduRAG: ';
            else if (isSystem) prefix = 'System: ';
            
            exportText += prefix + message.textContent.trim() + '\n\n';
        });
        
        // Create and download file
        const blob = new Blob([exportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'edrag-chat-export.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showAlert('Chat exported successfully!', 'success');
    }
}

// Clear chat function
function clearChat() {
    showConfirm('Are you sure you want to clear the chat history?', () => {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            // Keep only the welcome message
            const welcomeMessage = chatMessages.querySelector('.message.system');
            chatMessages.innerHTML = '';
            if (welcomeMessage) {
                chatMessages.appendChild(welcomeMessage);
            }
        }
        showAlert('Chat cleared successfully!', 'success');
    });
} 