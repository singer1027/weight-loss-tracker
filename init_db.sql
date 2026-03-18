-- 减肥打卡系统数据库初始化脚本
-- 执行方式: mysql -u root -p < init_db.sql

CREATE DATABASE IF NOT EXISTS weight_loss_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE weight_loss_db;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL        COMMENT '密码哈希',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) COMMENT='用户表';

-- 打卡记录表
CREATE TABLE IF NOT EXISTS records (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL                          COMMENT '用户ID',
    day        TINYINT NOT NULL                      COMMENT '第几天(1-30)',
    weight     DECIMAL(5,1)                          COMMENT '体重(斤)',
    waist      DECIMAL(5,1)                          COMMENT '腰围(cm)',
    thigh      DECIMAL(5,1)                          COMMENT '大腿围(cm)',
    sport      VARCHAR(100)                          COMMENT '运动模式',
    done       TINYINT(1) DEFAULT 0                  COMMENT '是否完成',
    lunch      VARCHAR(500)                          COMMENT '午餐',
    snack      VARCHAR(500)                          COMMENT '下午加餐',
    dinner     VARCHAR(500)                          COMMENT '晚餐',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP         COMMENT '最后更新时间',
    CONSTRAINT fk_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_day CHECK (day >= 1 AND day <= 30),
    UNIQUE KEY uq_user_day (user_id, day)
) COMMENT='打卡记录表';
