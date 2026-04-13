// 质量评估模块
(function() {
    // API 基础URL
    const API_BASE = 'http://localhost:8000';

    // DOM 元素
    const startEvalBtn = document.getElementById('startEvalBtn');
    const progressSection = document.getElementById('progressSection');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const lowScoreTableBody = document.getElementById('lowScoreTableBody');

    // 图表实例
    let scoreDistChart = null;
    let dimensionRadarChart = null;

    // 初始化
    function init() {
        bindEvents();
        initCharts();
    }

    // 绑定事件
    function bindEvents() {
        if (startEvalBtn) {
            startEvalBtn.addEventListener('click', startEvaluation);
        }
    }

    // 初始化图表
    function initCharts() {
        const scoreDistEl = document.getElementById('scoreDistChart');
        const dimensionRadarEl = document.getElementById('dimensionRadarChart');

        if (scoreDistEl && typeof echarts !== 'undefined') {
            scoreDistChart = echarts.init(scoreDistEl);
        }
        if (dimensionRadarEl && typeof echarts !== 'undefined') {
            dimensionRadarChart = echarts.init(dimensionRadarEl);
        }
    }

    // 获取选中的数据来源
    function getSelectedTables() {
        const checkboxes = document.querySelectorAll('#evaluation-panel .checkbox-group input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    // 获取日期范围
    function getDateRange() {
        const startDate = document.getElementById('evalStartDate')?.value || '';
        const endDate = document.getElementById('evalEndDate')?.value || '';
        return { startDate, endDate };
    }

    // 开始评估
    async function startEvaluation() {
        const tables = getSelectedTables();
        const { startDate, endDate } = getDateRange();

        if (tables.length === 0) {
            alert('请至少选择一个数据来源');
            return;
        }

        try {
            startEvalBtn.disabled = true;
            startEvalBtn.textContent = '评估中...';
            progressSection.style.display = 'block';

            const response = await fetch(`${API_BASE}/api/analyst/evaluate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
                },
                body: JSON.stringify({
                    tables: tables,
                    start_date: startDate,
                    end_date: endDate
                })
            });

            const data = await response.json();

            if (data.error) {
                alert(`评估启动失败: ${data.error}`);
                startEvalBtn.disabled = false;
                startEvalBtn.textContent = '开始评估';
                progressSection.style.display = 'none';
                return;
            }

            // 开始轮询进度
            pollProgress();

        } catch (error) {
            console.error('启动评估失败:', error);
            alert('启动评估失败，请检查网络连接');
            startEvalBtn.disabled = false;
            startEvalBtn.textContent = '开始评估';
            progressSection.style.display = 'none';
        }
    }

    // 轮询评估进度
    async function pollProgress() {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/analyst/evaluate/status`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
                    }
                });
                const progress = await response.json();

                // 更新进度条
                const percent = progress.progress || 0;
                progressFill.style.width = `${percent}%`;
                progressText.textContent = `${percent}% (${progress.completed}/${progress.total})`;

                // 评估完成
                if (progress.status === 'done') {
                    clearInterval(pollInterval);
                    startEvalBtn.disabled = false;
                    startEvalBtn.textContent = '开始评估';
                    progressSection.style.display = 'none';
                    alert('评估完成！');
                    // 加载评估结果
                    loadEvaluationResults();
                }

                // 评估出错
                if (progress.status === 'error') {
                    clearInterval(pollInterval);
                    startEvalBtn.disabled = false;
                    startEvalBtn.textContent = '开始评估';
                    alert('评估过程中出现错误');
                }

            } catch (error) {
                console.error('获取进度失败:', error);
            }
        }, 1000);
    }

    // 加载评估结果
    async function loadEvaluationResults() {
        try {
            const response = await fetch(`${API_BASE}/api/analyst/results?min_score=0`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
                }
            });
            const data = await response.json();

            if (data.error) {
                console.error('获取评估结果失败:', data.error);
                return;
            }

            // 更新评分分布图表
            updateScoreDistChart(data.score_distribution);

            // 更新维度雷达图
            updateDimensionRadarChart(data.dimension_avg);

            // 更新低分案例表格
            updateLowScoreTable(data.low_score_cases);

        } catch (error) {
            console.error('加载评估结果失败:', error);
        }
    }

    // 更新评分分布图表
    function updateScoreDistChart(scoreDistribution) {
        if (!scoreDistChart) return;

        const scores = [1, 2, 3, 4, 5];
        const counts = scores.map(score => {
            const item = scoreDistribution.find(d => d.score === score);
            return item ? item.count : 0;
        });

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            xAxis: {
                type: 'category',
                data: ['1分', '2分', '3分', '4分', '5分'],
                axisLabel: { color: '#94a3b8' }
            },
            yAxis: {
                type: 'value',
                axisLabel: { color: '#94a3b8' },
                splitLine: { lineStyle: { color: '#334155' } }
            },
            series: [{
                data: counts,
                type: 'bar',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#0ea5e9' },
                        { offset: 1, color: '#0284c7' }
                    ])
                },
                barWidth: '50%'
            }]
        };

        scoreDistChart.setOption(option);
    }

    // 更新维度雷达图
    function updateDimensionRadarChart(dimensionAvg) {
        if (!dimensionRadarChart) return;

        const dimensions = Object.keys(dimensionAvg);
        const values = Object.values(dimensionAvg);

        if (dimensions.length === 0) {
            dimensionRadarChart.setOption({
                title: {
                    text: '暂无数据',
                    left: 'center',
                    top: 'center',
                    textStyle: { color: '#94a3b8' }
                }
            });
            return;
        }

        const option = {
            tooltip: {},
            radar: {
                indicator: dimensions.map(dim => ({
                    name: dim,
                    max: 5
                })),
                axisName: {
                    color: '#94a3b8'
                },
                splitArea: {
                    areaStyle: {
                        color: ['rgba(14, 165, 233, 0.05)', 'rgba(14, 165, 233, 0.1)']
                    }
                },
                axisLine: {
                    lineStyle: { color: '#334155' }
                },
                splitLine: {
                    lineStyle: { color: '#334155' }
                }
            },
            series: [{
                type: 'radar',
                data: [{
                    value: values,
                    name: '平均分',
                    areaStyle: {
                        color: 'rgba(14, 165, 233, 0.3)'
                    },
                    lineStyle: {
                        color: '#0ea5e9'
                    },
                    itemStyle: {
                        color: '#0ea5e9'
                    }
                }]
            }]
        };

        dimensionRadarChart.setOption(option);
    }

    // 更新低分案例表格
    function updateLowScoreTable(lowScoreCases) {
        if (!lowScoreTableBody) return;

        if (!lowScoreCases || lowScoreCases.length === 0) {
            lowScoreTableBody.innerHTML = '<tr><td colspan="6" class="empty-tip">暂无低分案例</td></tr>';
            return;
        }

        const html = lowScoreCases.map(item => `
            <tr>
                <td>${item.id}</td>
                <td>${translateSourceTable(item.source_table)}</td>
                <td><span class="score-badge score-${item.score}">${item.score}分</span></td>
                <td>${item.issues || '-'}</td>
                <td class="content-cell" title="${escapeHtml(item.user_content || '')}">${truncateText(item.user_content, 50)}</td>
                <td class="content-cell" title="${escapeHtml(item.ai_content || '')}">${truncateText(item.ai_content, 50)}</td>
            </tr>
        `).join('');

        lowScoreTableBody.innerHTML = html;
    }

    // 翻译来源表名
    function translateSourceTable(table) {
        const map = {
            'user_chat_logs': '用户对话',
            'admin_chat_logs': '管理员对话',
            'chart_generation_logs': '图表生成',
            'security_warning_logs': '安全警告'
        };
        return map[table] || table;
    }

    // HTML转义
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 截断文本
    function truncateText(text, maxLength) {
        if (!text) return '-';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
