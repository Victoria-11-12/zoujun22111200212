// 页面主逻辑 - 负责Tab切换和退出系统

document.addEventListener('DOMContentLoaded', function() {
    initTabSwitch();
    initLogout();

    // 页面加载时，如果数据概览Tab是激活状态，自动初始化
    const activeTab = document.querySelector('.tab-item.active');
    if (activeTab && activeTab.getAttribute('data-tab') === 'overview' && typeof initOverview === 'function') {
        initOverview();
    }
});

// Tab 切换功能
function initTabSwitch() {
    const tabItems = document.querySelectorAll('.tab-item');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabItems.forEach(item => {
        item.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // 如果点击的是当前已激活的Tab，不重复初始化
            if (this.classList.contains('active')) {
                return;
            }

            // 移除所有Tab的激活状态
            tabItems.forEach(tab => tab.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));

            // 激活当前Tab
            this.classList.add('active');

            // 显示对应面板
            const targetPanel = document.getElementById(targetTab + '-panel');
            if (targetPanel) {
                targetPanel.classList.add('active');
            }

            // 触发对应模块的初始化（如果存在）
            if (targetTab === 'overview' && typeof initOverview === 'function') {
                initOverview();
            } else if (targetTab === 'evaluation' && typeof initEvaluation === 'function') {
                initEvaluation();
            } else if (targetTab === 'finetune' && typeof initFinetune === 'function') {
                initFinetune();
            }
        });
    });
}

// 退出系统功能
function initLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            // 清除本地存储的登录信息
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            localStorage.removeItem('role');

            // 跳转到登录页面
            window.location.href = 'login.html';
        });
    }
}
