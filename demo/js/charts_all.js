// 1. 图表映射字典 
const ChartRegistry = {
    "bar_top10": initBar1,
    "bar_director": initBar2,
    "word_cloud": initWordCloud,
    "line_trend": initLineChart,
    "radar_map": initRadarChart,
    "scatter_score": initScatterChart,
    "pie_genre": initPieGenre, 
    "funnel_roi": initFunnelRoi,
    "bubble_social": initBubbleSocial,
    "map_location": initMapLocation,
    "scatter_duration": initScatterDuration,
    "bar_actor": initBarActor, 
    "budget_scatter": initBudgetScatter,
    "pie_rating": initPieRating,
};

/**
 * 核心辅助函数：获取安全的 ECharts 容器
 * @param {string} targetId 容器ID
 */
// 适配函数
function getChartContainer(targetId) {
    const el = document.getElementById(targetId);
    if (!el) return null;
    // 如果是 demo.html 的面板（带 .chart 类），则返回内部的 chart div
    // 如果是 admin.html 的预览盒，则直接返回 el 本身
    return el.querySelector('.chart') || el;
}

// 1
function initBar1(boxId) {
    //获取容器、检查数据、创建实例
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;// 检查容器和数据是否存在
    const myChart = echarts.init(chartDom);

    // 获取前10条票房最高的电影
    const sortedMovies = window.movieData.sort((a, b) => b.gross - a.gross).slice(0, 10);
    const fullTitles = sortedMovies.map(m => m.movie_title.trim()); // 用于tooltip
    const grossData = sortedMovies.map(m => (m.gross / 1000000).toFixed(2)); // 单位 M$

    myChart.setOption({
        tooltip: {//提示框
            trigger: 'axis',//悬停显示
            axisPointer: { type: 'shadow' },//阴影高亮
            formatter: function(params) {
                const index = params[0].dataIndex;
                return `${fullTitles[index]}<br/>票房: ${grossData[index]} M$`;
            }//传参悬停显示
        },
        toolbox: {//工具箱
            show: true,
            feature: {
                saveAsImage: {//保存功能
                    show: true,
                    title: '保存为图片',
                    type: 'png',
                    backgroundColor: 'transparent'//透明背景
                }
            }
        },
        grid: {
            left: '5%',
            right: '10%',
            bottom: '5%',
            top: '10%',
            containLabel: true // 留出空间给轴名称
        },
        xAxis: {
            type: 'category',
            z: 3, // 提高层级，数字越大越靠前，确保箭头盖在柱子上
            type: 'category',
            name: '影片',
            nameLocation: 'end', // 修改为 end，让名称靠近箭头
            nameGap: 10,         // 调整名称与轴线末端的距离
            nameTextStyle: { // 轴名称样式
            color: '#fff', 
            fontSize: 12,
            },
            axisLabel: { show: false },
            axisLine: {
                show: true,
                symbol: ['none', 'arrow'], // 轴线末端显示箭头 [起点, 终点]
                symbolSize: [6, 10],      // 箭头的大小 [宽, 高]
                lineStyle: { color: '#fff' }
            }
        },
        yAxis: {
            type: 'value',
            name: 'M$',
            nameLocation: 'end',
            nameGap: 15, // 增加这个值可以拉开名称与轴顶部的基础距离
            nameTextStyle: {// 轴名称样式
                color: '#fff', 
                fontSize: 12,
                align: 'center',  
            },
            axisLine: {
                show: true,
                symbol: ['none', 'arrow'], // 纵轴末端显示箭头
                symbolSize: [6, 10],
                lineStyle: { color: '#fff' }
            },
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        series: [
            {
                type: 'bar',
                data: grossData,
                showBackground: true,
                backgroundStyle: {
                    color: 'rgba(180, 180, 180, 0.2)',
                    borderRadius: 5//圆角
                },
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#83bff6' },
                        { offset: 0.5, color: '#188df0' },
                        { offset: 1, color: '#188df0' }
                    ]),
                    borderRadius: [5, 5, 0, 0],
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.3)'
                },
                emphasis: {
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#2378f7' },
                            { offset: 0.7, color: '#2378f7' },
                            { offset: 1, color: '#83bff6' }
                        ]),
                        shadowBlur: 15,
                        shadowColor: 'rgba(0, 0, 255, 0.5)'
                    }
                }
            }
        ]
    });

    window.addEventListener("resize", () => myChart.resize());
}

