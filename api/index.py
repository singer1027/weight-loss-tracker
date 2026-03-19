import sys
import os

# 将项目根目录加入 Python 路径，使 app.py 可被正常导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

# Vercel Python 运行时通过 handler 变量识别 WSGI 入口
handler = app
