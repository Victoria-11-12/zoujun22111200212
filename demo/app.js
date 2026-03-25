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

// --- [接口] ---
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY; 

const openai = new OpenAI({
    baseURL: 'https://api.deepseek.com',
    apiKey: DEEPSEEK_API_KEY
});

// 存储对话历史（内存存储）
const conversationHistory = new Map();
const MAX_HISTORY_LENGTH = 10; // 保留最近10轮对话

const tools = [
    {
        //写法硬性要求三type: 第一个为function，第二个为object，第三个为具体数据类型
        type: 'function',
        function: {
            name: 'query_movie_by_title',
            description: '根据电影名称查询电影详细信息',
            parameters: {
                type: 'object',
                properties: {
                    movie_title: {
                        type: 'string',
                        description: '电影名称'
                    }
                },
                required: ['movie_title']
            }
        }
    },
    {
        type: 'function',
        function: {
            name: 'query_person_by_name',
            description: '根据演员或导演姓名查询其参与的电影和总票房',
            parameters: {
                type: 'object',
                properties: {
                    person_name: {
                        type: 'string',
                        description: '演员或导演姓名'
                    }
                },
                required: ['person_name']
            }
        }
    },
    {
        type: 'function',
        function: {
            name: 'query_movie_by_rank',
            description: '根据票房排名查询电影信息',
            parameters: {
                type: 'object',
                properties: {
                    rank: {
                        type: 'number',
                        description: '票房排名（1表示票房最高）'
                    }
                },
                required: ['rank']
            }
        }
    }
];

//标题查询电影信息
async function queryMovieByTitle(movie_title) {
    return new Promise((resolve, reject) => {
        const sql = 'SELECT * FROM movies WHERE movie_title = ?';
        db.query(sql, [movie_title], (err, results) => {
            if (err) reject(err);
            else resolve(results);
        });
    });
}
//演员或导演姓名查询其参与的电影和总票房
async function queryPersonByName(person_name) {
    return new Promise((resolve, reject) => {
        const sql = `
            SELECT 
                movie_title, 
                title_year, 
                genres, 
                imdb_score, 
                gross, 
                director_name,
                actor_1_name,
                actor_2_name,
                actor_3_name,
                CASE 
                    WHEN director_name LIKE ? THEN '导演'
                    WHEN actor_1_name LIKE ? THEN '主演'
                    WHEN actor_2_name LIKE ? THEN '主演'
                    WHEN actor_3_name LIKE ? THEN '主演'
                    ELSE '未知'
                END as role
            FROM movies 
            WHERE director_name LIKE ? 
               OR actor_1_name LIKE ? 
               OR actor_2_name LIKE ? 
               OR actor_3_name LIKE ?
            ORDER BY gross DESC
        `;
        const pattern = `%${person_name}%`;
        db.query(sql, [pattern, pattern, pattern, pattern, pattern, pattern, pattern, pattern], (err, results) => {
            if (err) reject(err);
            else resolve(results);
        });
    });
}
//票房排名查询电影信息
async function queryMovieByRank(rank) {
    return new Promise((resolve, reject) => {
        const sql = 'SELECT * FROM movies WHERE gross IS NOT NULL ORDER BY gross DESC LIMIT 1 OFFSET ?';
        db.query(sql, [rank - 1], (err, results) => {
            if (err) reject(err);
            else resolve(results);
        });
    });
}