// 2
function initBar2(boxId) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;
    const myChart = echarts.init(chartDom);

    // 计算每位导演的总票房
    const dirMap = {};
    window.movieData.forEach(m => {
        if (m.director_name) {
            dirMap[m.director_name] = (dirMap[m.director_name] || 0) + (parseFloat(m.gross) || 0);
        }
    });
    const data = Object.keys(dirMap).map(k => ({ name: k, value: dirMap[k] })).sort((a, b) => b.value - a.value).slice(0, 10);
    // 提取导演名称和票房值
    const directors = data.map(d => d.name);
    const grossValues = data.map(d => (d.value / 1000000).toFixed(2)); // 转换为 M$

    myChart.setOption({
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: function(params) {
                const index = params[0].dataIndex;
                return `${directors[index]}<br/>票房: ${grossValues[index]} M$`;
            }
        },
        toolbox: {
        show: true,
        feature: {
            saveAsImage: {
                show: true,
                title: '保存为图片',
                type: 'png',
                backgroundColor: 'transparent'
            }
        }
    },
        grid: {
            left: '5%',
            right: '5%',
            bottom: '5%',      // 增加底部空间，确保横轴名称完整显示
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            name: 'M$',
            nameLocation: 'middle',
            nameGap: 20,         
            nameTextStyle: { color: '#fff', fontSize: 12 },
            axisLine: {          
                lineStyle: { color: '#fff' }
            },
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        yAxis: {
            type: 'category',
            data: directors,
            axisLine: {
                lineStyle: { color: '#fff' }
            },
            axisLabel: { color: '#fff', fontSize: 10 },
            axisTick: { show: false },
            splitLine: { show: false }
        },
        series: [{
            type: 'bar',
            data: grossValues,
            showBackground: true,
            backgroundStyle: {
                color: 'rgba(180, 180, 180, 0.2)',
                borderRadius: 5
            },
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#83bff6' },
                    { offset: 1, color: '#2f89cf' }
                ]),
                borderRadius: [0, 5, 5, 0],
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.3)'
            },
            emphasis: {// 鼠标悬停时的g高亮样式
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                        { offset: 0, color: '#2378f7' },
                        { offset: 1, color: '#188df0' }
                    ]),
                    shadowBlur: 15,
                    shadowColor: 'rgba(0, 0, 255, 0.5)'
                }
            }
        }]
    });
    window.addEventListener("resize", () => myChart.resize());
}

// 3
function initWordCloud(boxId) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;
    const myChart = echarts.init(chartDom);

    // 统计关键词出现次数
    const keywords = {};
    window.movieData.forEach(m => {
        if (m.plot_keywords) {
            m.plot_keywords.split('|').forEach(k => {
                keywords[k] = (keywords[k] || 0) + 1;
            });
        }
    });

    // 取词
    const data = Object.keys(keywords)
        .map(k => ({ name: k, value: keywords[k] }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 60);

    myChart.setOption({
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} 次'
        },
            toolbox: {
                        show: true,
                        feature: {
                            saveAsImage: {
                                show: true,
                                title: '保存为图片',
                                type: 'png',
                                backgroundColor: 'transparent'
                            }
                        }
                    },
                            grid: {

            top: '15%',
        },
        series: [{
            type: 'wordCloud',
            shape: 'circle',
            gridSize: 5,                // 减小间距，使词更密集
            sizeRange: [10, 48],         // 扩大字体范围，让词的大小变化更明显
            drawOutOfBound: true,      // 允许词超出边界，避免被裁剪
            textStyle: {                //随机分配颜色
                fontFamily: 'sans-serif',
                fontWeight: 'bold',
                color: () => `rgb(${[Math.round(Math.random()*160), Math.round(Math.random()*160), Math.round(Math.random()*160)].join(',')})`
            },
            data: data
        }]
    });

    window.addEventListener('resize', () => myChart.resize());
}

// 4
function initLineChart(boxId, input) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;
    const myChart = echarts.init(chartDom);
    
    //获取输入，如果是年份，就根据年份过滤，否则根据电影名过滤
    const filterByInput = (item, val) => {
        if (!val || val.trim() === '') return true;
        const trimmed = val.trim();
        if (/^\d{4}$/.test(trimmed)) {
            return String(item.title_year) === trimmed;
        } else {
            return item.movie_title && item.movie_title.toLowerCase().includes(trimmed.toLowerCase());
        }
    };

    let filtered = window.movieData.filter(item => item.gross && filterByInput(item, input));
