(function() {
    // 管理员后台AI助手专用
    const aiChatContainer = document.getElementById('adminAiChatContainer');
    const sendAiMessage = document.getElementById('sendAdminAiMessage');
    const aiInput = document.getElementById('adminAiInput');

    // 生成新的 sessionId（每次刷新页面都新建，不保留历史）
    const sessionId = 'admin_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // 管理员模式配置
    const ADMIN_PASSWORD = 'admin123'; // 管理员口令
    let aiState = 'normal'; // normal, waiting_password, admin
    let adminSessionTimeout = null;

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

    // 处理管理员模式（异步函数）
    async function handleAdminMode(message) {
        if (aiState === 'waiting_password') {
            if (message === ADMIN_PASSWORD) {
                aiState = 'admin';
                adminSessionTimeout = setTimeout(() => {
                    aiState = 'normal';
                    addMessage('管理员会话已超时，已退出管理员模式。', false);
                }, 300000);
                return { handled: true, reply: '口令验证成功，已进入管理员模式。\n\n现在您可以使用自然语言与 AI 助手交互，例如：\n- "新增用户 test1 密码 123456"\n- "删除用户 test1"\n- "查询所有用户"\n- "修改用户 test1 为 admin"\n\n输入"退出管理员模式"退出。' };
            } else if (message === '取消') {
                aiState = 'normal';
                return { handled: true, reply: '已取消管理员模式。' };
            } else {
                return { handled: true, reply: '口令错误，请重新输入。如需取消，请输入"取消"。' };
            }
        } else if (aiState === 'admin') {
            if (adminSessionTimeout) {
                clearTimeout(adminSessionTimeout);
                adminSessionTimeout = setTimeout(() => {
                    aiState = 'normal';
                    addMessage('管理员会话已超时，已退出管理员模式。', false);
                }, 300000);
            }

            if (message === '退出管理员模式' || message === '取消') {
                aiState = 'normal';
                if (adminSessionTimeout) {
                    clearTimeout(adminSessionTimeout);
                    adminSessionTimeout = null;
                }
                return { handled: true, reply: '已退出管理员模式。' };
            }

            return { handled: false };
        }

        return { handled: false };
    }

    if (sendAiMessage) {
        sendAiMessage.onclick = async function() {
            const message = aiInput.value.trim();
            if (!message) { alert('请输入问题'); return; }

            addMessage(message, true);
            aiInput.value = '';
            sendAiMessage.disabled = true;

            // 检查是否触发管理员模式
            if (aiState === 'normal' && message === '管理员模式') {
                aiState = 'waiting_password';
                addMessage('请输入管理员口令：', false);
                sendAiMessage.disabled = false;
                return;
            }

            // 处理管理员模式（口令验证阶段）
            if (aiState === 'waiting_password') {
                const adminResult = await handleAdminMode(message);
                if (adminResult.handled) {
                    addMessage(adminResult.reply, false);
                    sendAiMessage.disabled = false;
                    return;
                }
            }

            // 管理员模式 - 使用 AI 解析复杂指令
            if (aiState === 'admin') {
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
                return;
            }

            // 普通模式 - 查询电影数据
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
