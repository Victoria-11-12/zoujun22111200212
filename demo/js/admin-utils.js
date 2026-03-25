// 通用工具模块

function ensureMovieData(callback) {
    if (window.movieData && window.movieData.length > 0) {
        console.log("数据已就绪，直接渲染...");
        if (typeof callback === 'function') callback();
        return;
    }

    console.log("正在从服务器获取电影基础数据...");
    fetch('http://localhost:3000/api/movies')
        .then(res => {
            if (!res.ok) throw new Error('网络响应错误');
            return res.json();
        })
        .then(data => {
            window.movieData = data; 
            console.log("后台数据加载成功，总条数:", window.movieData.length);
            if (typeof callback === 'function') callback();
        })
        .catch(err => {
            console.error("ensureMovieData 失败:", err);
            if (typeof callback === 'function') callback();
        });
}
