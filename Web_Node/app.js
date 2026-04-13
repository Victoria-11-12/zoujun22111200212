require('dotenv').config();

const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');//跨域访问，接上flask
const bcrypt = require('bcryptjs'); 
const jwt = require('jsonwebtoken'); 
const OpenAI = require('openai');

const app = express();
app.use(cors()); 

//解析 JSON 格式的请求体，否则无法获取前端传来的用户名和密码
app.use(express.json());
app.use(express.static('./'));

// 数据库连接配置
const db = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

// --- [日志工具函数] ---
const saveLog = (username, action, req) => {
    const ip = req.ip === '::1' ? '127.0.0.1' : req.ip.replace('::ffff:', ''); // 格式化 IP 地址
    const sql = 'INSERT INTO logs (username, action, ip) VALUES (?, ?, ?)';
    db.query(sql, [username || '未知用户', action, ip], (err) => {
        if (err) console.error('日志写入失败:', err);
    });
};

// 定义 JWT 密钥
const SECRET_KEY = 'your_movie_data_secret_key_123';

// ------------------- 注册 -------------------
app.post('/api/register', (req, res) => {
    const { username, password } = req.body;

    // 1. 检查数据是否完整
    if (!username || !password) {
        return res.send({ code: 400, msg: '用户名或密码不能为空' });
    }

    // 2. 检查用户名是否已存在
    const checkSql = 'SELECT * FROM users WHERE username = ?';
    db.query(checkSql, [username], (err, results) => {
        if (err) return res.send({ code: 500, msg: '数据库查询错误' });
        if (results.length > 0) {
            return res.send({ code: 400, msg: '用户名已被占用' });
        }

        // 3. 对密码进行加密处理 (强度设置为 10)
        const hashedPassword = bcrypt.hashSync(password, 10);

        // 4. 将用户信息写入数据库
        const insertSql = 'INSERT INTO users (username, password, role) VALUES (?, ?, ?)';
        db.query(insertSql, [username, hashedPassword, 'user'], (err, results) => {
            if (err) return res.send({ code: 500, msg: '注册失败' });
            res.send({ code: 200, msg: '注册成功！' });
        });
    });
});


// ------------------- 登录 -------------------
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;

    // 1. 基础检查
    if (!username || !password) {
        return res.send({ code: 400, msg: '用户名或密码不能为空' });
    }

    // 2. 根据用户名查询用户信息
    const sql = 'SELECT * FROM users WHERE username = ?';
    db.query(sql, [username], (err, results) => {
        if (err) return res.send({ code: 500, msg: '服务器数据库错误' });
        
        // 3. 检查用户是否存在
        if (results.length === 0) {
            return res.send({ code: 400, msg: '该用户不存在' });
        }

        const user = results[0];

        // 4. 使用 bcrypt 比对前端传来的明文密码和数据库里的密文
        const isMatch = bcrypt.compareSync(password, user.password);
        if (!isMatch) {
            return res.send({ code: 400, msg: '密码错误' });
        }

        // 5. 密码正确，签发 Token (有效期设置为 24小时)
        // 载荷中存入用户 id, username 和 role，方便后续权限判定
        const token = jwt.sign(
            { id: user.id, username: user.username, role: user.role },
            SECRET_KEY,
            { expiresIn: '24h' }
        );

        // 6. 返回成功信息、Token 和 角色
        saveLog(user.username, '执行了登录操作', req);
        res.send({
            code: 200,
            msg: '登录成功',
            token: 'Bearer ' + token, // 规范写法，加一个 Bearer 前缀
            role: user.role
        });
    });
});


// 2. 获取电影数据的接口 (保留原有逻辑)
app.get('/api/movies', (req, res) => {
    const sql = "SELECT * FROM movies"; 
    db.query(sql, (err, results) => {
        if (err) return res.status(500).json({ error: '数据库查询出错' });
        res.json(results);
    });
});

// ------------------- 管理员：获取所有用户列表 -------------------
app.get('/api/admin/users', (req, res) => {
    // 简单起见，我们先不在这里做复杂的 Token 验证，先让数据跑通
    const sql = 'SELECT id, username, role, create_time FROM users';
    db.query(sql, (err, results) => {
        if (err) return res.send({ code: 500, msg: '获取用户列表失败' });
        res.send({ code: 200, data: results });
    });
});

// ------------------- 管理员：删除用户 -------------------
app.delete('/api/admin/users/:id', (req, res) => {
    const id = req.params.id;
    const sql = 'DELETE FROM users WHERE id = ?';
    db.query(sql, [id], (err, results) => {
        if (err) return res.send({ code: 500, msg: '删除失败' });
        res.send({ code: 200, msg: '删除成功' });
    });
});

// ------------------- 管理员：新增用户 -------------------
app.post('/api/admin/users', (req, res) => {
    const { username, password, role } = req.body;
    // 先加密密码再存入
    const hashedPassword = bcrypt.hashSync(password, 10);
    const sql = 'INSERT INTO users (username, password, role) VALUES (?, ?, ?)';
    db.query(sql, [username, hashedPassword, role || 'user'], (err, results) => {
        if (err) return res.send({ code: 500, msg: '用户名可能已存在' });
        res.send({ code: 200, msg: '新增用户成功' });
    });
});

// ------------------- 管理员：修改用户权限/信息 -------------------
app.put('/api/admin/users/:id', (req, res) => {
    const id = req.params.id;
    const { role } = req.body; // 这里以修改角色为例
    const sql = 'UPDATE users SET role = ? WHERE id = ?';
    db.query(sql, [role, id], (err, results) => {
        if (err) return res.send({ code: 500, msg: '修改失败' });
        res.send({ code: 200, msg: '修改成功' });
    });
});


