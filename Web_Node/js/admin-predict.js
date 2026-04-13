// 票房预测模块

// 获取黑马数据并渲染表格
async function loadDarkHorses() {
    const listContainer = document.getElementById('darkHorseList');
    try {
        const response = await fetch('http://localhost:5000/api/flask/dark_horses');
        const res = await response.json();
        
        if (res.code === 200) {
            let html = '';
            res.data.forEach(movie => {
                const roi = movie.budget > 0 ? (movie.predicted_gross / movie.budget).toFixed(2) : 'N/A';
                html += `
                    <tr>
                        <td>${movie.movie_title}</td>
                        <td>${movie.budget.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
                        <td>${movie.predicted_gross.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
                        <td style="color: #52c41a; font-weight: bold;">${roi}x</td>
                    </tr>
                `;
            });
            listContainer.innerHTML = html;
        }
    } catch (error) {
        listContainer.innerHTML = '<tr><td colspan="4" style="color:red">无法连接到 Flask 预测服务器</td></tr>';
    }
}

// 提交深度预测表单
async function handleDeepPrediction(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const rawData = Object.fromEntries(formData.entries());
    
    const data = {
        budget: parseFloat(rawData.budget) || 0,
        genres: rawData.genres || '',
        New_Director: rawData.New_Director || '',
        New_Actor: rawData.New_Actor || ''
    };
    
    const resultValue = document.querySelector('.result-value');
    resultValue.innerText = '计算中...';

    try {
        const response = await fetch('http://localhost:5000/api/flask/predict_deep', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const res = await response.json();
        
        if (res.code === 200) {
            const formattedPrice = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(res.predicted_gross);
            resultValue.innerText = formattedPrice;
        } else {
            resultValue.innerText = '预测失败';
        }
    } catch (error) {
        resultValue.innerText = '服务器连接失败';
    }
}
