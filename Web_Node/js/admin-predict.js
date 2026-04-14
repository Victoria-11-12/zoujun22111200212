// 票房预测模块

// 获取黑马数据并渲染表格
async function loadDarkHorses() {
    const listContainer = document.getElementById('darkHorseList');
    try {
        const response = await fetch('http://localhost:5000/api/flask/dark_horses');
        const res = await response.json();
        
        if (res.code === 200) {
            let html = '';
            res.data.forEach(movie => {
                const roi = movie.budget > 0 ? (movie.predicted_gross / movie.budget).toFixed(2) : 'N/A';
                html += `
                    <tr>
                        <td>${movie.movie_title}</td>
                        <td>${movie.budget.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
                        <td>${movie.predicted_gross.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
                        <td style="color: #52c41a; font-weight: bold;">${roi}x</td>
                    </tr>
                `;
            });
            listContainer.innerHTML = html;
        }
    } catch (error) {
        listContainer.innerHTML = '<tr><td colspan="4" style="color:red">无法连接到 Flask 预测服务器</td></tr>';
    }
}

// 提交深度预测表单
async function handleDeepPrediction(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const rawData = Object.fromEntries(formData.entries());
    
    const data = {
        budget: parseFloat(rawData.budget) || 0,
        genres: rawData.genres || '',
        New_Director: rawData.New_Director || '',
        New_Actor: rawData.New_Actor || ''
    };
    
    const resultValue = document.querySelector('.result-value');
    resultValue.innerText = '计算中...';

    try {
        const response = await fetch('http://localhost:5000/api/flask/predict_deep', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const res = await response.json();
        
        if (res.code === 200) {
            const formattedPrice = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(res.predicted_gross);
            resultValue.innerText = formattedPrice;
        } else {
            resultValue.innerText = '预测失败';
        }
    } catch (error) {
        resultValue.innerText = '服务器连接失败';
    }
}

async function loadROIComparison() {
    const chartDom = document.getElementById('roiComparisonChart');
    if (!chartDom) return;
    
    const myChart = echarts.init(chartDom);
    
    try {
        const response = await fetch('http://localhost:5000/api/flask/roi_comparison');
        const res = await response.json();
        
        console.log('API返回数据量:', res.data ? res.data.length : 0);
        
        if (res.code === 200 && res.data.length > 0) {
            const filteredData = res.data.filter(item => item.actual_roi <= 6 && item.predicted_roi <= 6);
            const scatterData = filteredData.map(item => [item.actual_roi, item.predicted_roi, item.movie_title]);
            
            console.log('散点数据量:', scatterData.length);
            
            const axisMax = 7;
            
            const option = {
                title: {
                    text: '真实ROI vs 预测ROI 散点图',
                    left: 'center',
                    top: 10,
                    textStyle: {
                        fontSize: 16,
                        fontWeight: 'bold'
                    }
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        return `电影: ${params.data[2]}<br/>` +
                               `真实ROI: ${params.data[0].toFixed(2)}<br/>` +
                               `预测ROI: ${params.data[1].toFixed(2)}`;
                    }
                },
                legend: {
                    data: ['数据点', '完美预测线'],
                    top: 40
                },
                grid: {
                    left: '12%',
                    right: '10%',
                    bottom: '15%',
                    top: '20%',
                    containLabel: true
                },
                toolbox: {
                    show: true,
                    feature: {
                        dataZoom: {},
                        dataView: { readOnly: false },
                        restore: {},
                        saveAsImage: {}
                    }
                },
                xAxis: {
                    name: '真实 ROI',
                    nameLocation: 'middle',
                    nameGap: 30,
                    type: 'value',
                    min: 0,
                    max: axisMax,
                    interval: 1,
                    axisLabel: {
                        formatter: '{value}'
                    }
                },
                yAxis: {
                    name: '预测 ROI',
                    nameLocation: 'middle',
                    nameGap: 40,
                    type: 'value',
                    min: 0,
                    max: axisMax,
                    interval: 1,
                    axisLabel: {
                        formatter: '{value}'
                    }
                },
                series: [
                    {
                        name: '数据点',
                        type: 'scatter',
                        data: scatterData,
                        symbolSize: 6,
                        itemStyle: {
                            color: '#1890ff',
                            opacity: 0.6
                        },
                        emphasis: {
                            itemStyle: {
                                color: '#40a9ff',
                                borderColor: '#1890ff',
                                borderWidth: 2
                            }
                        }
                    },
                    {
                        name: '完美预测线',
                        type: 'line',
                        data: [[0, 0], [axisMax, axisMax]],
                        lineStyle: {
                            color: '#ff4d4f',
                            width: 2,
                            type: 'dashed'
                        },
                        symbol: 'none',
                        silent: true
                    }
                ]
            };
            
            myChart.setOption(option);
        } else {
            chartDom.innerHTML = '<p style="text-align:center; padding:50px; color:#999;">暂无数据</p>';
        }
    } catch (error) {
        console.error('加载ROI对比数据失败:', error);
        chartDom.innerHTML = '<p style="text-align:center; padding:50px; color:#ff4d4f;">数据加载失败</p>';
    }
    
    window.addEventListener('resize', function() {
        myChart.resize();
    });
}