// --- [管理员：获取操作日志列表] ---
app.get('/api/admin/logs', (req, res) => {
    const sql = 'SELECT * FROM logs ORDER BY create_time DESC LIMIT 100';
    db.query(sql, (err, results) => {
        if (err) return res.send({ code: 500, msg: '获取日志失败' });
        res.send({ code: 200, data: results });
    });
});

// --- [模块三：获取全图表配置 (供大屏使用)] ---
app.get('/api/charts/config', (req, res) => {
    // 查询数据库中 6 个工位的所有配置
    const sql = 'SELECT position_id, chart_type, chart_title FROM chart_configs';
    db.query(sql, (err, results) => {
        if (err) {
            console.error('数据库查询失败:', err);
            return res.send({ code: 500, msg: '获取配置失败' });
        }
        
        // 将数据库数组格式转换为前端好处理的对象格式
        // 转换后：{ pos1: { type: 'bar_top10', title: '...' }, pos2: ... }
        const configMap = {};
        results.forEach(row => {
            configMap[row.position_id] = {
                type: row.chart_type,
                title: row.chart_title
            };
        });
        
        res.send({ code: 200, data: configMap });
    });
});

// --- [模块三：修改图表配置 (供后台管理使用)] ---
app.post('/api/charts/update', (req, res) => {
    const { position_id, chart_type, chart_title } = req.body;
    
    // 更新数据库中对应位置的图表类型和标题
    const sql = 'UPDATE chart_configs SET chart_type = ?, chart_title = ? WHERE position_id = ?';
    db.query(sql, [chart_type, chart_title, position_id], (err, results) => {
        if (err) {
            console.error('更新失败:', err);
            return res.send({ code: 500, msg: '更新数据库失败' });
        }
        res.send({ code: 200, msg: '图表更替成功！' });
    });
});
// --- [模块五：获取用户留言] ---
// -
// ------------------- 用户提交留言接口 -------------------
app.post('/api/messages', (req, res) => {
    const { username, message } = req.body;
    if (!username || !message) {
        return res.send({ code: 400, msg: '用户名和留言内容不能为空' });
    }
    const sql = 'INSERT INTO user_messages (username, message) VALUES (?, ?)';
    db.query(sql, [username, message], (err, results) => {
        if (err) {
            console.error('留言保存失败:', err);
            return res.send({ code: 500, msg: '留言保存失败' });
        }
        res.send({ code: 200, msg: '留言成功' });
    });
});
// --- [管理员：获取留言列表] ---

app.get('/api/admin/messages', (req, res) => {
    const sql = 'SELECT id, username, message, mes_time FROM user_messages ORDER BY mes_time DESC';
    db.query(sql, (err, results) => {
        if (err) {
            console.error('获取留言列表失败:', err);
            return res.send({ code: 500, msg: '获取留言列表失败' });
        }
        res.send({ code: 200, data: results });
    });
});

// --- [管理员：删除留言] ---
app.delete('/api/admin/messages/:id', (req, res) => {
    const id = req.params.id;
    const sql = 'DELETE FROM user_messages WHERE id = ?';
    db.query(sql, [id], (err, results) => {
        if (err) {
            console.error('删除留言失败:', err);
            return res.send({ code: 500, msg: '删除留言失败' });
        }
        res.send({ code: 200, msg: '删除成功' });
    });
});

// ------------------- 分析师：数据概览 -------------------
app.get('/api/analyst/overview', (req, res) => {
    const result = {
        chat_trend: [],
        intent_distribution: [],
        chart_success_rate: { success: 0, fail: 0 },
        attack_distribution: []
    };

    // 1. 对话量趋势（最近30天）
    const chatTrendSql = `
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM user_chat_logs 
        GROUP BY DATE(created_at) 
        ORDER BY date DESC 
        LIMIT 30
    `;

    // 2. 意图分布（将NULL或空值归类为"缺失"）
    const intentSql = `
        SELECT 
            CASE 
                WHEN intent IS NULL OR intent = '' THEN '缺失'
                ELSE intent 
            END as intent, 
            COUNT(*) as count 
        FROM user_chat_logs 
        GROUP BY 
            CASE 
                WHEN intent IS NULL OR intent = '' THEN '缺失'
                ELSE intent 
            END
    `;

    // 3. 绘图成功率
    const chartSuccessSql = `
        SELECT is_success, COUNT(*) as count 
        FROM chart_generation_logs 
        GROUP BY is_success
    `;

    // 4. 攻击类型分布
    const attackSql = `
        SELECT warning_type, COUNT(*) as count 
        FROM security_warning_logs 
        GROUP BY warning_type
    `;

    // 执行所有查询
    db.query(chatTrendSql, (err, chatTrendResults) => {
        if (!err) {
            result.chat_trend = chatTrendResults.reverse(); // 按时间正序
        }

        db.query(intentSql, (err, intentResults) => {
            if (!err) {
                result.intent_distribution = intentResults;
            }

            db.query(chartSuccessSql, (err, chartResults) => {
                if (!err) {
                    chartResults.forEach(row => {
                        if (row.is_success === 1 || row.is_success === true) {
                            result.chart_success_rate.success = row.count;
                        } else {
                            result.chart_success_rate.fail = row.count;
                        }
                    });
                }

                db.query(attackSql, (err, attackResults) => {
                    if (!err) {
                        result.attack_distribution = attackResults;
                    }
                    res.send({ code: 200, data: result });
                });
            });
        });
    });
});

app.listen(3000, () => {
    console.log('--------------------------------------');
    console.log('后端启动成功');
    console.log('--------------------------------------');
});