// 处理用户请求
app.post('/api/ai/stream', async (req, res) => {
            const { message, sessionId } = req.body;
            
            // ==================== 参数验证 ====================
            if (!message) {
                return res.send({ code: 400, msg: '消息内容不能为空' });
            }

            // ==================== 设置响应头 ====================
            res.setHeader('Content-Type', 'text/event-stream');
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('Connection', 'keep-alive');
    
            // ==================== 准备阶段 ====================
            
            // 获取或创建对话历史
            let history = conversationHistory.get(sessionId) || [];

            try {
                // 构建系统提示词
                const systemPrompt = `你是一个电影数据分析系统的管理员，负责处理用户的查询请求以及管理员的后台修改操作。

                    你可以使用以下工具查询电影数据：
                    1. query_movie_by_title - 根据电影名称查询电影详细信息
                    2. query_person_by_name - 根据演员或导演姓名查询其参与的电影
                    3. query_movie_by_rank - 根据票房排名查询电影信息（1表示票房最高）

                    当用户询问电影相关数据时，使用相应的工具查询数据库，然后用自然语言回复用户。

                    电影信息输出格式示例：
                    根据查询结果，《侏罗纪世界》的详细信息：

                    年份：2015
                    导演：Colin Trevorrow
                    主演：Bryce Dallas Howard、Judy Greer、Omar Sy
                    片长：124分钟
                    语言：英语
                    国家：美国
                    分级：PG-13

                    预算：1.5亿美元
                    票房：6.52亿美元

                    评分：7.0/10
                    影评人数：644人
                    用户评分：418214人

                    类型：动作、冒险、科幻、惊悚
                    关键词：恐龙、灾难片、实验失控、侏罗纪公园、迅猛龙

                    演员信息输出格式示例：
                    根据查询结果，Ryan Reynolds的主要作品：

                    死侍 | 2016年 | 3.63亿美元 | 8.1分 | 主演
                    疯狂原始人 | 2013年 | 1.87亿美元 | 7.3分 | 主演
                    X战警前传：金刚狼 | 2009年 | 1.80亿美元 | 6.7分 | 主演`;

            // 构建消息数组（包含历史记录）
            const messages = [
                { role: 'system', content: systemPrompt },
                ...history,//展开历史记录数组，每个元素都是一个对象，包含role和content
                { role: 'user', content: message }
            ];

            // ==================== 第一次API调用 ====================
            
            const completion = await openai.chat.completions.create({
                model: 'deepseek-chat',
                messages: messages,
                tools: tools,
                tool_choice: 'auto',
                stream: true // 启用流式传输
            });

            // ==================== 初始化变量 ====================
            
            // 创建助手消息对象，用于存储AI的完整回复
            // - role: 'assistant' - 标识这是AI助手的消息（OpenAI API要求）
            // - content: '' - 初始内容为空，后续会累积文本回复
            // - tool_calls: null - 初始没有工具调用，后续如果有工具调用会赋值
            const assistantMessage = { role: 'assistant', content: '', tool_calls: null };
            
            // 累积AI生成的完整文本内容
            let fullContent = '';
            
            // 存储工具调用信息，用Map是因为可能有多个工具调用
            const toolCallsMap = new Map();
            
            // ==================== 流式处理循环 ====================
                
                for await (const chunk of completion) {//遍历流式数据，异步迭代每个chunk
                    const delta = chunk.choices[0]?.delta;//获取数据增量
                    
                    // 处理文本内容
                    if (delta?.content) {
                        fullContent += delta.content;
                        assistantMessage.content = fullContent;
                        
                        // 流式发送内容到前端
                        res.write(`data: ${JSON.stringify({ content: delta.content })}\n\n`);
                    }
                    
                    // 处理工具调用
                    if (delta?.tool_calls) {
                        for (const toolCall of delta.tool_calls) {
                            const index = toolCall.index;
                            
                            // 首次遇到该index，创建新的工具调用对象
                            if (!toolCallsMap.has(index)) {
                                toolCallsMap.set(index, {
                                    id: toolCall.id,
                                    type: toolCall.type,
                                    function: {
                                        name: toolCall.function?.name || '',
                                        arguments: toolCall.function?.arguments || ''
                                    }
                                });
                            } else {
                                // 后续遇到该index，追加内容
                                const existing = toolCallsMap.get(index);
                                if (toolCall.function?.name) {
                                    existing.function.name = toolCall.function.name;
                                }
                                if (toolCall.function?.arguments) {
                                    existing.function.arguments += toolCall.function.arguments;
                                }
                            }
                        }
                        // 将Map转为数组，存储到消息对象中
                        assistantMessage.tool_calls = Array.from(toolCallsMap.values());
                    }
                }

                // ==================== 处理工具调用 ====================
                
                if (assistantMessage.tool_calls) {
                    const toolCalls = assistantMessage.tool_calls;
                    const toolResponses = [];

                    // 逐个执行工具调用
                    for (const toolCall of toolCalls) {
                        const functionName = toolCall.function.name;
                        const functionArgs = JSON.parse(toolCall.function.arguments);
                        
                        let result;
                        // 根据工具名称调用对应的数据库函数
                        if (functionName === 'query_movie_by_title') {
                            result = await queryMovieByTitle(functionArgs.movie_title);
                        } else if (functionName === 'query_person_by_name') {
                            result = await queryPersonByName(functionArgs.person_name);
                        } else if (functionName === 'query_movie_by_rank') {
                            result = await queryMovieByRank(functionArgs.rank);
                        }

                        // 收集工具执行结果
                        toolResponses.push({
                            tool_call_id: toolCall.id,
                            role: 'tool',
                            content: JSON.stringify(result)
                        });
                    }

                    // ==================== 第二次API调用 ====================
                    
                    // 将工具执行结果发送给AI，生成最终回复
                    const secondCompletion = await openai.chat.completions.create({
                        model: 'deepseek-chat',
                        messages: [
                            {
                                role: 'system',
                                content: '你是一个专业的电影数据分析助手，可以查询数据库获取电影信息。当用户询问电影相关数据时，使用提供的工具查询数据库，然后用自然语言回复用户。'
                            },
                            {
                                role: 'user',
                                content: message
                            },
                            assistantMessage,
                            ...toolResponses
                        ],
                        stream: true
                    });

                    // 流式处理第二次API的响应
                    let secondContent = '';
                    for await (const chunk of secondCompletion) {
                        const delta = chunk.choices[0]?.delta;
                        if (delta?.content) {
                            secondContent += delta.content;
                            res.write(`data: ${JSON.stringify({ content: delta.content })}\n\n`);
                        }
                    }
                    
                    // 更新最终内容
                    fullContent = secondContent;
                }
                // ==================== 保存对话历史 ====================
                
                // 发送结束标记
                res.write(`data: [DONE]\n\n`);
                
                // 保存用户消息到历史
                history.push({ role: 'user', content: message });
                
                // 保存AI回复到历史
                history.push({ role: 'assistant', content: fullContent });
                
                // 限制历史长度（保留最近10轮对话）
                if (history.length > MAX_HISTORY_LENGTH * 2) {
                    history = history.slice(-MAX_HISTORY_LENGTH * 2);
                }
                
                // 保存回全局Map
                conversationHistory.set(sessionId, history);
                res.end();
                
            } catch (error) {
        // ==================== 错误处理 ====================
        
        console.error('DeepSeek API调用失败:', error); 
        
        if (error.status === 401) {
            res.write(`data: ${JSON.stringify({ error: 'API密钥无效，请检查配置' })}\n\n`);
        } else if (error.status === 429) {
            res.write(`data: ${JSON.stringify({ error: '请求过于频繁，请稍后重试' })}\n\n`);
        } else if (error.code === 'ECONNABORTED' || error.code === 'timeout') {
            res.write(`data: ${JSON.stringify({ error: '请求超时，请稍后重试' })}\n\n`);
        } else {
            res.write(`data: ${JSON.stringify({ error: 'AI服务暂时不可用，请稍后重试' })}\n\n`);
        }
        res.end();
    }
});