// 如果没有匹配数据，显示提示
    if (filtered.length === 0) {
        myChart.setOption({
            title: { text: '无匹配数据', left: 'center', top: 'center', textStyle: { color: '#ff4d4f', fontSize: 14, fontWeight: 'bold' } },
            series: []
        }, true);
        return;
    }

    filtered.sort((a, b) => b.gross - a.gross);

    // 生成详细信息作为副标题
    let subTitle = '';
    if (!input || input.trim() === '') {
        subTitle = `全部电影票房分布 (共 ${filtered.length} 部)`;
    } else if (/^\d{4}$/.test(input.trim())) {
        subTitle = `${input.trim()}年票房分布 (Top ${filtered.length} 部)`;
    } else {
        subTitle = `包含“${input.trim()}”的电影票房分布 (${filtered.length} 部)`;
    }

    const grossData = filtered.map(m => (m.gross / 1e6).toFixed(2));

    myChart.setOption({
        title: {
            subtext: subTitle,          // 仅设置副标题
            left: 'center',
            top: 5,
            subtextStyle: {
                color: '#fff',
                fontSize: 12,
                fontWeight: 'bold',
                textShadow: '0 0 10px rgba(76,155,253,0.8)'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: function(params) {
                const index = params[0].dataIndex;
                const m = filtered[index];
                return `${m.movie_title}<br/>年份: ${m.title_year || '未知'}<br/>导演: ${m.director_name || '未知'}<br/>票房: ${(m.gross / 1e6).toFixed(2)} M$`;
            },
            backgroundColor: 'rgba(0,0,0,0.7)',
            borderColor: '#4c9bfd',
            borderWidth: 1,
            textStyle: { color: '#fff' }
        },
        toolbox: {
            show: true,
            feature: {
                saveAsImage: {
                    show: true,
                    title: '保存为图片',
                    type: 'png',
                    backgroundColor: 'transparent'
                }
            }
        },
        grid: {
            left: '10%',
            right: '8%',
            top: '15%', 
            bottom: '15%',          // 增加顶部空间，为副标题留出位置，避免与坐标轴重叠
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: filtered.map((_, idx) => idx),
            name: '影片排序 (按票房降序)',
            nameLocation: 'middle',
            nameGap: 15,
            nameTextStyle: { color: '#aaa', fontSize: 10 },
            axisLine: { lineStyle: { color: '#4c9bfd', width: 2 } },
            axisTick: { show: false },
            axisLabel: { show: false }
        },
        yAxis: {
            type: 'value',
            name: '票房 (M$)',
            nameLocation: 'end',
            nameGap: 15,
            nameTextStyle: { color: '#fff', fontSize: 11 },
            axisLine: { lineStyle: { color: '#4c9bfd', width: 2 } },
            axisLabel: { color: '#fff', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)', type: 'dashed' } }
        },
        series: [
            {
                name: '票房',
                type: 'line',
                data: grossData,
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                showSymbol: true,
                lineStyle: {
                    color: '#4c9bfd',
                    width: 3,
                    shadowBlur: 15,
                    shadowColor: 'rgba(76, 155, 253, 0.6)',
                    shadowOffsetY: 5
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(76, 155, 253, 0.8)' },
                        { offset: 1, color: 'rgba(76, 155, 253, 0.1)' }
                    ])
                },
                itemStyle: {
                    color: '#ffeb3b',
                    borderColor: '#4c9bfd',
                    borderWidth: 1,
                    shadowBlur: 10,
                    shadowColor: '#ffeb3b'
                },
                emphasis: {
                    focus: 'series',
                    lineStyle: { width: 4 },
                    itemStyle: { borderWidth: 2, shadowBlur: 15 }
                }
            }
        ],
        //动画平滑
        animation: true,
        animationDuration: 1000,
        animationEasing: 'cubicOut'
    }, true);

    window.addEventListener('resize', () => myChart.resize());
}

