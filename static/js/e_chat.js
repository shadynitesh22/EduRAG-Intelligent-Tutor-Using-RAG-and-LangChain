// Enhanced Chat JavaScript for EduRAG Platform
    
    // Global variables
let currentPersona = 'helpful_tutor';
    let auditMode = false;
let chatHistory = [];
let uploadedTextbooks = [];
    
// Initialize chat functionality
    document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 EduRAG Chat Initializing...');
    initializeChat();
    loadChatHistory();
    setupPersonaSelector();
    setupAuditMode();
    loadUploadedTextbooks();
    enableChatInput(); // Enable chat input by default
    refreshTextbookDropdown(); // Refresh dropdown on page load
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
            
            // Update session stats
            updateSessionStats();
            
            // Show feedback modal after a delay
            setTimeout(() => {
                showFeedbackModal(result.query_log_id);
            }, 1000);
            
        } else {
            console.error('❌ Question failed:', result.error);
            addMessage('system', result.error || 'Sorry, I encountered an error. Please try again.');
        }
        
    } catch (error) {
        hideLoading();
        console.error('❌ Ask question error:', error);
        addMessage('system', 'Sorry, I encountered an error. Please check your connection and try again.');
    }
}

// Format AI response text with styling
function formatAIResponse(text) {
    if (!text) return '';
    
    // Convert **bold** text
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* text
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert numbered lists
    text = text.replace(/^(\d+\.\s+)(.*)$/gm, '<div class="list-item numbered"><span class="list-number">$1</span><span class="list-content">$2</span></div>');
    
    // Convert bullet lists
    text = text.replace(/^[-•*]\s+(.*)$/gm, '<div class="list-item bulleted"><span class="list-bullet">•</span><span class="list-content">$1</span></div>');
    
    // Convert headers
    text = text.replace(/^(#{1,6})\s+(.*)$/gm, function(match, hashes, content) {
        const level = hashes.length;
        return `<h${level} class="ai-header">${content}</h${level}>`;
    });
    
    // Convert code blocks
    text = text.replace(/```([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>');
    
    // Convert inline code
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Convert line breaks to proper paragraphs
    text = text.replace(/\n\n/g, '</p><p>');
    text = text.replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not already wrapped
    if (!text.startsWith('<')) {
        text = '<p>' + text + '</p>';
    }
    
    return text;
}

// Update addMessage to use formatted text for AI responses
function addMessage(type, content, sources = null, responseTime = null) {
    console.log('💬 Adding message:', type, content.substring(0, 50) + '...');
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error('❌ Chat messages container not found!');
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    let html = '';
    
    if (type === 'user') {
        html = `
            <div class="message-content">
                <div class="message-text">${escapeHtml(content)}</div>
                <div class="message-meta">
                    <span class="message-time">${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
        `;
    } else if (type === 'ai') {
        const formattedContent = formatAIResponse(content);
        html = `
            <div class="message-content">
                <div class="message-text ai-formatted">${formattedContent}</div>
                ${sources && sources.length > 0 ? `
                    <div class="message-sources">
                        <div class="sources-header">📚 Sources:</div>
                        ${sources.map(source => `
                            <div class="source-item">
                                <div class="source-title">${source.textbook_title || 'Unknown Source'}</div>
                                <div class="source-meta">
                                    ${source.subject || 'Unknown'} | Grade ${source.grade || 'Unknown'} | 
                                    Similarity: ${(source.similarity_score * 100).toFixed(1)}%
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                <div class="message-meta">
                    <span class="message-time">${new Date().toLocaleTimeString()}</span>
                    ${responseTime ? `<span class="response-time">${responseTime}ms</span>` : ''}
                </div>
            </div>
        `;
    } else {
        html = `
            <div class="message-content">
                <div class="message-text">${escapeHtml(content)}</div>
            </div>
        `;
    }
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom smoothly
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
    
    // Add to history
    chatHistory.push({
        type: type,
        content: content,
        timestamp: new Date().toISOString()
    });
    
    // Update chat history below
    renderChatHistory();
    
    console.log('✅ Message added successfully');
}

function setupPersonaSelector() {
    console.log('🎭 Setting up persona selector...');
    const personaBtns = document.querySelectorAll('.persona-btn');
    console.log('Found persona buttons:', personaBtns.length);
    
    personaBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            personaBtns.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update current persona
            currentPersona = this.dataset.persona;
            
            showAlert(`Switched to ${this.textContent} tutor mode`, 'info');
        });
    });
}

function setupAuditMode() {
    console.log('🔍 Setting up audit mode...');
    const auditToggle = document.getElementById('auditModeToggle');
        const auditInfo = document.getElementById('auditInfo');
        const auditStatus = document.getElementById('auditStatus');
        
    if (auditToggle) {
        auditToggle.addEventListener('change', function() {
            auditMode = this.checked;
            
            if (auditMode) {
            auditInfo.style.display = 'block';
            auditStatus.className = 'status-indicator status-online';
                showAlert('Audit mode enabled - all interactions are being logged', 'info');
        } else {
            auditInfo.style.display = 'none';
            auditStatus.className = 'status-indicator status-offline';
                showAlert('Audit mode disabled', 'info');
            }
        });
    }
}

function showLoading(message = 'Loading...') {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.querySelector('p').textContent = message;
        loading.style.display = 'block';
    }
}

function hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
        loading.style.display = 'none';
    }
}

function showAlert(message, type = 'info') {
    console.log('📢 Showing alert:', type, message);
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // Add to page
    document.body.appendChild(alertDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

function showConfirm(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

async function loadChatHistory() {
    try {
        const response = await fetch('/api/chat-history/');
        const result = await response.json();
        
        if (response.ok && result.history) {
            result.history.forEach(item => {
                addMessage('user', item.question);
                addMessage('ai', item.response);
            });
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

async function clearChat() {
    showConfirm('Are you sure you want to clear the chat history?', async () => {
        try {
            const response = await fetch('/api/clear-chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (response.ok) {
                const chatMessages = document.getElementById('chatMessages');
                if (chatMessages) {
                    chatMessages.innerHTML = `
                        <div class="message system">
                            <strong>Welcome to EduRAG!</strong><br>
                            Upload your study material above, then ask me anything about your studies. I can help with various subjects and adapt my teaching style to your needs.
                            <div class="audit-info" id="auditInfo" style="display: none;">
                                <br><strong>🔍 Audit Mode Active:</strong> All interactions are being logged for analysis and improvement.
                            </div>
                        </div>
                    `;
                }
                
                chatHistory = [];
                showAlert('Chat history cleared!', 'success');
            }
        } catch (error) {
            console.error('Clear chat error:', error);
            showAlert('Failed to clear chat history', 'error');
            }
        });
    }

async function updateSessionStats() {
    try {
        const response = await fetch('/api/session-stats/');
        const stats = await response.json();
        
        if (response.ok) {
            const questionsAsked = document.getElementById('questionsAsked');
            const avgResponseTime = document.getElementById('avgResponseTime');
            const avgRating = document.getElementById('avgRating');
            const sourcesUsed = document.getElementById('sourcesUsed');
            
            if (questionsAsked) questionsAsked.textContent = stats.questions_asked || 0;
            if (avgResponseTime) avgResponseTime.textContent = `${stats.avg_response_time || 0}ms`;
            if (avgRating) avgRating.textContent = stats.avg_rating || '0.0';
            if (sourcesUsed) sourcesUsed.textContent = stats.sources_used || 0;
        }
    } catch (error) {
        console.error('Error updating session stats:', error);
    }
}

async function loadUploadedTextbooks() {
    console.log('📚 Loading uploaded textbooks...');
    try {
        const response = await fetch('/api/textbooks/');
        console.log('Textbooks API response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('📚 API response data:', data);
            
            // Handle paginated response
            const textbooks = data.results || data;
            console.log('📚 Found textbooks:', textbooks.length);
            console.log('Textbooks data:', textbooks);
            
            uploadedTextbooks = textbooks;
            
            // Populate textbook filter dropdown
            const textbookFilter = document.getElementById('textbookFilter');
            if (textbookFilter) {
                // Clear existing options except the first one
                textbookFilter.innerHTML = '<option value="">All Textbooks</option>';
                
                // Add textbook options
                textbooks.forEach(textbook => {
                    const option = document.createElement('option');
                    option.value = textbook.id;
                    // Handle nested subject and grade objects
                    const subjectName = textbook.subject?.name || textbook.subject_name || 'Unknown';
                    const gradeLevel = textbook.grade?.level || textbook.grade_level || 'Unknown';
                    option.textContent = `${textbook.title} (${subjectName}, Grade ${gradeLevel})`;
                    textbookFilter.appendChild(option);
                });
                console.log('✅ Textbook filter populated');
            } else {
                console.error('❌ Textbook filter not found!');
            }
            
            // Update uploaded materials list
            updateUploadedMaterialsList(textbooks);
            
            // Enable chat input if we have textbooks
            if (textbooks.length > 0) {
                enableChatInput();
                console.log('✅ Chat enabled due to textbooks available');
            } else {
                console.log('⚠️ No textbooks available, chat may be limited');
            }
            
        } else {
            console.error('❌ Failed to load textbooks:', response.status, response.text);
        }
    } catch (error) {
        console.error('❌ Error loading textbooks:', error);
    }
}

function updateUploadedMaterialsList(textbooks) {
    console.log('📋 Updating materials list with', textbooks.length, 'textbooks');
    const materialsList = document.getElementById('uploadedMaterialsList');
    if (!materialsList) {
        console.error('❌ Materials list container not found!');
        return;
    }
    
    if (textbooks.length === 0) {
        materialsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-text">No materials uploaded yet</div>
                <div class="empty-state-hint">Upload your first study material to get started</div>
            </div>
        `;
        console.log('📋 Materials list: Empty state shown');
    } else {
        materialsList.innerHTML = textbooks.map(textbook => {
            // Handle nested subject and grade objects
            const subjectName = textbook.subject?.name || textbook.subject_name || 'Unknown';
            const gradeLevel = textbook.grade?.level || textbook.grade_level || 'Unknown';
            const createdDate = new Date(textbook.uploaded_at || textbook.created_at).toLocaleDateString();
            
            return `
                <div class="material-card" data-textbook-id="${textbook.id}">
                    <div class="material-header">
                        <h4 class="material-title">${textbook.title}</h4>
                        <button class="btn btn-small btn-danger" onclick="deleteTextbook('${textbook.id}')">Delete</button>
                    </div>
                    <div class="material-meta">
                        <span class="material-subject">${subjectName}</span>
                        <span class="material-grade">Grade ${gradeLevel}</span>
                        <span class="material-date">${createdDate}</span>
                    </div>
                    <div class="material-status">
                        <span class="status-indicator status-online"></span>
                        <span>Processed and ready</span>
                    </div>
                </div>
            `;
        }).join('');
        console.log('📋 Materials list: Updated with', textbooks.length, 'textbooks');
    }
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
            showAlert('Textbook deleted successfully', 'success');
            loadUploadedTextbooks(); // Reload the list
            refreshTextbookDropdown(); // Refresh dropdown after deletion
                } else {
            showAlert('Failed to delete textbook', 'error');
        }
    } catch (error) {
        console.error('Delete textbook error:', error);
        showAlert('Failed to delete textbook', 'error');
    }
}

