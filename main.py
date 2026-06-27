"""兼容需要 main.py 作为启动入口的平台。"""
import os

from game_api import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
