// 1. 定义全局变量
let movieData = []; 

// 2. 页面加载完成后，获取数据并渲染

// 页面加载主逻辑，监听器确保 DOM 完全加载
document.addEventListener('DOMContentLoaded', function() {
    console.log("大屏：开始同步基础数据...");

    // 1. 首先获取电影基础数据
    fetch('http://localhost:3000/api/movies')
        .then(res => res.json())
        .then(data => {
            window.movieData = data; // 统一使用 window. 对象
            console.log("大屏：基础数据加载成功，条数:", data.length);

            // 更新中间面板数字
            updatePanelNumbers(data);

            // 2. 基础数据有了，再去请求 6 个位置的配置并渲染
            return loadAndRenderCharts(); 
        })
        .catch(err => {
            console.error("大屏：数据初始化失败:", err);
            document.body.innerHTML += '<div style="color:red;position:fixed;top:0;">数据加载失败，请检查后端服务</div>';
        });
});

// 提取出的数字更新逻辑
function updatePanelNumbers(data) {
    const count = data.length;
    const validGross = data.map(item => parseFloat(item.gross) || 0);
    const maxBox = (Math.max(...validGross) / 1000000).toFixed(2);
    const liElements = document.querySelectorAll('.no-hd ul li');
    if (liElements.length >= 2) {
        liElements[0].innerText = count;
        liElements[1].innerText = maxBox + "M";
    }
}

// 图表渲染函数
function loadAndRenderCharts() {
    console.log("大屏：开始请求位置布局配置...");
    
    // 添加时间戳防止缓存
    fetch('http://localhost:3000/api/charts/config?t=' + Date.now())
        .then(res => res.json())
        .then(res => {
            if (res.code === 200) {
                const configs = res.data;
                console.log("配置获取成功:", configs);

                Object.keys(configs).forEach(posId => {
                    const item = configs[posId];
                    
                    // 注意：大屏接口返回的字段通常是 chart_title 和 chart_type
                    const cTitle = item.chart_title || item.title;
                    const cType = item.chart_type || item.type;

                    // 1. 更新面板标题
                    // demo.html 中标题通常在 .panel h2 或 id="title-xxx"
                    const titleEl = document.getElementById('title-' + posId);
                    if (titleEl) {
                        titleEl.innerText = cTitle;
                    }

                    // 2. 动态注入搜索/过滤框 (如果有该函数)
                    if (typeof injectFilters === 'function') {
                        injectFilters(posId, cType);
                    }

                    // 3. 执行绘图
                    // 从 charts_all.js 的 ChartRegistry 货架取货
                    const drawFunc = ChartRegistry[cType];
                    
                    if (typeof drawFunc === 'function') {
                        console.log(`正在渲染位置 ${posId}，类型: ${cType}`);
                        
                        // 稍微延时 100ms，等待 injectFilters 生成的 DOM 稳定
                        setTimeout(() => {
                            try {
                                drawFunc(posId); 
                            } catch (e) {
                                console.error(`位置 ${posId} 绘图执行失败:`, e);
                            }
                        }, 100);
                    } else {
                        console.warn(`位置 ${posId} 的图表类型 [${cType}] 在 ChartRegistry 中未定义或为 null`);
                    }
                });
            } else {
                console.error("配置接口返回状态码错误:", res.msg);
            }
        })
        .catch(err => {
            console.error("请求图表配置接口失败:", err);
        });
}

/**
 * 动态过滤器注入器
 * @param {string} posId 位置ID (如 pos4)
 * @param {string} type 图表类型
 */
//字典抓函数
function dispatchChartRender(posId, type) {
    const val = document.getElementById(`in-${posId}`).value;
    
    // 从之前定义的 ChartRegistry 字典里直接抓取函数
    const renderFunc = ChartRegistry[type];
    
    if (typeof renderFunc === 'function') {
        renderFunc(posId, val);
    } else {
        console.error(`未找到类型为 ${type} 的初始化函数`);
    }
}
//搜索框逻辑
function injectFilters(posId, type) {
    const container = document.getElementById(posId);
    if (!container) return;

    // 清理旧搜索框
    const oldFilter = container.querySelector('.chart-filter');
    if (oldFilter) oldFilter.remove();

    const filterDiv = document.createElement('div');
    filterDiv.className = 'chart-filter';

    // 需要统一搜索框的图表类型（用户可输入年份或电影名）
    const unifiedSearchTypes = [
        'line_trend', 
        'scatter_score', 
        'budget_scatter', 
        'bubble_social', 
        'scatter_duration'
    ];

    if (unifiedSearchTypes.includes(type)) {
        // 统一搜索框：提示“输入年份或电影名”
        filterDiv.innerHTML = `
            <input type="text" id="in-${posId}" placeholder="输入年份或电影名">
            <button onclick="dispatchChartRender('${posId}', '${type}')">确定</button>
        `;
    } else if (type === 'radar_map') {
        // 雷达图保留双输入框
        filterDiv.innerHTML = `
            <input type="text" id="in1-${posId}" placeholder="电影1" style="width:60px;">
            <input type="text" id="in2-${posId}" placeholder="电影2" style="width:60px;">
            <button onclick="initRadarChart('${posId}', document.getElementById('in1-${posId}').value, document.getElementById('in2-${posId}').value)">对比</button>
        `;
    } else {
        // 其他图表类型不添加搜索框
        return;
    }

    const chartDom = container.querySelector('.chart');
    container.insertBefore(filterDiv, chartDom);
}