//5
function initRadarChart(boxId, m1Name, m2Name) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;
    const myChart = echarts.init(chartDom);

    // 辅助函数：查找电影，若未找到则随机选一部
    const findMovie = (name) => {
        if (name && name.trim()) {
            const found = window.movieData.find(m => m.movie_title && m.movie_title.trim() === name.trim());
            if (found) return found;
        }
        return null; // 没找到就返回 null，不自动随机
    };

    // 验证电影数据是否完整有效
    const isValidMovie = (m) => {
        if (!m) return false;
        if (!m.imdb_score || m.imdb_score === 0) return false;
        if (!m.gross || m.gross === 0) return false;
        if (!m.num_critic_for_reviews || m.num_critic_for_reviews === 0) return false;
        if (!m.cast_total_facebook_likes || m.cast_total_facebook_likes === 0) return false;
        if (!m.duration || m.duration === 0) return false;
        return true;
    };

    // 随机选择一部数据完整的电影
    const findValidRandomMovie = () => {
        const validMovies = window.movieData.filter(m => isValidMovie(m));
        if (validMovies.length === 0) return null;
        return validMovies[Math.floor(Math.random() * validMovies.length)];
    };

    const mov1Input = findMovie(m1Name);
    const mov2Input = findMovie(m2Name);

    // 检查用户输入的电影是否数据完整
    if (m1Name && m1Name.trim() && !isValidMovie(mov1Input)) {
        myChart.setOption({
            title: { text: '电影数据不完整，无法比较', left: 'center', top: 'center', textStyle: { color: '#ff4d4f' } },
            series: []
        });
        return;
    }
    if (m2Name && m2Name.trim() && !isValidMovie(mov2Input)) {
        myChart.setOption({
            title: { text: '电影数据不完整，无法比较', left: 'center', top: 'center', textStyle: { color: '#ff4d4f' } },
            series: []
        });
        return;
    }

    // 如果用户未指定电影或指定了但数据完整，则使用该电影或随机选择数据完整的电影
    const mov1 = mov1Input && isValidMovie(mov1Input) ? mov1Input : findValidRandomMovie();
    const mov2 = mov2Input && isValidMovie(mov2Input) ? mov2Input : findValidRandomMovie();

    // 如果随机选择也找不到有效数据
    if (!mov1 || !mov2) {
        myChart.setOption({
            title: { text: '电影数据不完整，无法比较', left: 'center', top: 'center', textStyle: { color: '#ff4d4f' } },
            series: []
        });
        return;
    }

    const dimensions = [
        { name: '评分', key: 'imdb_score', max: 100 },
        { name: '票房', key: 'gross', max: 100 },
        { name: '评论数', key: 'num_critic_for_reviews', max: 100 },
        { name: '演员人气', key: 'cast_total_facebook_likes', max: 100 },
        { name: '时长', key: 'duration', max: 100 }
    ];

    const extractScore = (m) => {
        const scores = [];
        dimensions.forEach(dim => {
            let value = 0;
            const val = m[dim.key];
            if (val !== null && val !== undefined && val !== '') {
                if (dim.key === 'imdb_score') {
                    value = val * 10;
                } else if (dim.key === 'gross') {
                    value = Math.min(100, (parseFloat(val) || 0) / 1000000);
                } else if (dim.key === 'num_critic_for_reviews') {
                    value = Math.min(100, (val || 0) / 5);
                } else if (dim.key === 'cast_total_facebook_likes') {
                    value = Math.min(100, (val || 0) / 100);
                } else if (dim.key === 'duration') {
                    value = Math.min(100, (val || 0) / 2);
                }
            }
            scores.push(value);
        });
        return scores;
    };

    const data1 = extractScore(mov1);
    const data2 = extractScore(mov2);

    const indicator = dimensions.map(dim => ({ name: dim.name, max: dim.max }));

    myChart.setOption({
        color: ['#67F9D8', '#FFE434', '#56A3F1', '#FF917C'],
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
        const m = params.name === mov1.movie_title ? mov1 : mov2;
        const gross = (parseFloat(m.gross) || 0) / 1000000;
        return `${m.movie_title}<br/>
                【评分】 ${m.imdb_score * 10}<br/>
                【票房】 ${gross.toFixed(2)} M$<br/>
                【评论数】 ${((m.num_critic_for_reviews) || 0)}<br/>
                【演员人气】 ${(m.cast_total_facebook_likes || 0)}<br/>
                【时长】 ${m.duration || 0} min`;
    }
            
        },
            toolbox: {
        show: true,
        feature: {
            saveAsImage: {
                show: true,
                title: '保存为图片',
                type: 'png',
                backgroundColor: 'transparent'
            }
        }
    },
        legend: {
            data: [mov1.movie_title, mov2.movie_title],
            textStyle: { color: '#fff' },
            bottom: 10
        },
        radar: {
            indicator: indicator,
            center: ['50%', '45%'],
            radius: '60%',
            startAngle: 90,
            splitNumber: 4,
            shape: 'circle',
            axisName: {
                formatter: '【{value}】',
                color: '#428BD4',
                backgroundColor: 'rgba(0,0,0,0.3)',
                borderRadius: 3,
                padding: [2, 4]
            },
            splitArea: {
                areaStyle: {
                    color: ['#77EADF', '#26C3BE', '#64AFE9', '#428BD4'],
                    shadowColor: 'rgba(0, 0, 0, 0.3)',
                    shadowBlur: 10
                }
            },
            axisLine: {
                lineStyle: { color: 'rgba(211, 253, 250, 0.8)' }
            },
            splitLine: {
                lineStyle: { color: 'rgba(211, 253, 250, 0.8)' }
            }
        },
        series: [
            {
                type: 'radar',
                emphasis: {
                    lineStyle: { width: 4 }
                },
                data: [
                    {
                        value: data1,
                        name: mov1.movie_title,
                        areaStyle: { color: 'rgba(103, 249, 216, 0.4)' },
                        lineStyle: { color: '#67F9D8', width: 2 },
                        itemStyle: { color: '#67F9D8' },
                        symbol: 'circle',
                        symbolSize: 8,
                        label: {
                            show: false,
                            formatter: (params) => params.value,
                            color: '#fff',
                            fontSize: 9,
                            backgroundColor: 'rgba(0,0,0,0.5)',
                            borderRadius: 3,
                            padding: [2, 4]
                        }
                    },
                    {
                        value: data2,
                        name: mov2.movie_title,
                        areaStyle: {
                            color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                                { offset: 0, color: 'rgba(255, 228, 52, 0.2)' },
                                { offset: 1, color: 'rgba(255, 228, 52, 0.8)' }
                            ])
                        },
                        lineStyle: { color: '#FFE434', width: 2, type: 'dashed' },
                        itemStyle: { color: '#FFE434' },
                        symbol: 'rect',
                        symbolSize: 8,
                        label: {
                            show: false,
                            formatter: (params) => params.value,
                            color: '#fff',
                            fontSize: 9,
                            backgroundColor: 'rgba(0,0,0,0.5)',
                            borderRadius: 3,
                            padding: [2, 4]
                        }
                    }
                ]
            }
        ]
    });

    window.addEventListener('resize', () => myChart.resize());
}

