(function() {
    // ==================== 【1】获取DOM元素引用 ====================
    // 获取AI弹窗容器
    const aiModal = document.getElementById('aiModal');
    // 获取AI按钮
    const aiBtn = document.querySelector('.AI-btn');
    // 获取关闭按钮
    const closeAiModal = document.querySelector('[data-close="aiModal"]');
    // 获取发送按钮
    const sendAiMessage = document.getElementById('sendAiMessage');
    // 获取输入框
    const aiInput = document.getElementById('aiInput');
    // 获取聊天容器
    const aiChatContainer = document.getElementById('aiChatContainer');

    // ==================== 【2】生成唯一会话ID ====================
    // 基于时间戳和随机数生成sessionId
    const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);



    // ==================== 【3】打开AI助手弹窗 ====================
    // 绑定按钮点击事件
    if (aiBtn && aiModal) {
        aiBtn.onclick = function() {
            // 检查用户登录状态
            const username = localStorage.getItem('username');
            // 未登录提示
            if (!username) {
                alert('请先登录后再使用 AI 助手');
                return;
            }
            // 显示弹窗
            aiModal.style.display = 'flex';
        };
    }

    // ==================== 【4】关闭弹窗事件绑定 ====================
    // 关闭按钮点击事件
    if (closeAiModal) {
        closeAiModal.onclick = function() {
            // 隐藏弹窗
            aiModal.style.display = 'none';
        };
    }
    // 点击遮罩层关闭
    if (aiModal) {
        aiModal.addEventListener('click', function(e) {
            // 判断点击目标
            if (e.target === aiModal) aiModal.style.display = 'none';
        });
    }

    // ==================== 【5】消息渲染状态变量 ====================
    //消息是流式传输的，currentAIMessageDiv指向正在更新的消息气泡，方便追加内容
    //currentAIContent缓存已接收的文本，用于markdown解析
    //renderTimer用于防抖，避免每接收一个字都重复渲染，导致卡顿

    // 当前AI消息DOM元素
    let currentAIMessageDiv = null;
    // 当前AI消息内容
    let currentAIContent = '';
    // 渲染定时器
    let renderTimer = null;

    // ==================== 【6】添加消息到聊天区 ====================
    /**
     * 添加消息到聊天区域
     * @param {string} content - 消息内容
     * @param {boolean} isUser - 是否用户消息
     */
    function addMessage(content, isUser) {
        // 检查容器是否存在
        if (!aiChatContainer) return;
        // 创建消息外层div
        const messageDiv = document.createElement('div');
        // 设置消息样式类
        messageDiv.className = `message ${isUser ? 'message-user' : 'message-ai'}`;
        // 创建内容容器
        const messageContent = document.createElement('div');
        // 设置内容样式类
        messageContent.className = 'message-content';
        // 判断消息类型并渲染
        if (isUser) {
            // 用户消息直接显示文本
            messageContent.textContent = content;
        } else {
            // AI消息使用markdown解析
            messageContent.innerHTML = marked.parse(content);
        }
        // 组装消息结构
        messageDiv.appendChild(messageContent);
        // 添加到聊天容器
        aiChatContainer.appendChild(messageDiv);
        // 滚动到底部
        aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
    }

    // ==================== 【7】显示AI思考中状态 ====================
    /**
     * 开始显示AI回复，展示思考中状态
     */
    function startAIMessage() {
        // 检查容器是否存在
        if (!aiChatContainer) return;
        // 创建AI消息div
        currentAIMessageDiv = document.createElement('div');
        // 设置AI消息样式
        currentAIMessageDiv.className = 'message message-ai';
        // 创建内容div
        const messageContent = document.createElement('div');
        // 设置内容样式
        messageContent.className = 'message-content';
        // 显示思考中提示
        messageContent.innerHTML = '<span class="ai-thinking">🤖思考中</span>';
        // 组装结构
        currentAIMessageDiv.appendChild(messageContent);
        // 添加到容器
        aiChatContainer.appendChild(currentAIMessageDiv);
        // 滚动到底部
        aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        // 清空内容缓存
        currentAIContent = '';
    }

    // ==================== 【8】流式追加AI回复内容 ====================
    /**
     * 追加AI回复内容（流式）
     * @param {string} text - 追加的文本
     */
    function appendAIMessage(text) {
        // 检查必要元素
        if (!currentAIMessageDiv || !aiChatContainer) return;
        // 累加内容
        currentAIContent += text;
        // 获取内容元素
        const messageContent = currentAIMessageDiv.querySelector('.message-content');
        // 清除之前的定时器
        clearTimeout(renderTimer);
        // 延迟渲染避免频繁更新
        renderTimer = setTimeout(() => {
            // 解析markdown并显示
            messageContent.innerHTML = marked.parse(currentAIContent);
            // 滚动到底部
            aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        }, 30);
    }

    // ==================== 【9】完成AI消息渲染 ====================
    /**
     * 结束AI消息，完成最终渲染
     */
    function endAIMessage() {
        // 检查消息元素
        if (currentAIMessageDiv) {
            // 获取内容元素
            const messageContent = currentAIMessageDiv.querySelector('.message-content');
            // 最终渲染markdown
            messageContent.innerHTML = marked.parse(currentAIContent);
        }
        // 清除定时器
        clearTimeout(renderTimer);
        // 重置状态变量
        currentAIMessageDiv = null;
        currentAIContent = '';
    }

    // ==================== 【10】滚动聊天区到底部 ====================
    /**
     * 滚动聊天区域到底部
     */
    function scrollToBottom() {
        // 检查容器存在
        if (aiChatContainer) {
            // 设置滚动位置
            aiChatContainer.scrollTop = aiChatContainer.scrollHeight;
        }
    }

    // ==================== 【11】发送消息并处理流式响应 ====================
    // 绑定发送按钮点击事件
    if (sendAiMessage) {
        sendAiMessage.onclick = async function() {
            // 获取输入内容并去空格
            const message = aiInput.value.trim();
            // 空内容校验
            if (!message) { alert('请输入问题'); return; }
            // 显示用户消息
            addMessage(message, true);
            // 清空输入框
            aiInput.value = '';
            // 禁用发送按钮
            sendAiMessage.disabled = true;
            // 异常处理
            try {
                // 发起流式请求
                const response = await fetch('http://localhost:8000/api/ai/stream', {
                    // POST请求
                    method: 'POST',
                    // 设置请求头
                    headers: { 'Content-Type': 'application/json' },
                    // 请求体数据
                    body: JSON.stringify({ message, sessionId, username: localStorage.getItem('username') || '', clientIp: '' })
                });
                // 响应状态检查
                if (!response.ok) {
                    // 抛出错误
                    throw new Error('网络响应失败');
                }
                // 获取流式读取器
                const reader = response.body.getReader();
                // 创建文本解码器
                const decoder = new TextDecoder();
                // 数据缓冲区
                let buffer = '';
                // 显示AI思考中
                startAIMessage();
                // 循环读取流数据
                while (true) {
                    // 读取数据块
                    const { done, value } = await reader.read();
                    // 读取完成退出
                    if (done) break;
                    // 解码数据
                    const chunk = decoder.decode(value, { stream: true });
                    // 累加到缓冲区
                    buffer += chunk;
                    // 按行分割
                    const lines = buffer.split('\n');
                    // 保留未完整行
                    buffer = lines.pop() || '';
                    // 处理每一行数据
                    for (const line of lines) {
                        // 检查数据前缀
                        if (line.startsWith('data: ')) {
                            // 提取数据内容
                            const data = line.slice(6);
                            // 判断是否结束标记
                            if (data === '[DONE]') {
                                // 结束消息渲染
                                endAIMessage();
                            } else {
                                // 尝试解析JSON
                                try {
                                    const parsed = JSON.parse(data);
                                    // 检查内容字段
                                    if (parsed.content) {
                                        // 追加内容
                                        appendAIMessage(parsed.content);
                                    }
                                } catch (e) {
                                    // 解析失败忽略
                                }
                            }
                        }
                    }
                }
            } catch (err) {
                // 输出错误日志
                console.error(err);
                // 结束消息状态
                endAIMessage();
                // 显示错误提示
                addMessage('网络错误，请稍后重试。', false);
            } finally {
                // 恢复发送按钮
                sendAiMessage.disabled = false;
            }
        };
    }

    // ==================== 【12】回车键发送消息 ====================
    // 监听输入框按键事件
    aiInput.addEventListener('keypress', function(e) {
        // 判断是否回车且非Shift
        if (e.key === 'Enter' && !e.shiftKey) {
            // 阻止默认换行
            e.preventDefault();
            // 触发发送按钮
            if (sendAiMessage) {
                sendAiMessage.click();
            }
        }
    });
})();
