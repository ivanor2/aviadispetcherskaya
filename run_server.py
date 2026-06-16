# run_server.py
import uvicorn
import os
import sys

# Добавляем текущую директорию в путь, чтобы импорты работали корректно после упаковки
if getattr(sys, 'frozen', False):
    # Если запущено как скомпилированный exe
    application_path = sys._MEIPASS
else:
    # Если запущено как обычный скрипт
    application_path = os.path.dirname(os.path.abspath(__ini__file__))

sys.path.insert(0, application_path)

from app.main import app

if __name__ == "__main__":
    print("🚀 Запуск Airport Dispatcher API на порту 8001...")
    # host="0.0.0.0" позволяет принимать подключения извне (если нужно)
    # port=8001 - требуемый порт
    uvicorn.run(app, port=8001, log_level="info")