// Enhanced Chat JavaScript for EduRAG Platform
    
// CRITICAL: Make functions globally available immediately
window.askQuestion = function() {
    console.log('❓ Asking question...');
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) {
        showAlert('Please enter a question.', 'error');
        return;
    }

    // Get selected textbook
    const textbookFilter = document.getElementById('textbookFilter');
    const selectedTextbookId = textbookFilter ? textbookFilter.value : '';
    
    console.log('Question:', question);
    console.log('Selected textbook ID:', selectedTextbookId);
    
    // Show loading
    showLoading('AI is thinking...');
    
    // Add user message to chat
    addMessage('user', question);
    
    // Clear input
    questionInput.value = '';
    
    fetch('/api/ask/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            question: question,
            type: 'rag',
            persona: currentPersona || 'helpful_tutor',
            textbook_id: selectedTextbookId || ''
        })
    })
    .then(response => response.json())
    .then(result => {
        hideLoading();
        
        if (result.answer) {
            console.log('✅ Question answered successfully');
            // Add AI response to chat
            addMessage('ai', result.answer, result.sources, result.response_time_ms);
            
            // Store query log ID for rating
            currentQueryLogId = result.query_log_id;
            
            // Show feedback modal after a short delay
            setTimeout(() => {
                if (typeof showFeedbackModal === 'function') {
                    showFeedbackModal(result.query_log_id);
                }
            }, 1000);
            
            // Update session stats
            if (typeof updateSessionStats === 'function') {
                updateSessionStats();
            }
            
        } else {
            console.error('❌ Question failed:', result.error);
            addMessage('error', `Error: ${result.error || 'Failed to get response'}`);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('❌ Question error:', error);
        addMessage('error', 'Network error. Please try again.');
    });
};

