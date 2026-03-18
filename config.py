import os

# 优先读取环境变量（Vercel 部署时设置），本地开发时使用默认值
DB_HOST     = os.environ.get('DB_HOST',     'localhost')
DB_PORT     = int(os.environ.get('DB_PORT', '3306'))
DB_USER     = os.environ.get('DB_USER',     'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root123')
DB_NAME     = os.environ.get('DB_NAME',     'weight_loss_db')
SECRET_KEY  = os.environ.get('SECRET_KEY',  'change-this-to-a-random-secret-key')
# TiDB Cloud Serverless 需要 SSL，设为 true 开启
DB_SSL      = os.environ.get('DB_SSL', 'false').lower() == 'true'