// 管理员工具
const adminTools = [
    {
        type: 'function',
        function: {
            name: 'create_user',
            description: '创建新用户，如果用户名已存在会返回错误',
            parameters: {
                type: 'object',
                properties: {
                    username: {
                        type: 'string',
                        description: '用户名'
                    },
                    password: {
                        type: 'string',
                        description: '密码'
                    },
                    role: {
                        type: 'string',
                        description: '角色，可选值：user(普通用户)、admin(管理员)，默认为user'
                    }
                },
                required: ['username', 'password']
            }
        }
    },
    {
        type: 'function',
        function: {
            name: 'delete_user',
            description: '删除用户，可以通过用户ID或用户名删除',
            parameters: {
                type: 'object',
                properties: {
                    user_id: {
                        type: 'string',
                        description: '用户ID（优先使用）'
                    },
                    username: {
                        type: 'string',
                        description: '用户名（如果没有user_id则使用用户名查询后删除）'
                    }
                }
            }
        }
    },
    {
        type: 'function',
        function: {
            name: 'update_user_role',
            description: '修改用户角色，可以通过用户ID或用户名修改',
            parameters: {
                type: 'object',
                properties: {
                    user_id: {
                        type: 'string',
                        description: '用户ID（优先使用）'
                    },
                    username: {
                        type: 'string',
                        description: '用户名（如果没有user_id则使用用户名查询后修改）'
                    },
                    role: {
                        type: 'string',
                        description: '新角色，可选值：user、admin'
                    }
                },
                required: ['role']
            }
        }
    },
    {
        type: 'function',
        function: {
            name: 'query_user_by_username',
            description: '根据用户名查询用户信息，返回用户ID等信息',
            parameters: {
                type: 'object',
                properties: {
                    username: {
                        type: 'string',
                        description: '用户名'
                    }
                },
                required: ['username']
            }
        }
    },
];

