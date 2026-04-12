(function() {
            const messageModal = document.getElementById('messageModal');
            const msgBtn = document.querySelector('.msg-btn');
            const closeMessageModal = document.getElementById('closeMessageModal');
            const submitMessage = document.getElementById('submitMessage');
            const messageInput = document.getElementById('messageInput');

            // 留言才能登陆
            if (msgBtn) {
                msgBtn.onclick = function() {
                    const username = localStorage.getItem('username');
                    if (!username) {
                        alert('请先登录后再留言');
                        return;
                    }
                    messageModal.style.display = 'flex';
                };
            }
            // 关闭按钮留言弹窗
            if (closeMessageModal) {
                closeMessageModal.onclick = function() {
                    messageModal.style.display = 'none';
                };
            }
            // 点击弹窗外部关闭
            if (messageModal) {
                messageModal.addEventListener('click', function(e) {
                    if (e.target === messageModal) messageModal.style.display = 'none';
                });
            }

            if (submitMessage) {
                submitMessage.onclick = function() {
                    const message = messageInput.value.trim();
                    if (!message) { alert('留言内容不能为空'); return; }
                    const username = localStorage.getItem('username');
                    if (!username) { alert('登录信息已失效，请重新登录'); return; }
                    fetch('http://localhost:3000/api/messages', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, message })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.code === 200) {
                            alert('留言成功！');
                            messageInput.value = '';
                            messageModal.style.display = 'none';
                            // 刷新留言列表,清空并关闭
                        } else {
                            alert('留言失败：' + data.msg);
                        }
                    })
                    .catch(err => { console.error(err); alert('网络错误，请稍后重试'); });
                };
            }
        })();