//6
function initScatterChart(boxId, input) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;
    let myChart = echarts.getInstanceByDom(chartDom);
    if (!myChart) myChart = echarts.init(chartDom);

    const filterByInput = (item, val) => {
        if (!val || val.trim() === '') return true;
        const trimmed = val.trim();
        if (/^\d{4}$/.test(trimmed)) {
            return String(item.title_year) === trimmed;
        } else {
            return item.movie_title && item.movie_title.toLowerCase().includes(trimmed.toLowerCase());
        }
    };

    const filtered = window.movieData.filter(item =>
        item.gross && item.imdb_score && filterByInput(item, input)
    );

    if (filtered.length === 0) {
        myChart.setOption({
            title: { text: '无匹配数据', left: 'center', top: 'center', textStyle: { color: '#ff4d4f' } },
            series: []
        }, true);
        return;
    }

    // 生成详细信息作为副标题
    let subTitle = '';
    if (!input || input.trim() === '') {
        subTitle = `全部电影评分-票房分布 (共 ${filtered.length} 部)`;
    } else if (/^\d{4}$/.test(input.trim())) {
        subTitle = `${input.trim()}年评分-票房分布 (${filtered.length} 部)`;
    } else {
        subTitle = `包含“${input.trim()}”的电影评分-票房分布 (${filtered.length} 部)`;
    }

    myChart.setOption({
        title: {
            subtext: subTitle,          // 仅设置副标题
            left: 'center',
            top: 5,
            subtextStyle: {
                color: '#fff',
                fontSize: 12,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            formatter: (p) => `${p.data[2]}<br/>评分: ${p.data[0]}<br/>票房: ${p.data[1]}M`
        },
        toolbox: {
            show: true,
            feature: {
                saveAsImage: {
                    show: true,
                    title: '保存为图片',
                    type: 'png',
                    backgroundColor: 'transparent'
                }
            }
        },
        grid: {
            left: '5%',
            right: '12%',
            bottom: '8%',
            top: '22%',          // 增加顶部空间，为副标题留出位置，避免与坐标轴重叠
            containLabel: true
        },
        xAxis: {
            name: '评分',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { show: false }
        },
        yAxis: {
            name: '票房(M)',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        series: [{
            type: 'scatter',
            symbolSize: 10,
            data: filtered.map(m => [m.imdb_score, (m.gross / 1e6).toFixed(2), m.movie_title.trim()]),
            itemStyle: { color: '#ffeb3b' }
        }]
    }, true);

    window.addEventListener('resize', () => myChart.resize());
}

// 7
function initPieGenre(boxId) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData.length) return;
    if (echarts.getInstanceByDom(chartDom)) echarts.getInstanceByDom(chartDom).dispose();
    const myChart = echarts.init(chartDom);

    // 统计各类型出现次数
    const genreMap = {};
    window.movieData.forEach(m => {
        if (m.genres) {
            m.genres.split('|').forEach(g => {
                genreMap[g] = (genreMap[g] || 0) + 1;
            });
        }
    });

    // 按数量排序，取前10个主要类型，其余合并为“其他”
    const sortedGenres = Object.keys(genreMap)
        .map(name => ({ name, value: genreMap[name] }))
        .sort((a, b) => b.value - a.value);
    
    const topN = 10;
    let chartData = sortedGenres.slice(0, topN);
    const otherCount = sortedGenres.slice(topN).reduce((acc, cur) => acc + cur.value, 0);
    if (otherCount > 0) {
        chartData.push({ name: '其他', value: otherCount });
    }

    // 图例数据（所有类型名称）
    const legendData = chartData.map(item => item.name);

    myChart.setOption({

        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b} : {c} 部 ({d}%)'
        },
            toolbox: {
        show: true,
        feature: {
            saveAsImage: {
                show: true,
                title: '保存为图片',
                type: 'png',
                backgroundColor: 'transparent'
            }
        }
    },
        legend: {
            type: 'scroll',
            orient: 'vertical',//垂直方向
            right: 15,
            top: 50,
            bottom: 15,
            data: legendData,
            textStyle: { color: '#fff' },
            pageIconColor: '#4c9bfd',
            pageTextStyle: { color: '#fff' }
        },
        series: [
            {
                name: '电影类型',
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['40%', '50%'],
                avoidLabelOverlap: true,//避免标签重叠
                itemStyle: {
                    borderRadius: 8,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false, // 默认不显示标签，鼠标悬停时通过emphasis显示
                    position: 'outside'
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,//阴影模糊半径
                        shadowOffsetX: 0,//阴影偏移量
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    },
                    label: {
                        show: true,
                        color: '#fff',
                        fontWeight: 'bold'
                    }
                },
                data: chartData
            }
        ]
    });

    window.addEventListener('resize', () => myChart.resize());
}

