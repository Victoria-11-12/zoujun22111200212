(function() {
    // 管理员后台AI助手专用
    const aiChatContainer = document.getElementById('adminAiChatContainer');
    const sendAiMessage = document.getElementById('sendAdminAiMessage');
    const aiInput = document.getElementById('adminAiInput');

    // 生成新的 sessionId（每次刷新页面都新建，不保留历史）
    const sessionId = 'admin_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    let currentAIMessageDiv = null;
    let currentAIContent = '';
    let renderTimer = null;

    function addMessage(content, isUser) {
        if (!aiChatContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${isUser ? 'ai-message-user' : 'ai-message-ai'}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'ai-message-content';

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
        currentAIMessageDiv.className = 'ai-message ai-message-ai';
        const messageContent = document.createElement('div');
        messageContent.className = 'ai-message-content';
        messageContent.innerHTML = '<span class="ai-thinking">🤖思考中</span>';
        currentAIMessageDiv.appendChild(messageContent);
        aiChatContainer.appendChild(currentAIMessageDiv);
        aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        currentAIContent = '';
    }

    function appendAIMessage(text) {
        if (!currentAIMessageDiv || !aiChatContainer) return;
        currentAIContent += text;
        const messageContent = currentAIMessageDiv.querySelector('.ai-message-content');

        clearTimeout(renderTimer);
        renderTimer = setTimeout(() => {
            messageContent.innerHTML = marked.parse(currentAIContent);
            aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        }, 30);
    }

    function endAIMessage() {
        if (currentAIMessageDiv) {
            const messageContent = currentAIMessageDiv.querySelector('.ai-message-content');
            messageContent.innerHTML = marked.parse(currentAIContent);
        }
        clearTimeout(renderTimer);
        currentAIMessageDiv = null;
        currentAIContent = '';
    }

    if (sendAiMessage) {
        sendAiMessage.onclick = async function() {
            const message = aiInput.value.trim();
            if (!message) { alert('请输入问题'); return; }

            addMessage(message, true);
            aiInput.value = '';
            sendAiMessage.disabled = true;

            // 管理员后台直接使用管理员AI接口
            try {
                const response = await fetch('http://localhost:8000/api/admin/ai/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, sessionId, username: localStorage.getItem('username') || '' })
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

    if (aiInput) {
        aiInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (sendAiMessage) {
                    sendAiMessage.click();
                }
            }
        });
    }
})();