window.clearChat = function() {
    console.log('🗑️ Clearing chat...');
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="message system">
                <strong>Welcome to EduRAG!</strong><br>
                Upload your study material above, then ask me anything about your studies. I can help with various subjects and adapt my teaching style to your needs.
            </div>
        `;
    }
};

window.exportChat = function() {
    console.log('📤 Exporting chat...');
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        const content = chatMessages.innerText;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_export_${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
};

window.showFeedbackModal = function(queryLogId) {
    console.log('📝 Opening feedback modal for query:', queryLogId);
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        
        // Reset rating
        document.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
        const labelElement = document.getElementById('ratingLabel');
        if (labelElement) labelElement.textContent = 'Select a rating';
        
        // Clear comment
        const commentElement = document.getElementById('feedbackComment');
        if (commentElement) commentElement.value = '';
        
        // Store the query log ID
        modal.dataset.queryLogId = queryLogId;
    }
};

window.closeFeedbackModal = function() {
    console.log('📝 Closing feedback modal');
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        modal.dataset.queryLogId = '';
    }
};

window.submitFeedback = function() {
    console.log('📝 Submitting feedback...');
    
    const modal = document.getElementById('feedbackModal');
    const queryLogId = modal ? modal.dataset.queryLogId : null;
    
    if (!queryLogId) {
        showAlert('No active query to rate.', 'error');
        return;
    }
    
    const activeStar = document.querySelector('.star.active');
    if (!activeStar) {
        showAlert('Please select a rating.', 'error');
        return;
    }
    
    const rating = parseInt(activeStar.dataset.rating);
    const comment = document.getElementById('feedbackComment').value.trim();
    
    fetch('/api/feedback/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            query_log_id: queryLogId,
            rating: rating,
            feedback_text: comment
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('Thank you for your feedback!', 'success');
            closeFeedbackModal();
            // Update session stats if the function exists
            if (typeof updateSessionStats === 'function') {
                updateSessionStats();
            }
        } else {
            showAlert(result.error || 'Failed to submit feedback.', 'error');
        }
    })
    .catch(error => {
        console.error('❌ Submit feedback error:', error);
        showAlert('Failed to submit feedback.', 'error');
    });
};

// Global variables (some may be declared in base.js)
let chatHistory = [];
let uploadedTextbooks = [];
let currentQueryLogId = null;
    
// Initialize chat functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 EduRAG Chat Initializing...');
    initializeChat();
    loadChatHistory();
    setupPersonaSelector();
    setupAuditMode();
    // loadUploadedTextbooks(); // Removed - handled by upload.js
    enableChatInput(); // Enable chat input by default
    
    // CRITICAL: Refresh dropdown immediately
    setTimeout(() => {
        refreshTextbookDropdown();
    }, 100);
    
    loadSessionStats(); // Load real session stats
    setupRatingSystem();
    console.log('✅ EduRAG Chat Initialized');
});

function initializeChat() {
    console.log('🔧 Initializing chat...');
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    
    console.log('Question input found:', !!questionInput);
    console.log('Ask button found:', !!askBtn);
    
    if (questionInput && askBtn) {
        // Enable enter key to submit
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
        
        // Enable button click
        askBtn.addEventListener('click', askQuestion);
        console.log('✅ Chat event listeners attached');
    } else {
        console.error('❌ Chat elements not found!');
    }
}

function setupRatingSystem() {
    // Rating stars event listeners
    document.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', function() {
            const rating = parseInt(this.dataset.rating);
            
            // Update star display
            document.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
            for (let i = 1; i <= rating; i++) {
                const starElement = document.querySelector(`[data-rating="${i}"]`);
                if (starElement) starElement.classList.add('active');
            }
            
            // Update label
            const labels = ['Select a rating', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'];
            const labelElement = document.getElementById('ratingLabel');
            if (labelElement) labelElement.textContent = labels[rating];
        });
    });
}

function enableChatInput() {
    console.log('🔓 Enabling chat input...');
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const uploadPrompt = document.getElementById('uploadPrompt');
    
    if (questionInput) {
        questionInput.disabled = false;
        console.log('✅ Question input enabled');
    }
    if (askBtn) {
        askBtn.disabled = false;
        console.log('✅ Ask button enabled');
    }
    if (uploadPrompt) {
        uploadPrompt.style.display = 'none';
        console.log('✅ Upload prompt hidden');
    }
}

function disableChatInput() {
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const uploadPrompt = document.getElementById('uploadPrompt');
    
    if (questionInput) questionInput.disabled = true;
    if (askBtn) askBtn.disabled = true;
    if (uploadPrompt) uploadPrompt.style.display = 'block';
}

async function askQuestion() {
    console.log('❓ Asking question...');
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) {
        showAlert('Please enter a question.', 'error');
        return;
    }

    // Get selected textbook
    const textbookFilter = document.getElementById('textbookFilter');
    const selectedTextbookId = textbookFilter ? textbookFilter.value : '';
    
    console.log('Question:', question);
    console.log('Selected textbook ID:', selectedTextbookId);
    
    // Show loading
    showLoading('AI is thinking...');
    
    // Add user message to chat
    addMessage('user', question);
    
    // Clear input
    questionInput.value = '';
    
    try {
        const response = await fetch('/api/ask/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                question: question,
                type: 'rag',
                persona: currentPersona,
                textbook_id: selectedTextbookId || ''
            })
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (response.ok) {
            console.log('✅ Question answered successfully');
            // Add AI response to chat
            addMessage('ai', result.answer, result.sources, result.response_time_ms);
            
            // Store query log ID for rating
            currentQueryLogId = result.query_log_id;
            
            // Show feedback modal after a short delay
            setTimeout(() => {
                showFeedbackModal(result.query_log_id);
            }, 1000);
            
            // Update session stats
            updateSessionStats();
            
        } else {
            console.error('❌ Question failed:', result.error);
            addMessage('error', `Error: ${result.error || 'Failed to get response'}`);
        }
        
    } catch (error) {
        hideLoading();
        console.error('❌ Question error:', error);
        addMessage('error', 'Network error. Please try again.');
    }
}

window.formatAIResponse = function(text) {
    // Format the AI response for better readability
    return text
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
};

window.addMessage = function(type, content, sources = null, responseTime = null) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    let messageContent = '';
    
    if (type === 'user') {
        messageContent = `
            <div class="message-content">
                <strong>You:</strong> ${escapeHtml(content)}
            </div>
        `;
    } else if (type === 'ai') {
        messageContent = `
            <div class="message-content">
                <strong>AI Tutor:</strong> ${formatAIResponse(content)}
            </div>
        `;
        
        if (sources && sources.length > 0) {
            messageContent += `
                <div class="message-sources">
                    <strong>Sources:</strong>
                    <ul>
                        ${sources.map(source => `
                            <li>${source.textbook_title} (${source.subject}, Grade ${source.grade}) - Relevance: ${(source.similarity_score * 100).toFixed(1)}%</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
        
        if (responseTime) {
            messageContent += `
                <div class="message-meta">
                    <small>Response time: ${responseTime}ms</small>
                </div>
            `;
        }
    } else if (type === 'error') {
        messageContent = `
            <div class="message-content error">
                <strong>Error:</strong> ${escapeHtml(content)}
            </div>
        `;
    }
    
    messageDiv.innerHTML = messageContent;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
};

function setupPersonaSelector() {
    const personaButtons = document.querySelectorAll('.persona-btn');
    personaButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            personaButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            // Update current persona
            currentPersona = this.dataset.persona;
            console.log('🎭 Persona changed to:', currentPersona);
        });
    });
}

function setupAuditMode() {
    const auditToggle = document.getElementById('auditModeToggle');
    const auditInfo = document.getElementById('auditInfo');
    
    if (auditToggle) {
        auditToggle.addEventListener('change', function() {
            auditMode = this.checked;
            if (auditInfo) {
                auditInfo.style.display = auditMode ? 'block' : 'none';
            }
            console.log('🔍 Audit mode:', auditMode ? 'enabled' : 'disabled');
        });
    }
}

// showLoading and hideLoading functions are defined in base.js

// showAlert function is defined in base.js

function showConfirm(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

async function loadChatHistory() {
    try {
        const response = await fetch('/api/feedback/');
        const data = await response.json();
        
        if (data.results) {
            chatHistory = data.results;
            console.log('📜 Loaded chat history:', chatHistory.length, 'items');
        }
    } catch (error) {
        console.error('❌ Load chat history error:', error);
    }
}

async function clearChat() {
    console.log('🗑️ Clearing chat...');
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="message system">
                <strong>Welcome to EduRAG!</strong><br>
                Upload your study material above, then ask me anything about your studies. I can help with various subjects and adapt my teaching style to your needs.
            </div>
        `;
    }
    
    // Clear chat history from server
    try {
        await fetch('/tutor/clear-chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
    } catch (error) {
        console.error('❌ Clear chat error:', error);
    }
}

async function updateSessionStats() {
    try {
        const response = await fetch('/api/session-stats/');
        const stats = await response.json();
        
        // Update stats display
        const questionsAsked = document.getElementById('questionsAsked');
        const avgResponseTime = document.getElementById('avgResponseTime');
        const avgRating = document.getElementById('avgRating');
        const sourcesUsed = document.getElementById('sourcesUsed');
        
        if (questionsAsked) questionsAsked.textContent = stats.total_questions || 0;
        if (avgResponseTime) avgResponseTime.textContent = `${Math.round(stats.avg_response_time || 0)}ms`;
        if (avgRating) avgRating.textContent = (stats.avg_rating || 0).toFixed(1);
        if (sourcesUsed) sourcesUsed.textContent = stats.total_sources || 0;
        
        console.log('📊 Session stats updated');
    } catch (error) {
        console.error('❌ Update session stats error:', error);
    }
}

async function loadSessionStats() {
    await updateSessionStats();
}

async function loadUploadedTextbooks() {
    try {
        const response = await fetch('/api/textbooks/');
        const data = await response.json();
        
        uploadedTextbooks = data.results || data;
        updateUploadedMaterialsList(uploadedTextbooks);
        
        console.log('📚 Loaded textbooks:', uploadedTextbooks.length);
    } catch (error) {
        console.error('❌ Load textbooks error:', error);
        uploadedTextbooks = [];
    }
}

function addUploadedTextbook(book) {
    uploadedTextbooks.unshift(book);
    updateUploadedMaterialsList(uploadedTextbooks);
    refreshTextbookDropdown();
}

function updateUploadedMaterialsList(textbooks) {
    const container = document.getElementById('uploadedMaterialsList');
    if (!container) return;
    
    if (textbooks.length === 0) {
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
    textbooks.forEach(book => {
        const statusClass = getStatusClass(book.processing_status);
        const statusIcon = getStatusIcon(book.processing_status);
        
        html += `
            <div class="material-item" data-id="${book.id}">
                <div class="material-info">
                    <div class="material-icon">📚</div>
                    <div class="material-details">
                        <div class="material-title">${book.title}</div>
                        <div class="material-meta">
                            <span>${book.subject.name}</span>
                            <span>Grade ${book.grade.level}</span>
                            <span>${new Date(book.uploaded_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
                <div class="material-status">
                    <span class="status-badge ${statusClass}">
                        ${statusIcon} ${book.processing_status}
                    </span>
                </div>
                <div class="material-actions">
                    <button class="material-action-btn" onclick="viewTextbook('${book.id}')">View</button>
                    <button class="material-action-btn delete" onclick="deleteTextbook('${book.id}')">Delete</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

async function deleteTextbook(textbookId) {
    if (!confirm('Are you sure you want to delete this textbook?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/textbooks/${textbookId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (response.ok) {
            showAlert('Textbook deleted successfully!', 'success');
            loadUploadedTextbooks();
            refreshTextbookDropdown();
        } else {
            showAlert('Failed to delete textbook.', 'error');
        }
    } catch (error) {
        console.error('❌ Delete textbook error:', error);
        showAlert('Failed to delete textbook.', 'error');
    }
}

// FEEDBACK MODAL FUNCTIONS - THESE ARE THE MISSING ONES!
function showFeedbackModal(queryLogId) {
    console.log('📝 Opening feedback modal for query:', queryLogId);
    currentQueryLogId = queryLogId;
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        
        // Reset rating
        document.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
        const labelElement = document.getElementById('ratingLabel');
        if (labelElement) labelElement.textContent = 'Select a rating';
        
        // Clear comment
        const commentElement = document.getElementById('feedbackComment');
        if (commentElement) commentElement.value = '';
    }
}

function closeFeedbackModal() {
    console.log('📝 Closing feedback modal');
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
    currentQueryLogId = null;
}

async function submitFeedback() {
    console.log('📝 Submitting feedback...');
    
    if (!currentQueryLogId) {
        showAlert('No active query to rate.', 'error');
        return;
    }
    
    const activeStar = document.querySelector('.star.active');
    if (!activeStar) {
        showAlert('Please select a rating.', 'error');
        return;
    }
    
    const rating = parseInt(activeStar.dataset.rating);
    const comment = document.getElementById('feedbackComment').value.trim();
    
    try {
        const response = await fetch('/api/feedback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                query_log_id: currentQueryLogId,
                rating: rating,
                feedback_text: comment
            })
        });
        
        if (response.ok) {
            showAlert('Thank you for your feedback!', 'success');
            closeFeedbackModal();
            updateSessionStats();
        } else {
            const result = await response.json();
            showAlert(result.error || 'Failed to submit feedback.', 'error');
        }
    } catch (error) {
        console.error('❌ Submit feedback error:', error);
        showAlert('Failed to submit feedback.', 'error');
    }
}

function exportChat() {
    console.log('📤 Exporting chat...');
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        const content = chatMessages.innerText;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_export_${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

async function loadTopics() {
    try {
        const response = await fetch('/api/topics/');
        const topics = await response.json();
        console.log('📚 Loaded topics:', topics);
    } catch (error) {
        console.error('❌ Load topics error:', error);
    }
}

async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics/');
        const metrics = await response.json();
        console.log('📈 Loaded metrics:', metrics);
    } catch (error) {
        console.error('❌ Load metrics error:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/tutor/chat-history/');
        const history = await response.json();
        console.log('📜 Loaded history:', history);
    } catch (error) {
        console.error('❌ Load history error:', error);
    }
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
        console.error('❌ Add subject error:', error);
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
        console.error('❌ Add grade error:', error);
        showAlert('Failed to add grade. Please try again.', 'error');
    }
}

window.escapeHtml = function(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

// getCSRFToken function is defined in base.js

function getStatusClass(status) {
    switch (status) {
        case 'pending': return 'pending';
        case 'processing': return 'processing';
        case 'completed': return 'completed';
        case 'failed': return 'failed';
        default: return 'pending';
    }
}

window.getStatusIcon = function(status) {
    switch (status) {
        case 'pending': return '⏳';
        case 'processing': return '🔄';
        case 'completed': return '✅';
        case 'failed': return '❌';
        default: return '⏳';
    }
};

window.refreshTextbookDropdown = async function() {
    console.log('🔄 Refreshing textbook dropdown...');
    const dropdown = document.getElementById('textbookFilter');
    if (!dropdown) {
        console.error('❌ Dropdown not found: textbookFilter');
        return;
    }
    try {
        const response = await fetch('/api/textbooks/');
        const data = await response.json();
        console.log('📚 Dropdown API response:', data);
        
        const textbooks = data.results || data;
        console.log('📚 Textbooks for dropdown:', textbooks);
        
        dropdown.innerHTML = '<option value="">All Textbooks</option>';
        textbooks.forEach(book => {
            const status = book.processing_status;
            const statusIcon = getStatusIcon(status);
            const option = document.createElement('option');
            option.value = book.id;
            option.textContent = `${book.title} (${book.subject.name}, Grade ${book.grade.level}) ${statusIcon} [${status}]`;
            dropdown.appendChild(option);
        });
        console.log('📚 Textbook dropdown refreshed with', textbooks.length, 'books');
    } catch (error) {
        console.error('❌ Refresh dropdown error:', error);
    }
};

function openChatHistoryModal() {
    const modal = document.getElementById('chatHistoryModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        loadChatHistory();
    }
}

function closeChatHistoryModal() {
    const modal = document.getElementById('chatHistoryModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

// CRITICAL: Make ALL functions globally available
window.askQuestion = askQuestion;
window.clearChat = clearChat;
window.exportChat = exportChat;
window.openManageModal = openManageModal;
window.closeManageModal = closeManageModal;
window.addSubject = addSubject;
window.addGrade = addGrade;
window.openChatHistoryModal = openChatHistoryModal;
window.closeChatHistoryModal = closeChatHistoryModal;
window.showFeedbackModal = showFeedbackModal;
window.closeFeedbackModal = closeFeedbackModal;
window.submitFeedback = submitFeedback;
window.viewTextbook = function(id) { console.log('Viewing textbook:', id); };
window.deleteTextbook = deleteTextbook; 