//8
function initFunnelRoi(boxId) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData.length) return;
    const myChart = echarts.init(chartDom);

    // 1. 计算 ROI 并过滤有效数据 (原有逻辑)
    const roiList = window.movieData
        .filter(m => m.budget > 0 && m.gross > 0)
        .map(m => m.gross / m.budget);

    // 获取总数，用于计算百分比
    const totalCount = roiList.length;

    // 2. 定义 ROI 区间
    const intervals = [
        { name: 'ROI < 1', min: 0, max: 1 },
        { name: '1 ≤ ROI < 2', min: 1, max: 2 },
        { name: '2 ≤ ROI < 3', min: 2, max: 3 },
        { name: '3 ≤ ROI < 5', min: 3, max: 5 },
        { name: 'ROI ≥ 5', min: 5, max: Infinity }
    ];

    // 3. 统计每个区间的电影数量
    const counts = intervals.map(interval => 
        roiList.filter(roi => roi >= interval.min && roi < interval.max).length
    );

    const chartData = intervals.map((interval, idx) => ({
        name: interval.name,
        value: counts[idx]
    })).filter(item => item.value > 0);

    myChart.setOption({
        tooltip: {
            trigger: 'item',
            formatter: function(params) {//百分比
                const count = params.value;
                const percent = totalCount > 0 ? ((count / totalCount) * 100).toFixed(2) : 0;
                return `<b>${params.name}</b><br/>
                        电影数量 : ${count} 部<br/>
                        占整体比例 : ${percent}%`;
            }
        },
        toolbox: {
            show: true,
            feature: {
                saveAsImage: {
                    show: true,
                    title: '保存为图片',
                    type: 'png',
                    backgroundColor: 'transparent'//透明背景
                }
            }
        },
        series: [{
            name: 'ROI 分布',
            type: 'funnel',
            left: '10%',
            right: '10%',
            top: '5%',       // 保持较长的布局
            bottom: '5%',
            width: '80%',
            minSize: '0%',
            maxSize: '100%',
            label: { //`     标签样式
                show: true, 
                position: 'inside', 
                color: '#fff',
                fontSize: 12 
            },
            itemStyle: { //`     项样式
                borderColor: '#fff', 
                borderWidth: 1,
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.3)'
            },
            data: chartData.sort((a, b) => a.value - b.value) 
        }]
    });

    window.addEventListener('resize', () => myChart.resize());
}
//9
function initBubbleSocial(boxId, input) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;

    let myChart = echarts.getInstanceByDom(chartDom);
    if (!myChart) myChart = echarts.init(chartDom);

    const filterByInput = (item, val) => {
        if (!val || val.trim() === '') return true;
        const trimmed = val.trim();
        if (/^\d{4}$/.test(trimmed)) {
            return String(item.title_year) === trimmed;
        } else {
            return item.movie_title && item.movie_title.toLowerCase().includes(trimmed.toLowerCase());
        }
    };

    const filtered = window.movieData.filter(item =>
        item.director_facebook_likes &&
        item.director_facebook_likes > 0 &&
        item.actor_1_facebook_likes &&
        item.actor_1_facebook_likes > 0 &&
        item.gross &&
        item.gross > 0 &&
        filterByInput(item, input)
    );

    if (filtered.length === 0) {
        myChart.setOption({
            title: { text: '无匹配数据', left: 'center', top: 'center', textStyle: { color: '#ff4d4f' } },
            series: []
        }, true);
        return;
    }

    const sliced = filtered.slice(0, 50);
    const chartData = sliced.map(m => [
        m.director_facebook_likes,
        m.actor_1_facebook_likes,
        (m.gross / 1e6).toFixed(2),
        m.movie_title.trim()
    ]);

    // 生成详细信息作为副标题
    let subTitle = '';
    if (!input || input.trim() === '') {
        subTitle = `全部电影社交热度气泡图 (共 ${filtered.length} 部，显示前50)`;
    } else if (/^\d{4}$/.test(input.trim())) {
        subTitle = `${input.trim()}年社交热度气泡图 (${filtered.length} 部，显示前50)`;
    } else {
        subTitle = `包含“${input.trim()}”的电影社交热度气泡图 (${filtered.length} 部，显示前50)`;
    }

    myChart.setOption({
        title: {
            subtext: subTitle,
            left: 'center',
            top: 5,
            subtextStyle: { color: '#fff', fontSize: 12, fontWeight: 'bold' }
        },
        tooltip: {
            formatter: (p) => `${p.data[3]}<br/>票房: ${p.data[2]}M`
        },
        toolbox: {
            show: true,
            feature: {
                saveAsImage: {
                    show: true,
                    title: '保存为图片',
                    type: 'png',
                    backgroundColor: 'transparent'
                }
            }
        },
        grid: {
            left: '5%',
            right: '12%',
            bottom: '8%',
            top: '22%',
            containLabel: true
        },
        xAxis: {
            name: '导演社交热度',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { show: false },
            nameLocation: 'middle',
            nameGap:25
        },
        yAxis: {
            name: '主演社交热度',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        series: [{
            type: 'scatter',
            symbolSize: (data) => Math.sqrt(data[2]) * 2,
            data: chartData,
            itemStyle: { color: 'rgba(255, 246, 0, 0.6)' }
        }]
    }, true);

    window.addEventListener('resize', () => myChart.resize());
}

//10
function initMapLocation(boxId) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData.length) return;
    
    // 确保地图已加载
    if (!echarts.getMap('world')) {
        console.error("地图数据尚未加载，请检查是否引入了 world.js");
        return;
    }

    const myChart = echarts.init(chartDom);
    const countryMap = {};
    
    window.movieData.forEach(m => {
        if (m.country) {
            let name = m.country.trim();
            // 常见名称纠偏，适配 world.js 的标准
            if (name === 'USA') name = 'United States';
            if (name === 'UK') name = 'United Kingdom';
            countryMap[name] = (countryMap[name] || 0) + 1;
        }
    });

    const chartData = Object.keys(countryMap).map(name => ({
        name: name,
        value: countryMap[name]
    }));

    myChart.setOption({
        visualMap: {
            min: 0,
            max: 50, // 根据你的数据量调整
            inRange: { color: ['#e0ffff', '#006edd'] },
            textStyle: { color: '#fff' }
        },
            toolbox: {
        show: true,
        feature: {
            saveAsImage: {
                show: true,
                title: '保存为图片',
                type: 'png',
                backgroundColor: 'transparent'
            }
        }
    },
        series: [{
            type: 'map',
            map: 'world', // 这里必须对应 world.js 注册的名字
            data: chartData,
            // 针对地图名字不匹配的自动补全
            nameMap: {
                'United States of America': 'United States',
                'China': 'China'
            }
        }]
    });
}

