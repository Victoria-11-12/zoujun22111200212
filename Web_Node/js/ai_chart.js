(function() {
        // 从环境变量配置读取 FastAPI 地址，未配置时回退到本地地址
        const _FASTAPI_URL = (window.__CONFIG__ && window.__CONFIG__.FASTAPI_URL !== undefined) ? window.__CONFIG__.FASTAPI_URL : 'http://localhost:8000';

        const chartModal = document.getElementById('chartModal');
        const chartBtn = document.querySelector('.chart-btn');
        const closeChartModal = document.querySelector('[data-close="chartModal"]');
        const generateChartBtn = document.getElementById('generateChart');
        const chartInput = document.getElementById('chartInput');
        const chartCanvasContainer = document.getElementById('chartCanvasContainer');

        // sessionId
        const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        // ==================== AI图表使用次数限制配置 ====================
        // 定义不同角色的AI图表使用次数上限，-1表示无限制
        const CHART_LIMITS = {
            'user': 3,      // 普通用户：3次
            'analyst': 5,   // 分析师：5次
            'admin': -1      // 管理员：无限制
        };
        // 24小时的时间戳（毫秒）
        const ONE_DAY_MS = 24 * 60 * 60 * 1000;

        /**
         * 获取当前用户的AI图表使用数据（包含次数和最后重置时间）
         * 如果超过24小时未重置，自动重置次数
         * @returns {Object} 包含count和lastReset的对象
         */
        function getChartUsageData() {
            const username = localStorage.getItem('username');
            if (!username) return { count: 0, lastReset: Date.now() };
            const key = 'ai_chart_usage_' + username;
            const stored = localStorage.getItem(key);
            if (!stored) {
                return { count: 0, lastReset: Date.now() };
            }
            try {
                const data = JSON.parse(stored);
                const now = Date.now();
                // 检查是否超过24小时，超过则重置
                if (now - data.lastReset > ONE_DAY_MS) {
                    const newData = { count: 0, lastReset: now };
                    localStorage.setItem(key, JSON.stringify(newData));
                    return newData;
                }
                return data;
            } catch (e) {
                // 解析失败时返回默认值
                return { count: 0, lastReset: Date.now() };
            }
        }

        /**
         * 增加AI图表使用次数
         * 每次生成图表成功后调用
         */
        function incrementChartUsage() {
            const username = localStorage.getItem('username');
            if (!username) return;
            const key = 'ai_chart_usage_' + username;
            const data = getChartUsageData();
            data.count += 1;
            localStorage.setItem(key, JSON.stringify(data));
        }

        /**
         * 检查AI图表使用限制
         * @returns {Object} 包含allowed(是否允许)、current(当前次数)、limit(上限)的对象
         */
        function checkChartLimit() {
            const role = localStorage.getItem('role') || 'user';
            const limit = CHART_LIMITS[role] || CHART_LIMITS['user'];
            // -1表示无限制
            if (limit === -1) return { allowed: true, current: 0, limit: -1 };
            const data = getChartUsageData();
            return { allowed: data.count < limit, current: data.count, limit: limit };
        }

        if (chartBtn) {
            chartBtn.onclick = function() {
                const username = localStorage.getItem('username');
                if (!username) {
                    alert('请先登录后再使用在线绘图功能');
                    return;
                }
                // 检查使用次数限制
                const limitCheck = checkChartLimit();
                if (!limitCheck.allowed) {
                    alert('今日AI绘图次数已用完（上限' + limitCheck.limit + '次），请24小时后再试');
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

        // 添加 iframe 图表 + 新窗口打开链接
        function addChartIframe(htmlContent) {
            const wrapper = document.createElement('div');
            wrapper.className = 'chart-iframe-wrapper';
            
            const iframe = document.createElement('iframe');
            iframe.style.width = '100%';
            iframe.style.height = '400px';
            iframe.style.border = 'none';
            iframe.style.borderRadius = '8px';
            iframe.setAttribute('srcdoc', htmlContent);
            wrapper.appendChild(iframe);
            
            // 新窗口打开链接
            const linkRow = document.createElement('div');
            linkRow.className = 'chart-link-row';
            const openLink = document.createElement('a');
            openLink.href = '#';
            openLink.className = 'chart-open-link';
            openLink.textContent = '🔗 新窗口打开完整图表';
            openLink.onclick = function(e) {
                e.preventDefault();
                const win = window.open('', '_blank');
                win.document.write(htmlContent);
                win.document.close();
            };
            linkRow.appendChild(openLink);
            wrapper.appendChild(linkRow);
            
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
                // 发起请求前立即计数，防止快速重复点击绕过限制
                incrementChartUsage();

                // 创建 AI 回复气泡
                const aiMsgDiv = addChartMessage('🤔 思考中...', false);

                try {
                    const response = await fetch(_FASTAPI_URL + '/api/chart/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message, sessionId: sessionId, username: localStorage.getItem('username') || '' })
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