// 执行管理员工具
async function executeAdminTool(functionName, args) {
    return new Promise(async (resolve, reject) => {
        try {
            let result;
            
            switch (functionName) {
                case 'create_user':
                    result = await new Promise((res, rej) => {
                        const checkSql = 'SELECT * FROM users WHERE username = ?';
                        db.query(checkSql, [args.username], (err, results) => {
                            if (err) return rej(err);
                            if (results.length > 0) return res({ success: false, error: '用户名已存在' });
                            
                            // 对密码进行加密处理
                            const hashedPassword = bcrypt.hashSync(args.password, 10);
                            
                            const insertSql = 'INSERT INTO users (username, password, role) VALUES (?, ?, ?)';
                            db.query(insertSql, [args.username, hashedPassword, args.role || 'user'], (err, result) => {
                                if (err) return rej(err);
                                res({ success: true, user_id: result.insertId, username: args.username });
                            });
                        });
                    });
                    break;
                    
                case 'delete_user':
                    result = await new Promise((res, rej) => {
                        // 第一步：用 username 查出 id
                        const querySql = 'SELECT id, username FROM users WHERE username = ?';
                        db.query(querySql, [args.username], (err, results) => {
                            if (err) return rej(err);
                            if (results.length === 0) {
                                return res({ success: false, error: `用户 "${args.username}" 不存在` });
                            }

                            // 第二步：拿到 id，执行删除
                            const userId = results[0].id;
                            db.query('DELETE FROM users WHERE id = ?', [userId], (err, result) => {
                                if (err) return rej(err);
                                if (result.affectedRows === 0) {
                                    return res({ success: false, error: '用户不存在或已被删除' });
                                }
                                res({ success: true, user_id: userId, username: args.username });
                            });
                        });
                    });
                    break;   
                
                case 'update_user_role':
                    result = await new Promise((res, rej) => {
                        // 第一步：用 username 查出 id
                        const querySql = 'SELECT id FROM users WHERE username = ?';
                        db.query(querySql, [args.username], (err, results) => {
                            if (err) return rej(err);
                            if (results.length === 0) {
                                return res({ success: false, error: `用户 "${args.username}" 不存在` });
                            }
                
                            // 第二步：拿到 id，执行更新
                            const userId = results[0].id;
                            db.query('UPDATE users SET role = ? WHERE id = ?', [args.role, userId], (err, result) => {
                                if (err) return rej(err);
                                if (result.affectedRows === 0) {
                                    return res({ success: false, error: '用户不存在' });
                                }
                                res({ success: true, user_id: userId, username: args.username, role: args.role });
                            });
                        });
                    });
                    break;
                    
                case 'query_user_by_username':
                    result = await new Promise((res, rej) => {
                        const sql = 'SELECT id, username, role, create_time FROM users WHERE username = ?';
                        db.query(sql, [args.username], (err, results) => {
                            if (err) return rej(err);
                            if (results.length === 0) return res({ success: false, error: '用户不存在' });
                            res({ success: true, user: results[0] });
                        });
                    });
                    break;
                    
                default:
                    result = { success: false, error: '未知工具' };
            }
            resolve(result);
        } catch (err) {
            reject(err);
        }
    });
}

