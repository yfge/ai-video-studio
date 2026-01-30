@echo off
REM 测试运行批处理脚本
REM 使用方法: run_tests.bat [command]

if "%1"=="" (
    echo 使用方法:
    echo     run_tests.bat all          # 运行所有测试
    echo     run_tests.bat unit         # 只运行单元测试
    echo     run_tests.bat integration  # 只运行集成测试
    echo     run_tests.bat migration    # 只运行迁移测试
    echo     run_tests.bat api          # 只运行API测试
    echo     run_tests.bat model        # 只运行模型测试
    echo     run_tests.bat coverage     # 运行测试并生成覆盖率报告
    echo     run_tests.bat quick        # 快速测试（跳过慢速测试）
    echo     run_tests.bat parallel     # 并行运行测试
    echo     run_tests.bat lint         # 代码质量检查
    echo     run_tests.bat clean        # 清理测试产物
    goto :eof
)

REM 激活虚拟环境并运行Python脚本
call .venv\Scripts\activate.bat
python run_tests.py %1 %2 %3 %4 %5
if errorlevel 1 (
    echo 测试执行失败
    pause
    exit /b 1
)

echo 测试执行完成
pause
