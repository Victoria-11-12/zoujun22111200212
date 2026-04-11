(function() {
        const chartModal = document.getElementById('chartModal');
        const chartBtn = document.querySelector('.chart-btn');
        const closeChartModal = document.querySelector('[data-close="chartModal"]');
        const generateChartBtn = document.getElementById('generateChart');
        const chartInput = document.getElementById('chartInput');
        const chartCanvasContainer = document.getElementById('chartCanvasContainer');

        // sessionId
        const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        if (chartBtn) {
            chartBtn.onclick = function() {
                const username = localStorage.getItem('username');
                if (!username) {
                    alert('请先登录后再使用在线绘图功能');
                    return;
                }
                chartModal.style.display = 'flex';
            };
        }

        if (closeChartModal) {
            closeChartModal.onclick = function() {
                chartModal.style.display = 'none';
            };
        }

        if (chartModal) {
            chartModal.addEventListener('click', function(e) {
                if (e.target === chartModal) {
                    chartModal.style.display = 'none';
                }
            });
        }

        // 添加消息气泡（文字提示）
        function addChartMessage(content, isUser) {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'chart-msg ' + (isUser ? 'chart-msg-user' : 'chart-msg-ai');
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            msgDiv.appendChild(contentDiv);
            chartCanvasContainer.appendChild(msgDiv);
            chartCanvasContainer.scrollTop = chartCanvasContainer.scrollHeight;
            return msgDiv;
        }

        // 添加 iframe 图表
        function addChartIframe(htmlContent) {
            const wrapper = document.createElement('div');
            wrapper.className = 'chart-iframe-wrapper';
            const iframe = document.createElement('iframe');
            iframe.style.width = '100%';
            iframe.style.height = '450px';
            iframe.style.border = 'none';
            iframe.style.borderRadius = '8px';
            iframe.setAttribute('srcdoc', htmlContent);
            wrapper.appendChild(iframe);
            chartCanvasContainer.appendChild(wrapper);
            chartCanvasContainer.scrollTop = chartCanvasContainer.scrollHeight;
        }

        if (generateChartBtn) {
            generateChartBtn.onclick = async function() {
                const message = chartInput.value.trim();
                if (!message) {
                    alert('请输入图表描述或数据');
                    return;
                }

                // 显示用户输入
                addChartMessage(message, true);
                chartInput.value = '';
                generateChartBtn.disabled = true;

                // 创建 AI 回复气泡
                const aiMsgDiv = addChartMessage('🤔 思考中...', false);

                try {
                    const response = await fetch('http://localhost:8000/api/chart/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message, sessionId: sessionId })
                    });

                    if (!response.ok) {
                        throw new Error('网络响应失败');
                    }

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '';
                    let fullContent = '';

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
                                    continue;
                                } else {
                                    try {
                                        const parsed = JSON.parse(data);
                                        if (parsed.type === 'chart' && parsed.chart_html) {
                                            // 收到图表 HTML → 用 iframe 渲染
                                            aiMsgDiv.textContent = '';
                                            addChartIframe(parsed.chart_html);
                                        } else if (parsed.content) {
                                            // 收到文字内容 → 更新气泡
                                            fullContent += parsed.content;
                                            const contentEl = aiMsgDiv.querySelector('.message-content');
                                            if (contentEl) {
                                                contentEl.textContent = fullContent;
                                            }
                                            chartCanvasContainer.scrollTop = chartCanvasContainer.scrollHeight;
                                        }
                                    } catch (e) {
                                    }
                                }
                            }
                        }
                    }
                } catch (err) {
                    console.error(err);
                    const contentEl = aiMsgDiv.querySelector('.message-content');
                    if (contentEl) {
                        contentEl.textContent = '网络错误，请稍后重试。';
                    }
                } finally {
                    generateChartBtn.disabled = false;
                }
            };
        }

        if (chartInput) {
            chartInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    generateChartBtn.click();
                }
            });
        }
    })();