function showFeedbackModal(queryLogId) {
    console.log('📝 Opening feedback modal for query:', queryLogId);
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        
        // Store the query log ID for submission
        modal.dataset.queryLogId = queryLogId;
        
        // Reset rating
        document.querySelectorAll('.star').forEach(star => star.classList.remove('active'));
        document.getElementById('ratingLabel').textContent = 'Select a rating';
        document.getElementById('feedbackComment').value = '';
    }
}

function openFeedbackModal(responseText, responseTime) {
    console.log('📝 Opening feedback modal...');
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        
        // Store feedback data
        modal.dataset.responseText = responseText;
        modal.dataset.responseTime = responseTime;
        
        // Reset rating
        document.querySelectorAll('.star').forEach(star => star.classList.remove('active'));
        document.getElementById('ratingLabel').textContent = 'Select a rating';
        document.getElementById('feedbackComment').value = '';
    }
}

function closeFeedbackModal() {
    const modal = document.getElementById('feedbackModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

async function submitFeedback() {
    console.log('📝 Submitting feedback...');
    
    const modal = document.getElementById('feedbackModal');
    const selectedRating = document.querySelector('.star.active');
    const comment = document.getElementById('feedbackComment').value.trim();
    
    if (!selectedRating) {
        showAlert('Please select a rating.', 'error');
        return;
    }
    
    const rating = parseInt(selectedRating.dataset.rating);
    const queryLogId = modal.dataset.queryLogId;
    const responseText = modal.dataset.responseText;
    const responseTime = modal.dataset.responseTime;
    
    const feedbackData = {
        rating: rating,
        comment: comment
    };
    
    // If we have a query log ID, use it; otherwise use direct feedback
    if (queryLogId) {
        feedbackData.query_log_id = queryLogId;
    } else if (responseText) {
        feedbackData.response_text = responseText;
        feedbackData.response_time = responseTime;
    }
    
    try {
        const response = await fetch('/api/feedback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(feedbackData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Thank you for your feedback!', 'success');
            closeFeedbackModal();
        } else {
            showAlert(result.error || 'Failed to submit feedback.', 'error');
        }
        
    } catch (error) {
        console.error('❌ Feedback submission error:', error);
        showAlert('Failed to submit feedback. Please try again.', 'error');
    }
}

// Feedback modal star selection
const stars = document.querySelectorAll('.rating-stars .star');
stars.forEach(star => {
    star.addEventListener('click', function() {
        stars.forEach(s => s.classList.remove('selected'));
        this.classList.add('selected');
    });
});

// Helpful buttons
const helpfulBtns = document.querySelectorAll('.helpful-btn');
helpfulBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        helpfulBtns.forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
    });
});

