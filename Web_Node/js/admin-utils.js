// 通用工具模块

function ensureMovieData(callback) {
    if (window.movieData && window.movieData.length > 0) {
        if (typeof callback === 'function') callback();
        return;
    }

    fetch('http://localhost:3000/api/movies')
        .then(res => {
            if (!res.ok) throw new Error('网络响应错误');
            return res.json();
        })
        .then(data => {
            window.movieData = data;
            if (typeof callback === 'function') callback();
        })
        .catch(err => {
            console.error("ensureMovieData 失败:", err);
            if (typeof callback === 'function') callback();
        });
}
