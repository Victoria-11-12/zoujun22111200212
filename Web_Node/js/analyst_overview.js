// 数据概览模块 - 负责加载和展示四个ECharts图表

// 图表实例
let chatTrendChart = null;
let intentDistChart = null;
let chartSuccessChart = null;
let attackDistChart = null;

// 初始化函数 - 由 analyst_main.js 调用
function initOverview() {
    // 初始化图表实例
    initCharts();
    // 加载数据
    loadOverviewData();
}

// 初始化图表实例
function initCharts() {
    // 如果图表已存在，先销毁
    if (chatTrendChart) {
        chatTrendChart.dispose();
    }
    if (intentDistChart) {
        intentDistChart.dispose();
    }
    if (chartSuccessChart) {
        chartSuccessChart.dispose();
    }
    if (attackDistChart) {
        attackDistChart.dispose();
    }
    
    chatTrendChart = echarts.init(document.getElementById('chatTrendChart'));
    intentDistChart = echarts.init(document.getElementById('intentDistChart'));
    chartSuccessChart = echarts.init(document.getElementById('chartSuccessChart'));
    attackDistChart = echarts.init(document.getElementById('attackDistChart'));

    // 监听窗口大小变化，自适应调整图表
    window.addEventListener('resize', function() {
        chatTrendChart && chatTrendChart.resize();
        intentDistChart && intentDistChart.resize();
        chartSuccessChart && chartSuccessChart.resize();
        attackDistChart && attackDistChart.resize();
    });
}

// 从后端加载数据概览
async function loadOverviewData() {
    try {
        const response = await fetch('http://localhost:3000/api/analyst/overview', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('获取数据失败');
        }

        const result = await response.json();

        if (result.code !== 200) {
            throw new Error(result.msg || '获取数据失败');
        }

        const data = result.data;

        // 渲染四个图表
        renderChatTrendChart(data.chat_trend);
        renderIntentDistChart(data.intent_distribution);
        renderChartSuccessChart(data.chart_success_rate);
        renderAttackDistChart(data.attack_distribution);
    } catch (error) {
        console.error('加载数据概览失败:', error);
        // 使用模拟数据展示（开发阶段）
        useMockData();
    }
}

// 对话量趋势 - 折线图
function renderChatTrendChart(data) {
    if (!data || data.length === 0) {
        chatTrendChart.setOption({
            title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999' } }
        });
        return;
    }

    const dates = data.map(item => {
        const date = new Date(item.date);
        return `${date.getMonth() + 1}-${date.getDate()}`;
    });
    const counts = data.map(item => item.count);

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'line' }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: dates,
            axisLine: { lineStyle: { color: '#ccc' } },
            axisLabel: { color: '#666' }
        },
        yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#ccc' } },
            axisLabel: { color: '#666' },
            splitLine: { lineStyle: { color: '#eee' } }
        },
        series: [{
            name: '对话量',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            data: counts,
            itemStyle: { color: '#3498db' },
            lineStyle: { width: 3 },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(52, 152, 219, 0.3)' },
                    { offset: 1, color: 'rgba(52, 152, 219, 0.05)' }
                ])
            }
        }]
    };

    chatTrendChart.setOption(option);
}

// 意图分布 - 饼图
function renderIntentDistChart(data) {
    if (!data || data.length === 0) {
        intentDistChart.setOption({
            title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999' } }
        });
        return;
    }

    const chartData = data.map(item => ({
        name: item.intent,
        value: item.count
    }));

    const intentNameMap = {
        'NEED_SQL': '需要SQL查询',
        'DIRECT_REPLY': '直接回复',
        'WARNING': '警告/攻击',
        'CHART_GENERATION': '图表生成',
        '缺失': '缺失'
    };

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                return params.name + ': ' + params.value + ' (' + params.percent.toFixed(2) + '%)';
            }
        },
        legend: {
            orient: 'vertical',
            right: '5%',
            top: 'center',
            textStyle: { color: '#666' }
        },
        series: [{
            name: '意图分布',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['40%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 10,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: {
                show: false,
                position: 'center'
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: 16,
                    fontWeight: 'bold',
                    formatter: function(params) {
                        return params.name + '\n' + params.percent.toFixed(2) + '%';
                    }
                }
            },
            labelLine: { show: false },
            data: chartData.map(item => ({
                name: intentNameMap[item.name] || item.name,
                value: item.value
            })),
            color: ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
        }]
    };

    intentDistChart.setOption(option);
}

