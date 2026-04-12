   // 获取 DOM 元素
    const modal = document.getElementById("searchModal");
    const searchBtn = document.getElementById("searchBtn");
    const closeBtn = document.querySelector(".close-btn");
    const execSearch = document.getElementById("execSearch");

    const titleInput = document.getElementById('inputTitle');
    const directorInput = document.getElementById('inputDirector');
    const yearInput = document.getElementById('inputYear');
    const actorInput = document.getElementById('inputActor');

    titleInput.addEventListener('input', debounceSearch);
    directorInput.addEventListener('input', debounceSearch);
    yearInput.addEventListener('input', debounceSearch);
    actorInput.addEventListener('input', debounceSearch);

    // 延迟300ms执行，避免频繁搜索
    let debounceTimer;
    function debounceSearch() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(performSearch, 300);
    }

    // 1. 控制弹窗开关
    searchBtn.onclick = () => {
        const username = localStorage.getItem('username');
        if (!username) {
            alert('请先登录后再使用搜索功能');
            return;
        }
        modal.style.display = "block";
    };
    closeBtn.onclick = () => {
        modal.style.display = "none";
    };
        // 合并背景点击关闭事件
        window.onclick = function(event) {
            const searchModal = document.getElementById('searchModal');
            const messageModal = document.getElementById('messageModal');
            const aiModal = document.getElementById('aiModal');
            if (event.target == searchModal) searchModal.style.display = 'none';
            if (event.target == messageModal) messageModal.style.display = 'none';
            if (event.target == aiModal) aiModal.style.display = 'none';
        };
        
    function performSearch() {
        // 2. 核心查询逻辑 
        console.log("开始执行搜索...");
        
        // 获取并清洗输入数据
        const title = document.getElementById('inputTitle').value.trim().toLowerCase();
        const director = document.getElementById('inputDirector').value.trim().toLowerCase();
        const actor = document.getElementById('inputActor').value.trim().toLowerCase();
        const year = document.getElementById('inputYear').value.trim();

        // 过滤 movieData 数组
        const filteredResults = window.movieData.filter(m => {
            let isMatch = true;
            
            // 电影名过滤：使用 (m.movie_title || "") 防止数据缺失导致报错
            // 使用 .replace(/\u00a0/g, " ") 处理某些数据中存在的不间断空格
            if (title) {
                const mTitle = (m.movie_title || "").toString().replace(/\u00a0/g, " ").trim().toLowerCase();
                if (!mTitle.includes(title)) isMatch = false;
                // 没有输入电影名则不匹配
            }
            
            // 导演名过滤
            if (isMatch && director) {
                const mDirector = (m.director_name || "").toString().toLowerCase();
                if (!mDirector.includes(director)) isMatch = false;
            }
            
            // 年份过滤 (模糊匹配)
            if (isMatch && year) {
                const mTitle_year = (m.title_year || "").toString().toLowerCase();
                if (!mTitle_year.includes(year)) isMatch = false;
            }
            
            // 演员过滤 (检查主演字段)
            if (isMatch && actor) {
                const a1 = (m.actor_1_name || "").toString().toLowerCase();
                if (!(a1.includes(actor))) {
                    isMatch = false;
                }
            }
            return isMatch;
        });

        console.log("搜索结束，找到结果数量:", filteredResults.length);
        renderSearchResults(filteredResults);
    };
    // 查询按钮绑定
    execSearch.onclick = function() {
        performSearch();
    };

    // 3. 渲染结果函数
    function renderSearchResults(data) {
        const container = document.getElementById('resultArea');
        
        if (data.length === 0) {
            container.innerHTML = 
            '<p style="text-align:center; padding: 20px; color: #ffeb3b;">未找到匹配的数据，请检查输入或更换关键词。</p>';
            return;
        }

        let html = `<table class="search-results-table">
        <thead>
            <tr>
            <th>电影名称</th>
            <th>导演</th>
            <th>主演</th>
            <th>年份</th>
            <th>票房(M)</th>
            </tr>
        </thead>
        <tbody>`;
  
        data.forEach(m => {
        const grossM = m.gross ? (m.gross / 1000000).toFixed(2) : '未知';
        html += `<tr>
            <td class="movie-title">${(m.movie_title || '未知').trim()}</td>
            <td>${m.director_name || '未知'}</td>
            <td>${m.actor_1_name || '未知'}</td>
            <td>${m.title_year || '未知'}</td>
            <td class="gross-value">${grossM}</td>
        </tr>`;
        });
                html += '</tbody></table>';
                container.innerHTML = html;
            }