// Close modal
const closeBtn = document.querySelector('#feedbackModal .close');
if (closeBtn) {
    closeBtn.onclick = function() {
        const modal = document.getElementById('feedbackModal');
        modal.style.display = 'none';
        modal.classList.remove('show');
    };
}

function exportChat() {
    const chatData = JSON.stringify(chatHistory, null, 2);
    const blob = new Blob([chatData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showAlert('Chat exported successfully!', 'success');
}

async function loadTopics() {
    try {
        const response = await fetch('/api/topics/');
        const result = await response.json();
        
        if (response.ok) {
            const topicsList = document.getElementById('topicsList');
            if (topicsList) {
                topicsList.innerHTML = result.topics.map(topic => `
                    <div class="topic-item">
                        <div class="topic-name">${topic.name}</div>
                        <div class="topic-count">${topic.count} questions</div>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading topics:', error);
    }
}

async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics/');
        const result = await response.json();
        
        if (response.ok) {
            const metricsList = document.getElementById('metricsList');
            if (metricsList) {
                metricsList.innerHTML = result.metrics.map(metric => `
                    <div class="metric-item">
                        <div class="metric-name">${metric.name}</div>
                        <div class="metric-value">${metric.value} ${metric.unit}</div>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

// Add missing functions
async function loadHistory() {
    console.log('📜 Loading history...');
    try {
        const response = await fetch('/api/history/');
        const data = await response.json();
        
        const historyList = document.getElementById('historyList');
        if (historyList && data.history) {
            if (data.history.length === 0) {
                historyList.innerHTML = '<div class="history-item empty">No previous questions</div>';
            } else {
                historyList.innerHTML = data.history.map(item => `
                    <div class="history-item" data-question="${escapeHtml(item.question)}">
                        <div class="history-item-question">${escapeHtml(item.question)}</div>
                        <div class="history-item-meta">
                            ${item.persona || 'Helpful'} | ${item.subject || 'All'} | ${item.timestamp}
                        </div>
                        ${item.response_time ? `<div class="history-item-rating">Response: ${item.response_time}ms</div>` : ''}
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('❌ Load history error:', error);
    }
}

function openManageModal() {
    console.log('🔧 Opening manage modal...');
    const modal = document.getElementById('manageModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
    }
}

function closeManageModal() {
    console.log('🔧 Closing manage modal...');
    const modal = document.getElementById('manageModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

async function addSubject() {
    console.log('📚 Adding subject...');
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
            location.reload(); // Reload to update dropdowns
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
    console.log('📚 Adding grade...');
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
            location.reload(); // Reload to update dropdowns
        } else {
            const result = await response.json();
            showAlert(result.error || 'Failed to add grade.', 'error');
        }
    } catch (error) {
        console.error('❌ Add grade error:', error);
        showAlert('Failed to add grade. Please try again.', 'error');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Export functions for global access
window.askQuestion = askQuestion;
window.clearChat = clearChat;
window.exportChat = exportChat;
window.loadTopics = loadTopics;
window.loadMetrics = loadMetrics;
window.loadHistory = loadHistory;
window.openManageModal = openManageModal;
window.closeManageModal = closeManageModal;
window.addSubject = addSubject;
window.addGrade = addGrade;
window.deleteTextbook = deleteTextbook;
window.showFeedbackModal = showFeedbackModal;
window.closeFeedbackModal = closeFeedbackModal;
window.submitFeedback = submitFeedback;

// After addMessage and after a successful AI response, update chat history below chat
function renderChatHistory() {
    const historyList = document.getElementById('chatHistoryList');
    if (!historyList) return;
    historyList.innerHTML = '';
    chatHistory.forEach((msg, idx) => {
        const div = document.createElement('div');
        div.className = `history-msg history-msg-${msg.type}`;
        div.innerHTML = `<span class='history-type'>${msg.type === 'user' ? 'You' : 'AI'}:</span> <span class='history-content'>${escapeHtml(msg.content)}</span> <span class='history-time'>${new Date(msg.timestamp).toLocaleTimeString()}</span>`;
        historyList.appendChild(div);
    });
}

// Patch addMessage to also update chat history below
const origAddMessage = addMessage;
addMessage = function(type, content, sources = null, responseTime = null) {
    origAddMessage(type, content, sources, responseTime);
    renderChatHistory();
};

// Ensure chatMessages scrolls smoothly
const chatMessages = document.getElementById('chatMessages');
if (chatMessages) {
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

// Show feedback modal after every AI response
function showFeedbackModal(queryLogId) {
    const modal = document.getElementById('feedbackModal');
    if (!modal) return;
    modal.style.display = 'block';
    modal.classList.add('show');
    modal.dataset.queryLogId = queryLogId;
}

async function refreshTextbookDropdown() {
    try {
        const response = await fetch('/api/textbooks/');
        const data = await response.json();
        const dropdown = document.getElementById('textbookFilter');
        if (!dropdown) return;
        dropdown.innerHTML = '<option value="">All Textbooks</option>';
        if (Array.isArray(data)) {
            data.forEach(book => {
                dropdown.innerHTML += `<option value="${book.id}">${book.title} (${book.subject.name}, Grade ${book.grade.level})</option>`;
            });
        } else if (data.results) {
            data.results.forEach(book => {
                dropdown.innerHTML += `<option value="${book.id}">${book.title} (${book.subject.name}, Grade ${book.grade.level})</option>`;
            });
        }
    } catch (e) {
        console.error('Failed to refresh textbook dropdown:', e);
    }
}

function openChatHistoryModal() {
    console.log('📜 Opening chat history modal...');
    const modal = document.getElementById('chatHistoryModal');
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        loadChatHistory();
    }
}

function closeChatHistoryModal() {
    console.log('📜 Closing chat history modal...');
    const modal = document.getElementById('chatHistoryModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

async function loadChatHistory() {
    console.log('📜 Loading chat history...');
    const dateFilter = document.getElementById('historyDateFilter')?.value || 'all';
    const historyContent = document.getElementById('chatHistoryContent');
    
    if (!historyContent) {
        console.error('❌ Chat history content container not found!');
        return;
    }
    
    historyContent.innerHTML = '<div class="loading">Loading chat history...</div>';
    
    try {
        const response = await fetch(`/api/feedback/?date_filter=${dateFilter}`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            const historyHtml = data.results.map(item => `
                <div class="history-item">
                    <div class="history-question">${escapeHtml(item.query_text)}</div>
                    <div class="history-answer">${formatAIResponse(item.response_text)}</div>
                    <div class="history-meta">
                        <span class="history-time">${new Date(item.created_at).toLocaleString()}</span>
                        ${item.rating ? `<span class="history-rating">Rating: ${item.rating}/5</span>` : ''}
                        ${item.response_time ? `<span class="history-response-time">${item.response_time}ms</span>` : ''}
                    </div>
                </div>
            `).join('');
            historyContent.innerHTML = historyHtml;
        } else {
            historyContent.innerHTML = '<div class="empty-state">No chat history found.</div>';
        }
    } catch (error) {
        console.error('❌ Load chat history error:', error);
        historyContent.innerHTML = '<div class="error">Failed to load chat history.</div>';
    }
}

function exportChatHistory() {
    console.log('📤 Exporting chat history...');
    const dateFilter = document.getElementById('historyDateFilter')?.value || 'all';
    
    fetch(`/api/feedback/export/?date_filter=${dateFilter}`)
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_history_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        console.error('❌ Export chat history error:', error);
        showAlert('Failed to export chat history.', 'error');
    });
}

console.log('📜 EduRAG Chat JavaScript loaded and ready!'); 