// 绘图成功率 - 环形图
function renderChartSuccessChart(data) {
    if (!data) {
        chartSuccessChart.setOption({
            title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999' } }
        });
        return;
    }

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            right: '10%',
            top: 'center',
            textStyle: { color: '#666' }
        },
        series: [{
            name: '绘图成功率',
            type: 'pie',
            radius: ['50%', '75%'],
            center: ['35%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 8,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: {
                show: true,
                position: 'center',
                formatter: function() {
                    const total = data.success + data.fail;
                    const rate = total > 0 ? Math.round((data.success / total) * 100) : 0;
                    return '成功率\n' + rate + '%';
                },
                fontSize: 18,
                fontWeight: 'bold',
                color: '#2c3e50'
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: 20,
                    fontWeight: 'bold'
                }
            },
            data: [
                { name: '成功', value: data.success || 0, itemStyle: { color: '#2ecc71' } },
                { name: '失败', value: data.fail || 0, itemStyle: { color: '#e74c3c' } }
            ]
        }]
    };

    chartSuccessChart.setOption(option);
}

// 攻击类型分布 - 柱状图
function renderAttackDistChart(data) {
    if (!data || data.length === 0) {
        attackDistChart.setOption({
            title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999' } }
        });
        return;
    }

    const types = data.map(item => item.warning_type);
    const counts = data.map(item => item.count);

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: types,
            axisLine: { lineStyle: { color: '#ccc' } },
            axisLabel: { 
                color: '#666',
                rotate: data.length > 5 ? 30 : 0
            },
            axisTick: { alignWithLabel: true }
        },
        yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#ccc' } },
            axisLabel: { color: '#666' },
            splitLine: { lineStyle: { color: '#eee' } }
        },
        series: [{
            name: '攻击次数',
            type: 'bar',
            barWidth: '60%',
            data: counts,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#e74c3c' },
                    { offset: 1, color: '#c0392b' }
                ]),
                borderRadius: [4, 4, 0, 0]
            }
        }]
    };

    attackDistChart.setOption(option);
}

// 模拟数据（开发阶段使用）
function useMockData() {
    const mockData = {
        chat_trend: [
            { date: '2026-04-01', count: 45 },
            { date: '2026-04-02', count: 52 },
            { date: '2026-04-03', count: 38 },
            { date: '2026-04-04', count: 65 },
            { date: '2026-04-05', count: 48 },
            { date: '2026-04-06', count: 72 },
            { date: '2026-04-07', count: 55 }
        ],
        intent_distribution: [
            { intent: 'NEED_SQL', count: 120 },
            { intent: 'DIRECT_REPLY', count: 80 },
            { intent: 'WARNING', count: 15 },
            { intent: 'CHART_GENERATION', count: 35 }
        ],
        chart_success_rate: {
            success: 85,
            fail: 15
        },
        attack_distribution: [
            { warning_type: 'SQL注入', count: 10 },
            { warning_type: '社会工程', count: 5 },
            { warning_type: '敏感词', count: 8 },
            { warning_type: '异常访问', count: 3 }
        ]
    };

    renderChatTrendChart(mockData.chat_trend);
    renderIntentDistChart(mockData.intent_distribution);
    renderChartSuccessChart(mockData.chart_success_rate);
    renderAttackDistChart(mockData.attack_distribution);
}