// 管理员AI接口 - 解析复杂指令（流式传输）
app.post('/api/admin/ai/stream', async (req, res) => {
    const { message, sessionId } = req.body;
    
    if (!message) {
        return res.send({ code: 400, msg: '消息内容不能为空' });
    }
    
    // 设置SSE响应头
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    // 获取对话历史（管理员模式只保留最近2轮对话，避免干扰）
    let history = conversationHistory.get(sessionId) || [];
    history = history.slice(-4); // 只保留最近2轮（user+assistant各2条）
    
    const adminSystemPrompt = `你是电影数据系统的管理员助手，专门处理复杂的管理指令。

【核心规则 - 必须严格遵守】
1. 用户输入可能包含多个操作指令，你必须识别并执行所有操作
2. 每个操作都要调用对应的工具函数
3. 按指令顺序依次调用所有工具
4. 不要遗漏任何操作！
5. 如果用户输入包含多个操作，必须一次性返回所有工具调用
6. 识别操作时要注意不同的分隔符：逗号、分号、句号、顿号等

【可用工具】
1. create_user - 创建新用户（参数：username, password, role）
2. delete_user - 删除用户（参数：user_id 或 username，可以直接使用用户名删除）
3. update_user_role - 修改用户角色（参数：user_id 或 username + role，可以直接使用用户名修改）
4. query_user_by_username - 根据用户名查询用户（参数：username）

【操作识别规则】
- "新增"、"添加"、"创建" → create_user
- "删除"、"移除" → delete_user  
- "修改"、"更改"、"设置"、"为"、"权限" → update_user_role
- "查询"、"查看"、"搜索"、"找" → query_user_by_username 或 query_all_users
- 如果有具体用户名 → query_user_by_username

【复合指令示例】
用户："新增用户test1密码123，删除用户test2，修改test3为admin，查询test4"
→ 这是4个不同的操作，你必须同时调用4个工具：
   工具1: create_user({"username": "test1", "password": "123"})
   工具2: delete_user({"username": "test2"})
   工具3: update_user_role({"username": "test3", "role": "admin"})
   工具4: query_user_by_username({"username": "test4"})`;

    try {
        let toolCalls = [];
        let usedAI = false;
        
        // 先使用AI解析指令（体现AI功能）
        console.log('[管理员AI] 使用AI解析指令...');
        
        // 构建消息数组
        const messages = [
            { role: 'system', content: adminSystemPrompt },
            ...history,
            { role: 'user', content: message }
        ];
        
        // 调用AI，获取工具调用列表
        const completion = await openai.chat.completions.create({
            model: 'deepseek-chat',
            messages: messages,
            tools: adminTools,
            tool_choice: 'auto'
        });
        
        const assistantMessage = completion.choices[0].message;
        
        // 如果AI没有调用工具，直接返回回复
        if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
            const reply = assistantMessage.content;
            
            // 流式发送回复
            for (let i = 0; i < reply.length; i += 10) {
                const chunk = reply.slice(i, i + 10);
                res.write(`data: ${JSON.stringify({ content: chunk })}\n\n`);
                await new Promise(resolve => setTimeout(resolve, 20));
            }
            res.write(`data: [DONE]\n\n`);
            
            // 保存对话历史
            history.push({ role: 'user', content: message });
            history.push({ role: 'assistant', content: reply });
            if (history.length > MAX_HISTORY_LENGTH * 2) {
                history = history.slice(-MAX_HISTORY_LENGTH * 2);
            }
            conversationHistory.set(sessionId, history);
            
            return res.end();
        }
        
        toolCalls = assistantMessage.tool_calls;
        usedAI = true;
        
        console.log(`[管理员AI] AI识别了 ${toolCalls.length} 个操作`);
        
        // 执行所有工具调用
        const toolResponses = [];
        
        console.log(`[管理员AI] 共 ${toolCalls.length} 个工具调用:`);
        toolCalls.forEach((tc, i) => {
            console.log(`  [${i+1}] ${tc.function.name}: ${tc.function.arguments}`);
        });
        
        for (let i = 0; i < toolCalls.length; i++) {
            const toolCall = toolCalls[i];
            const functionName = toolCall.function.name;
            const functionArgs = JSON.parse(toolCall.function.arguments);
            
            console.log(`\n========== 执行工具 [${i+1}/${toolCalls.length}]: ${functionName} ==========`);
            console.log(`参数:`, functionArgs);
            
            try {
                const result = await executeAdminTool(functionName, functionArgs);
                console.log(`结果:`, result);
                console.log(`========== 工具执行完成 ==========\n`);
                toolResponses.push({
                    tool_call_id: toolCall.id,
                    role: 'tool',
                    content: JSON.stringify(result)
                });
            } catch (err) {
                console.error(`工具执行失败 ${functionName}:`, err);
                toolResponses.push({
                    tool_call_id: toolCall.id,
                    role: 'tool',
                    content: JSON.stringify({ success: false, error: err.message })
                });
            }
        }
        
        // 直接根据工具执行结果生成回复（不再调用AI，避免DeepSeek返回工具调用格式）
        let reply = '操作执行结果：\n\n';
        
        for (let i = 0; i < toolCalls.length; i++) {
            const toolCall = toolCalls[i];
            const functionName = toolCall.function.name;
            const functionArgs = JSON.parse(toolCall.function.arguments);
            const toolResponse = toolResponses[i];
            
            try {
                const result = JSON.parse(toolResponse.content);
                
                // 根据工具类型生成友好的回复
                switch (functionName) {
                    case 'create_user':
                        if (result.success) {
                            reply += `✅ 创建用户成功：${result.username}（ID: ${result.user_id}）\n`;
                        } else {
                            reply += `❌ 创建用户失败：${result.error}\n`;
                        }
                        break;
                    case 'delete_user':
                        if (result.success) {
                            if (result.username) {
                                reply += `✅ 删除用户成功：${result.username}（ID: ${result.user_id}）\n`;
                            } else {
                                reply += `✅ 删除用户成功（ID: ${result.user_id}）\n`;
                            }
                        } else {
                            reply += `❌ 删除用户失败：${result.error}\n`;
                        }
                        break;
                    case 'update_user_role':
                        if (result.success) {
                            if (result.username) {
                                reply += `✅ 修改用户角色成功：${result.username}（ID: ${result.user_id}）→ ${result.role}\n`;
                            } else {
                                reply += `✅ 修改用户角色成功（ID: ${result.user_id}）→ ${result.role}\n`;
                            }
                        } else {
                            reply += `❌ 修改用户角色失败：${result.error}\n`;
                        }
                        break;
                    case 'query_user_by_username':
                        if (result.success) {
                            reply += `📋 查询到用户：${result.user.username}（ID: ${result.user.id}, 角色: ${result.user.role}）\n`;
                        } else {
                            reply += `❌ 查询用户失败：${result.error}\n`;
                        }
                        break;
                    default:
                        reply += `📝 ${functionName}: ${result.success ? '成功' : '失败'}\n`;
                }
            } catch (e) {
                reply += `⚠️ 操作执行异常\n`;
            }
        }
        
        console.log('生成的回复:', reply);
        
        // 流式发送回复
        for (let i = 0; i < reply.length; i += 10) {
            const chunk = reply.slice(i, i + 10);
            res.write(`data: ${JSON.stringify({ content: chunk })}\n\n`);
            await new Promise(resolve => setTimeout(resolve, 20));
        }
        res.write(`data: [DONE]\n\n`);
        
        // 保存对话历史
        history.push({ role: 'user', content: message });
        history.push({ role: 'assistant', content: reply });
        if (history.length > MAX_HISTORY_LENGTH * 2) {
            history = history.slice(-MAX_HISTORY_LENGTH * 2);
        }
        conversationHistory.set(sessionId, history);
        
        res.end();
        
    } catch (error) {
        console.error('管理员AI接口调用失败:', error);
        res.write(`data: ${JSON.stringify({ error: 'AI服务暂时不可用，请稍后重试' })}\n\n`);
        res.end();
    }
});

// 3. 启动监听
app.listen(3000, () => {
    console.log('--------------------------------------');
    console.log('后端启动成功');
    console.log('--------------------------------------');
});

