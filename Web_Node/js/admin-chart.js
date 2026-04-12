// 图表更替模块

function executeLoadConfigs() {
    fetch('http://localhost:3000/api/charts/config?t=' + Date.now())
        .then(res => res.json())
        .then(res => {
            const container = document.getElementById('chartConfigBody');
            if (!container) return;
            container.innerHTML = '';
            
            const configs = res.data;

            window.chartConfigs = configs;

            Object.keys(configs).forEach(posId => {
                const item = configs[posId];
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="text-align:center;"><b>${posId}</b></td>
                    <td><input type="text" id="title-${posId}" value="${item.title}" class="table-input"></td>
                    <td>
                        <select id="type-${posId}" onchange="handleTypeChange('${posId}', this)" class="table-select">
                            ${CHART_OPTIONS.map(opt => `
                                <option value="${opt.value}" ${opt.value === item.type ? 'selected' : ''}>${opt.text}</option>
                            `).join('')}
                        </select>
                    </td>
                    <td style="text-align:center;">
                        <button onclick="saveChartUpdate('${posId}')" class="btn-save">保存修改</button>
                    </td>
                `;
                container.appendChild(tr);
            });

            renderSupermarketPreview();
        })
        .catch(err => console.error("配置列表加载失败:", err));
}

function loadChartConfigs() {
    if (!window.movieData || window.movieData.length === 0) {
        ensureMovieData(executeLoadConfigs);
    } else {
        executeLoadConfigs();
    }
}

function renderSupermarketPreview() {
    const grid = document.getElementById('supermarketGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const usageMap = {};
    if (window.chartConfigs) {
        Object.entries(window.chartConfigs).forEach(([pos, cfg]) => {
            const type = cfg.chart_type || cfg.type;
            if (!usageMap[type]) usageMap[type] = [];
            usageMap[type].push(pos.toUpperCase());
        });
    }

    Object.keys(ChartRegistry).forEach(key => {
        const drawFunc = ChartRegistry[key];
        const isReady = (typeof drawFunc === 'function');

        let displayName = key;
        const opt = CHART_OPTIONS.find(o => o.value === key);
        if (opt) {
            displayName = opt.text.includes('：') ? opt.text.split('：')[1] : opt.text;
        }

        const usageList = usageMap[key] || [];
        const usageText = usageList.length ? `使用中：${usageList.join('、')}` : '未使用';
        const usageColor = usageList.length ? '#ff4d4f' : '#aaa';

        const box = document.createElement('div');
        box.className = `chart-item-box ${!isReady ? 'gray' : ''}`;
        box.innerHTML = `
            <div class="item-header" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #303030;">
                <span class="item-title" style="color: #00f6ff; font-weight: bold;">${displayName}</span>
                <div style="display: flex; gap: 6px;">
                    <select class="pos-select" style="width: 80px; padding:4px; background: #1a1a1a; color: white; border: 1px solid #4c9bfd; border-radius:4px;">
                        <option value="">应用至</option>
                        <option value="pos1">POS1</option>
                        <option value="pos2">POS2</option>
                        <option value="pos3">POS3</option>
                        <option value="pos4">POS4</option>
                        <option value="pos5">POS5</option>
                        <option value="pos6">POS6</option>
                    </select>
                    <button class="apply-btn" style="padding: 4px 8px; background: #1890ff; color: white; border: none; border-radius:4px; cursor: pointer;">应用</button>
                </div>
            </div>
            <div class="usage-info" style="padding: 4px 12px; background: #262626; color: ${usageColor}; font-size: 11px; border-bottom:1px solid #434343;">
                ${usageText}
            </div>
            <div id="pv-${key}" class="preview-container" style="height:200px; width:100%;"></div>
        `;
        grid.appendChild(box);

        const applyBtn = box.querySelector('.apply-btn');
        const posSelect = box.querySelector('.pos-select');
        applyBtn.onclick = () => {
            const targetPos = posSelect.value;
            if (!targetPos) {
                alert('请先选择目标工位');
                return;
            }
            applyChartToPosition(key, targetPos);
        };

        if (isReady && window.movieData && window.movieData.length > 0) {
            setTimeout(() => {
                try {
                    drawFunc(`pv-${key}`);
                } catch (e) {
                    console.warn(`图表 ${key} 渲染失败:`, e);
                }
            }, 200);
        }
    });
}

window.handleTypeChange = function(posId, selectEl) {
    const selectedText = selectEl.options[selectEl.selectedIndex].text;
    const titleInput = document.getElementById('title-' + posId);
    if (titleInput) {
        const autoTitle = selectedText.includes('：') ? selectedText.split('：')[1] : selectedText;
        titleInput.value = autoTitle;
    }
};

window.saveChartUpdate = function(posId) {
    const newTitle = document.getElementById('title-' + posId).value;
    const newType = document.getElementById('type-' + posId).value;
    fetch('http://localhost:3000/api/charts/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position_id: posId, chart_type: newType, chart_title: newTitle })
    })
    .then(res => res.json())
    .then(res => {
        if (res.code === 200) {
            alert('✅ 更替成功！请刷新大屏查看效果。');
            loadChartConfigs();
        } else {
            alert('❌ 修改失败：' + res.msg);
        }
    });
};

window.applyChartToPosition = function(chartKey, targetPos) {
    const opt = CHART_OPTIONS.find(o => o.value === chartKey);
    const defaultTitle = opt ? (opt.text.includes('：') ? opt.text.split('：')[1] : opt.text) : chartKey;

    fetch('http://localhost:3000/api/charts/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            position_id: targetPos,
            chart_type: chartKey,
            chart_title: defaultTitle
        })
    })
    .then(res => res.json())
    .then(res => {
        if (res.code === 200) {
            alert(`✅ 已应用至 ${targetPos.toUpperCase()}`);
            loadChartConfigs();
        } else {
            alert('❌ 应用失败：' + res.msg);
        }
    })
    .catch(err => {
        console.error('应用失败', err);
        alert('网络错误，请稍后重试');
    });
};
