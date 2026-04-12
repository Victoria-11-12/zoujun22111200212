// 操作日志模块

window.loadLogList = function() {
    fetch('http://localhost:3000/api/admin/logs')
        .then(res => res.json())
        .then(res => {
            if (res.code === 200) {
                const tbody = document.getElementById('logTableBody');
                tbody.innerHTML = '';
                res.data.forEach(log => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${new Date(log.create_time).toLocaleString()}</td>
                        <td><b style="color:#1890ff">${log.username}</b></td>
                        <td>${log.action}</td>
                        <td><code style="background:#f5f5f5;padding:2px 5px;border-radius:3px">${log.ip}</code></td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        });
};
