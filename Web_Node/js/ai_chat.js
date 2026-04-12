(function() {
    const aiModal = document.getElementById('aiModal');
    const aiBtn = document.querySelector('.AI-btn');
    const closeAiModal = document.querySelector('[data-close="aiModal"]');
    const sendAiMessage = document.getElementById('sendAiMessage');
    const aiInput = document.getElementById('aiInput');
    const aiChatContainer = document.getElementById('aiChatContainer');

    // 生成新的 sessionId（每次刷新页面都新建，不保留历史）
    const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    if (aiBtn && aiModal) {
        aiBtn.onclick = function() {
            const username = localStorage.getItem('username');
            if (!username) {
                alert('请先登录后再使用 AI 助手');
                return;
            }
            aiModal.style.display = 'flex';
        };
    }

    if (closeAiModal) {
        closeAiModal.onclick = function() {
            aiModal.style.display = 'none';
        };
    }

    if (aiModal) {
        aiModal.addEventListener('click', function(e) {
            if (e.target === aiModal) aiModal.style.display = 'none';
        });
    }

    let currentAIMessageDiv = null;
    let currentAIContent = '';
    let renderTimer = null;

    function addMessage(content, isUser) {
        if (!aiChatContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'message-user' : 'message-ai'}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        if (isUser) {
            messageContent.textContent = content;
        } else {
            messageContent.innerHTML = marked.parse(content);
        }

        messageDiv.appendChild(messageContent);
        aiChatContainer.appendChild(messageDiv);
        aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
    }

    function startAIMessage() {
        if (!aiChatContainer) return;
        
        currentAIMessageDiv = document.createElement('div');
        currentAIMessageDiv.className = 'message message-ai';
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = '<span class="ai-thinking">🤖思考中</span>';
        currentAIMessageDiv.appendChild(messageContent);
        aiChatContainer.appendChild(currentAIMessageDiv);
        aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        currentAIContent = '';
    }

    function appendAIMessage(text) {
        if (!currentAIMessageDiv || !aiChatContainer) return;
        currentAIContent += text;
        const messageContent = currentAIMessageDiv.querySelector('.message-content');

        clearTimeout(renderTimer);
        renderTimer = setTimeout(() => {
            messageContent.innerHTML = marked.parse(currentAIContent);
            aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        }, 30);
    }

    function endAIMessage() {
        if (currentAIMessageDiv) {
            const messageContent = currentAIMessageDiv.querySelector('.message-content');
            messageContent.innerHTML = marked.parse(currentAIContent);
        }
        clearTimeout(renderTimer);
        currentAIMessageDiv = null;
        currentAIContent = '';
    }

    function scrollToBottom() {
        if (aiChatContainer) {
            aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        }
    }

    if (sendAiMessage) {
        sendAiMessage.onclick = async function() {
            const message = aiInput.value.trim();
            if (!message) { alert('请输入问题'); return; }

            addMessage(message, true);
            aiInput.value = '';
            sendAiMessage.disabled = true;

            try {
                const response = await fetch('http://localhost:8000/api/ai/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, sessionId, username: localStorage.getItem('username') || '', clientIp: '' })
                });

                if (!response.ok) {
                    throw new Error('网络响应失败');
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                startAIMessage();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;

                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') {
                                endAIMessage();
                            } else {
                                try {
                                    const parsed = JSON.parse(data);
                                    if (parsed.content) {
                                        appendAIMessage(parsed.content);
                                    }
                                } catch (e) {
                                }
                            }
                        }
                    }
                }
            } catch (err) {
                console.error(err);
                endAIMessage();
                addMessage('网络错误，请稍后重试。', false);
            } finally {
                sendAiMessage.disabled = false;
            }
        };
    }

    aiInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (sendAiMessage) {
                sendAiMessage.click();
            }
        }
    });
})();
