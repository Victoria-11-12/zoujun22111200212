// 微调数据模块 - 导出 JSONL 格式数据

// 导出按钮点击事件
function bindExportEvents() {
    // 预览按钮
    const previewBtn = document.getElementById('previewBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewData);
    }

    // 导出按钮
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportJsonl);
    }
}

// 获取筛选条件
function getFilterParams() {
    const minScore = document.getElementById('minScoreSelect')?.value || '4';
    
    // 获取选中的数据来源
    const checkboxes = document.querySelectorAll('#finetune-panel .checkbox-group input[type="checkbox"]:checked');
    const tables = Array.from(checkboxes).map(cb => cb.value);
    
    const startDate = document.getElementById('finetuneStartDate')?.value || '';
    const endDate = document.getElementById('finetuneEndDate')?.value || '';
    
    return { minScore, tables, startDate, endDate };
}

// 预览数据
async function previewData() {
    const previewDiv = document.getElementById('jsonlPreview');
    previewDiv.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const { minScore, tables, startDate, endDate } = getFilterParams();
        
        // 构建查询参数
        const params = new URLSearchParams();
        params.append('min_score', minScore);
        params.append('limit', '10'); // 预览只显示前10条
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        tables.forEach(t => params.append('tables', t));
        
        const response = await fetch(`http://localhost:3000/api/analyst/preview?${params.toString()}`);
        const data = await response.json();
        
        if (data.error) {
            previewDiv.innerHTML = `<div class="error-tip">错误: ${data.error}</div>`;
            return;
        }
        
        if (!data.records || data.records.length === 0) {
            previewDiv.innerHTML = '<div class="empty-tip">没有找到符合条件的数据</div>';
            return;
        }
        
        // 显示预览数据
        let html = '<div class="preview-list">';
        data.records.forEach((record, index) => {
            html += `
                <div class="preview-item">
                    <div class="preview-header">#${index + 1} - 评分: ${record.score || 'N/A'}</div>
                    <pre class="preview-content">${escapeHtml(JSON.stringify(record, null, 2))}</pre>
                </div>
            `;
        });
        html += '</div>';
        html += `<div class="preview-summary">共找到 ${data.total} 条数据，显示前 10 条</div>`;
        
        previewDiv.innerHTML = html;
        
    } catch (error) {
        console.error('预览失败:', error);
        previewDiv.innerHTML = '<div class="error-tip">加载失败，请稍后重试</div>';
    }
}

// 导出 JSONL 文件
async function exportJsonl() {
    const exportBtn = document.getElementById('exportBtn');
    const originalText = exportBtn.textContent;
    exportBtn.textContent = '导出中...';
    exportBtn.disabled = true;
    
    try {
        const { minScore, tables, startDate, endDate } = getFilterParams();
        
        // 构建查询参数
        const params = new URLSearchParams();
        params.append('min_score', minScore);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        tables.forEach(t => params.append('tables', t));
        
        const response = await fetch(`http://localhost:3000/api/analyst/export?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error('导出失败');
        }
        
        // 获取文件名
        const disposition = response.headers.get('Content-Disposition');
        let filename = 'fine_tune_data.jsonl';
        if (disposition) {
            const match = disposition.match(/filename="(.+)"/);
            if (match) filename = match[1];
        }
        
        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('导出成功！', 'success');
        
    } catch (error) {
        console.error('导出失败:', error);
        showToast('导出失败: ' + error.message, 'error');
    } finally {
        exportBtn.textContent = originalText;
        exportBtn.disabled = false;
    }
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示提示消息
function showToast(message, type = 'info') {
    // 移除已有的 toast
    const existingToast = document.querySelector('.toast-message');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    toast.textContent = message;
    
    // 样式
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 4px;
        color: white;
        font-size: 14px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    if (type === 'success') {
        toast.style.backgroundColor = '#52c41a';
    } else if (type === 'error') {
        toast.style.backgroundColor = '#ff4d4f';
    } else {
        toast.style.backgroundColor = '#1890ff';
    }
    
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .loading {
        text-align: center;
        padding: 40px;
        color: #999;
    }
    .error-tip {
        text-align: center;
        padding: 40px;
        color: #ff4d4f;
    }
    .preview-list {
        max-height: 500px;
        overflow-y: auto;
    }
    .preview-item {
        margin-bottom: 16px;
        border: 1px solid #e8e8e8;
        border-radius: 4px;
        overflow: hidden;
    }
    .preview-header {
        background: #f5f5f5;
        padding: 8px 12px;
        font-size: 12px;
        color: #666;
        border-bottom: 1px solid #e8e8e8;
    }
    .preview-content {
        margin: 0;
        padding: 12px;
        background: #fafafa;
        font-size: 12px;
        line-height: 1.5;
        overflow-x: auto;
    }
    .preview-summary {
        text-align: center;
        padding: 12px;
        color: #666;
        font-size: 12px;
        border-top: 1px solid #e8e8e8;
    }
`;
document.head.appendChild(style);

// 页面加载完成后绑定事件
document.addEventListener('DOMContentLoaded', bindExportEvents);
