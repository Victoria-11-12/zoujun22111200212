-- ========================================
-- MySQL 数据库用户初始化脚本
-- 首次启动容器时自动执行
-- ========================================

-- 只读用户（仅 movies 表）
CREATE USER IF NOT EXISTS 'readonly_user'@'%' IDENTIFIED BY '123456';
GRANT SELECT ON movie_db.movies TO 'readonly_user'@'%';

-- 分析师用户
CREATE USER IF NOT EXISTS 'analyst'@'%' IDENTIFIED BY '123456';
GRANT SELECT ON movie_db.admin_chat_logs TO 'analyst'@'%';
GRANT SELECT ON movie_db.chart_generation_logs TO 'analyst'@'%';
GRANT SELECT, INSERT ON movie_db.eval_results TO 'analyst'@'%';
GRANT SELECT ON movie_db.security_warning_logs TO 'analyst'@'%';
GRANT SELECT ON movie_db.user_chat_logs TO 'analyst'@'%';

FLUSH PRIVILEGES;
