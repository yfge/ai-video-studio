@echo off
REM 数据库迁移管理批处理脚本
REM 使用方法: migrate.bat [command]

if "%1"=="" (
    echo 使用方法:
    echo     migrate.bat init          # 初始化迁移（仅第一次使用）
    echo     migrate.bat generate      # 生成新的迁移文件
    echo     migrate.bat upgrade       # 应用迁移到数据库
    echo     migrate.bat downgrade     # 回退迁移
    echo     migrate.bat current       # 查看当前迁移版本
    echo     migrate.bat history       # 查看迁移历史
    echo     migrate.bat reset         # 重置数据库（危险操作）
    goto :eof
)

REM 激活虚拟环境并运行 Python 脚本
call .venv\Scripts\activate.bat
python migrate.py %1
if errorlevel 1 (
    echo 命令执行失败
    pause
    exit /b 1
)

echo 命令执行完成
pause 