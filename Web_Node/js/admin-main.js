// 主入口模块

const menuItems = document.querySelectorAll('.menu-item');
const panels = document.querySelectorAll('.panel');
const currentTitle = document.getElementById('currentTitle') || { innerText: '', textContent: '' };

// 动态设置管理员名称
(function() {
    const username = localStorage.getItem('username');
    const adminNameEl = document.getElementById('adminName');
    if (username && adminNameEl) {
        adminNameEl.textContent = username;
    }
})();

function switchPanel(targetId) {
    menuItems.forEach(item => item.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-target="${targetId}"]`).classList.add('active');
    document.getElementById(targetId).classList.add('active');
    
    // 切换背景
    const mainContent = document.querySelector('.main-content');
    mainContent.classList.remove('panel-user-active', 'panel-log-active', 'panel-message-active');
    if (targetId === 'panel-user') {
        mainContent.classList.add('panel-user-active');
    } else if (targetId === 'panel-log') {
        mainContent.classList.add('panel-log-active');
    } else if (targetId === 'panel-message') {
        mainContent.classList.add('panel-message-active');
    }
    
    // 所有模块都不显示标题
    currentTitle.innerText = '';

    if (targetId === 'panel-user') {
        loadUserList();
    } else if (targetId === 'panel-log') {
        loadLogList();
    } else if (targetId === 'panel-chart') {
        loadChartConfigs();
    } else if (targetId === 'panel-message') {
        loadMessageList();
    } else if (targetId === 'panel-predict') {
        loadDarkHorses();
        loadROIComparison();
        const predForm = document.getElementById('predictionForm');
        if (predForm) {
            predForm.onsubmit = handleDeepPrediction;
        }
    }
}

menuItems.forEach(item => {
    item.addEventListener('click', function(e) {
        e.preventDefault();
        const target = this.getAttribute('data-target');
        switchPanel(target);
    });
});

switchPanel('panel-user');

document.getElementById('logoutBtn').onclick = function() {
    localStorage.clear();
    window.location.href = 'login.html';
};

ensureMovieData(() => {});