//11
function initScatterDuration(boxId, input) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;

    let myChart = echarts.getInstanceByDom(chartDom);
    if (!myChart) myChart = echarts.init(chartDom);

    const filterByInput = (item, val) => {
        if (!val || val.trim() === '') return true;
        const trimmed = val.trim();
        if (/^\d{4}$/.test(trimmed)) {
            return String(item.title_year) === trimmed;
        } else {
            return item.movie_title && item.movie_title.toLowerCase().includes(trimmed.toLowerCase());
        }
    };

    const filtered = window.movieData.filter(item =>
        item.duration && item.gross && filterByInput(item, input)
    );

    if (filtered.length === 0) {
        myChart.setOption({
            title: { text: '无匹配数据', left: 'center', top: 'center', textStyle: { color: '#ff4d4f' } },
            series: []
        }, true);
        return;
    }

    //数据转换
    const chartData = filtered.map(m => [
        m.duration,
        (m.gross / 1e6).toFixed(2),
        m.movie_title.trim()
    ]);

    // 生成详细信息作为副标题
    let subTitle = '';
    if (!input || input.trim() === '') {
        subTitle = `全部电影时长-票房分布 (共 ${filtered.length} 部)`;
    } else if (/^\d{4}$/.test(input.trim())) {
        subTitle = `${input.trim()}年时长-票房分布 (${filtered.length} 部)`;
    } else {
        subTitle = `包含“${input.trim()}”的电影时长-票房分布 (${filtered.length} 部)`;
    }

    myChart.setOption({
        title: {
            subtext: subTitle,
            left: 'center',
            top: 5,
            subtextStyle: { color: '#fff', fontSize: 12, fontWeight: 'bold' }
        },
        tooltip: {
            formatter: (p) => `${p.data[2]}<br/>时长: ${p.data[0]}min<br/>票房: ${p.data[1]}M`
        },
        toolbox: {
            show: true,
            feature: {
                saveAsImage: {
                    show: true,
                    title: '保存为图片',
                    type: 'png',
                    backgroundColor: 'transparent'
                }
            }
        },
        grid: {
            left: '5%',
            right: '12%',
            bottom: '8%',
            top: '22%',
            containLabel: true
        },
        xAxis: {
            name: '时长(min)',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { show: false },
            nameLocation: 'middle',
            nameGap:25
        },
        yAxis: {
            name: '票房(M)',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        series: [{
            symbolSize: 8,
            data: chartData,
            type: 'scatter',
            itemStyle: { color: '#00f6ff' }
        }]
    }, true);

    window.addEventListener('resize', () => myChart.resize());
}

//12

