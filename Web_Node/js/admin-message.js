// 留言管理模块

window.loadMessageList = function() {
    fetch('http://localhost:3000/api/admin/messages')
        .then(res => res.json())
        .then(res => {
            if (res.code === 200) {
                const tbody = document.getElementById('messageTableBody');
                tbody.innerHTML = '';
                res.data.forEach(msg => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${msg.id}</td>
                        <td>${msg.username}</td>
                        <td>${msg.message}</td>
                        <td>${new Date(msg.mes_time).toLocaleString()}</td>
                        <td>
                            <button class="del-btn" onclick="deleteMessage(${msg.id})">删除</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                alert('获取留言列表失败：' + res.msg);
            }
        })
        .catch(err => {
            console.error('加载留言失败:', err);
            alert('网络错误，请稍后重试');
        });
};

window.deleteMessage = function(id) {
    if (confirm('确定要删除该留言吗？')) {
        fetch(`http://localhost:3000/api/admin/messages/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(res => {
                alert(res.msg);
                loadMessageList();
            })
            .catch(err => {
                console.error('删除失败:', err);
                alert('网络错误，请稍后重试');
            });
    }
};

// 绑定留言面板的刷新和搜索
const refreshBtn = document.getElementById('refreshMessages');
if (refreshBtn) {
    refreshBtn.onclick = loadMessageList;
}
const searchInput = document.getElementById('messageSearch');
if (searchInput) {
    searchInput.oninput = function() {
        const keyword = this.value.toLowerCase();
        document.querySelectorAll('#messageTableBody tr').forEach(row => {
            const username = row.children[1].innerText.toLowerCase();
            const message = row.children[2].innerText.toLowerCase();
            row.style.display = (username.includes(keyword) || message.includes(keyword)) ? '' : 'none';
        });
    };
}
