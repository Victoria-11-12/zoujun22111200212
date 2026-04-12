// 用户管理模块

window.loadUserList = function() {
    fetch('http://localhost:3000/api/admin/users')
        .then(res => res.json())
        .then(res => {
            if (res.code === 200) {
                const tbody = document.getElementById('userTableBody');
                tbody.innerHTML = '';
                res.data.forEach(user => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${user.id}</td>
                        <td>${user.username}</td>
                        <td><span class="badge ${user.role}">${user.role}</span></td>
                        <td>${new Date(user.create_time).toLocaleString()}</td>
                        <td>
                            <button class="edit-btn" onclick="editUser(${user.id})">修改</button>
                            <button class="del-btn" onclick="deleteUser(${user.id})">删除</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        });
};

window.deleteUser = function(id) {
    if (confirm('确定要删除该用户吗？')) {
        fetch(`http://localhost:3000/api/admin/users/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(res => {
                alert(res.msg);
                loadUserList();
            });
    }
};

window.editUser = function(id) {
    const newRole = prompt("将该用户角色修改为 (user/admin):");
    if (newRole !== 'user' && newRole !== 'admin') return alert("请输入有效的角色名");
    fetch(`http://localhost:3000/api/admin/users/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
    })
    .then(res => res.json())
    .then(res => {
        alert(res.msg);
        loadUserList();
    });
};

// 新增用户
document.querySelector('.add-btn').onclick = function() {
    const username = prompt("请输入新用户名:");
    if (!username) return;
    const password = prompt("请输入初始密码:");
    if (!password) return;
    const role = prompt("请输入角色 (user 或 admin):", "user");
    fetch('http://localhost:3000/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role })
    })
    .then(res => res.json())
    .then(res => {
        alert(res.msg);
        loadUserList();
    });
};

// 搜索用户
document.getElementById('userSearch').oninput = function() {
    const keyword = this.value.toLowerCase();
    document.querySelectorAll('#userTableBody tr').forEach(row => {
        const username = row.children[1].innerText.toLowerCase();
        row.style.display = username.includes(keyword) ? '' : 'none';
    });
};