function initBarActor(boxId) {
    const chartDom = getChartContainer(boxId);
    
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;
    const myChart = echarts.init(chartDom);

    // --- 逻辑部分保持不变 ---
    const actorGross = {};
    window.movieData.forEach(m => {
        const gross = parseFloat(m.gross) || 0;
        if (m.actor_1_name) actorGross[m.actor_1_name] = (actorGross[m.actor_1_name] || 0) + gross;
        if (m.actor_2_name) actorGross[m.actor_2_name] = (actorGross[m.actor_2_name] || 0) + gross;
        if (m.actor_3_name) actorGross[m.actor_3_name] = (actorGross[m.actor_3_name] || 0) + gross;
    });

    const rawData = Object.keys(actorGross)
        .map(name => ({ name, value: actorGross[name] }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10);

    const processedData = rawData.map((d, index) => {
        const val = parseFloat((d.value / 1000000).toFixed(2));
        return {
            name: d.name,
            value: index % 2 === 1 ? -val : val, 
            realVal: val 
        };
    });

    myChart.setOption({
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            confine: true, // 确保提示框不超出容器
            formatter: function(params) {
                const item = params[0].data;
                return `${item.name}<br/>总票房: ${item.realVal} M$`;
            }
        },
        toolbox: {
            show: true,
            feature: {
                saveAsImage: { show: true, title: '保存图片', backgroundColor: 'transparent' }
            }
        },
        grid: {
            left: '3%',
            right: '3%',
            bottom: '10%',
            top: '10%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            axisLine: { lineStyle: { color: '#fff' } }
        },
        yAxis: {
            type: 'category',
            data: processedData.map(d => d.name),
            axisTick: { show: false },
            axisLine: { lineStyle: { color: '#fff' } },
            axisLabel: { show: false } 
        },
        series: [{
            type: 'bar',
            data: processedData,
            showBackground: true,
            backgroundStyle: {
                color: 'rgba(180, 180, 180, 0.1)',
                borderRadius: 5
            },
            itemStyle: {
                color: function(params) {
                    let colorStop0 = '#83bff6';
                    let colorStop1 = '#2f89cf';
                    // 根据正负决定渐变方向，让颜色从中间轴向外延申
                    return new echarts.graphic.LinearGradient(
                        params.data.value >= 0 ? 0 : 1, 0, 
                        params.data.value >= 0 ? 1 : 0, 0, 
                        [
                            { offset: 0, color: colorStop0 },
                            { offset: 1, color: colorStop1 }
                        ]
                    );
                },
                borderRadius: 5,
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.3)'
            },
            label: {
                show: true,
                position: 'inside', 
                formatter: '{b}',
                color: '#fff', // 正常状态文字为白色
                fontSize: 12
            },
            emphasis: {
                // 重点：当柱子变亮时，把文字颜色改为深色，避免看不见
                label: {
                    show: true,
                    color: '#2f89cf', // 悬停时文字改为深蓝色（或 #333）
                    fontWeight: 'bold'
                },
                itemStyle: {
                    // 确保高亮时的渐变色足够显眼
                    color: function(params) {
                        return new echarts.graphic.LinearGradient(
                            params.data.value >= 0 ? 0 : 1, 0, 
                            params.data.value >= 0 ? 1 : 0, 0, 
                            [
                                { offset: 0, color: '#2378f7' },
                                { offset: 1, color: '#188df0' }
                            ]
                        );
                    },
                    shadowBlur: 15,
                    shadowColor: 'rgba(0, 0, 255, 0.5)'
                }
            }
        }]
    });

    window.addEventListener("resize", () => myChart.resize());
}//13
function initBudgetScatter(boxId, input) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData || window.movieData.length === 0) return;

    if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
        setTimeout(() => initBudgetScatter(boxId, input), 100);
        return;
    }

    let myChart = echarts.getInstanceByDom(chartDom);
    if (!myChart) myChart = echarts.init(chartDom);

    const filterByInput = (item, val) => {
        if (!val || val.trim() === '') return true;
        const trimmed = val.trim();
        if (/^\d{4}$/.test(trimmed)) {
            return String(item.title_year) === trimmed;
        } else {
            return item.movie_title && item.movie_title.toLowerCase().includes(trimmed.toLowerCase());
        }
    };

    const filtered = window.movieData.filter(item =>
        item.budget > 0 &&
        item.gross > 0 &&
        item.movie_title &&
        filterByInput(item, input)
    );

    if (filtered.length === 0) {
        myChart.setOption({
            title: { text: '无匹配数据', left: 'center', top: 'center', textStyle: { color: '#ff4d4f' } },
            series: []
        }, true);
        return;
    }

    const data = filtered.map(m => [
        (m.budget / 1e6).toFixed(2),
        (m.gross / 1e6).toFixed(2),
        m.movie_title.trim(),
        m.content_rating || 'Unknown'
    ]);

    // 生成详细信息作为副标题
    let subTitle = '';
    if (!input || input.trim() === '') {
        subTitle = `全部电影预算-票房分布 (共 ${filtered.length} 部)`;
    } else if (/^\d{4}$/.test(input.trim())) {
        subTitle = `${input.trim()}年预算-票房分布 (${filtered.length} 部)`;
    } else {
        subTitle = `包含“${input.trim()}”的电影预算-票房分布 (${filtered.length} 部)`;
    }

    const ratingColorMap = {
        'PG-13': '#5470c6', 'R': '#fac858', 'PG': '#ee6666',
        'G': '#73c0de', 'NC-17': '#3ba272', 'Unknown': '#aaa'
    };

    myChart.setOption({
        title: {
            subtext: subTitle,
            left: 'center',
            top: 5,
            subtextStyle: { color: '#fff', fontSize: 12, fontWeight: 'bold' }
        },
        tooltip: {
            trigger: 'item',
            formatter: params => {
                const d = params.data;
                return `${d[2]}<br/>预算: $${d[0]}M<br/>票房: $${d[1]}M<br/>分级: ${d[3]}`;
            }
        },
        toolbox: {
            show: true,
            feature: {
                saveAsImage: {
                    show: true,
                    title: '保存为图片',
                    type: 'png',
                    backgroundColor: 'transparent'
                }
            }
        },
        grid: {
            left: '5%',
            right: '12%',
            bottom: '8%',
            top: '10%',
            containLabel: true
        },
        xAxis: {
            name: '预算',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { show: false }
        },
        yAxis: {
            name: '票房 (M$)',
            nameTextStyle: { color: '#fff' },
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        series: [{
            type: 'scatter',
            data: data,
            symbolSize: 10,
            itemStyle: {
                color: params => ratingColorMap[params.data[3]] || '#ccc'
            },
            emphasis: {
                focus: 'series',
                itemStyle: { borderColor: '#fff', borderWidth: 2 }
            }
        }]
    }, true);

    window.addEventListener('resize', () => myChart.resize());
}
//14
function initPieRating(boxId) {
    const chartDom = getChartContainer(boxId);
    if (!chartDom || !window.movieData.length) return;
    const myChart = echarts.init(chartDom);

    const rateMap = {};
    window.movieData.forEach(m => {
        if (m.content_rating) {
            rateMap[m.content_rating] = (rateMap[m.content_rating] || 0) + 1;
        }
    });

    const chartData = Object.keys(rateMap).map(name => ({ name, value: rateMap[name] }));

    myChart.setOption({
        tooltip: { trigger: 'item' },
            toolbox: {
        show: true,
        feature: {
            saveAsImage: {
                show: true,
                title: '保存为图片',
                type: 'png',
                backgroundColor: 'transparent'
            }
        }
    },
       legend: {
    bottom: '-2%',
    itemWidth: 20,
    itemHeight: 14,
    textStyle: {
        color: '#fff',
        fontSize: 10
    }
},

        series: [{
            name: '内容分级',
            type: 'pie',
                radius: '60%',               // 增大半径
    center: ['50%', '45%'], 
            data: chartData,
            emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
            label: { color: '#fff' }
        }]
    });
}

