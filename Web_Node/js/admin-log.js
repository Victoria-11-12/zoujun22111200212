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
                        <td><span class="badge user">${log.username}</span></td>
                        <td>${log.action}</td>
                        <td><code style="padding:2px 5px;border-radius:3px">${log.ip}</code></td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        });
};
