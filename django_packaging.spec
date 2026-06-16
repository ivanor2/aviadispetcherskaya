# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# 1. Собираем скрытые импорты, которые PyInstaller не может найти автоматически
hidden_imports = [
    'django_app',
    'django_app.settings',
    'django_app.urls',
    'django_app.wsgi',
    'django_app.asgi',
    'app',
    'app.middleware',
    'app.context_processors',
    'reportlab',
    'reportlab.pdfbase.ttfonts',
    'reportlab.lib.styles',
    'reportlab.platypus',
    'decouple',
]

# 2. Автоматически находим ВСЕ подмодули внутри папок app и django_app
# Это критически важно для Django, так как он часто импортирует вещи динамически
hidden_imports += collect_submodules('app')
hidden_imports += collect_submodules('django_app')

a = Analysis(
    ['run_server.py'],  # Точка входа теперь run_server.py, а не manage.py!
    pathex=[],
    binaries=[],
    datas=[
        # 3. Явно упаковываем папки app и django_app внутрь exe-файла
        # Формат: ('исходная_папка', 'папка_внутри_архива')
        ('app', 'app'),
        ('django_app', 'django_app'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Исключаем ненужные библиотеки, чтобы уменьшить размер exe
        'tkinter',
        'matplotlib',
        'pytest',
        'selenium',
        'tests',
        'django.contrib.postgres', # Если не используете специфичные фичи PG
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DjangoApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Сжатие исполняемого файла
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # ВАЖНО: Оставляем консоль, чтобы видеть логи Django и ошибки запуска
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app/assets/favicon.ico', # Раскомментируйте и укажите путь, если есть иконка
)