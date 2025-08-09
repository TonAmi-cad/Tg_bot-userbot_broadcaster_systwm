@echo off
:: Устанавливаем русскую кодировку
chcp 65001 >nul

:: Цвета для вывода
echo.
echo ===============================================
echo           BROADCASTER - ЗАПУСК ПРОЕКТА
echo ===============================================
echo.

:: Проверяем наличие conda окружения
echo [1/3] Проверяю conda окружение TG_WS...
if not exist "D:\0_filesys\1_program\Anaconda\envs\TG_WS" (
    echo ОШИБКА: Окружение TG_WS не найдено!
    echo Сначала запустите setup.bat для первоначальной настройки
    echo.
    pause
    exit /b 1
)
echo ✓ Окружение TG_WS найдено

:: Проверяем наличие .env файла
echo.
echo [2/3] Проверяю конфигурацию...
if not exist "..\.env" (
    if exist "..\..\.env copy" (
        echo ВНИМАНИЕ: Найден файл ".env copy"
        echo Переименуйте его в ".env" и настройте перед запуском
    ) else (
        echo ОШИБКА: Файл .env не найден в корне проекта!
        echo Создайте и настройте файл .env
    )
    echo.
    pause
    exit /b 1
)
echo ✓ Файл конфигурации найден

:: Активируем conda окружение
echo.
echo [3/3] Запускаю проект...
echo Активирую conda окружение TG_WS...
call "D:\0_filesys\1_program\Anaconda\Scripts\activate.bat" "D:\0_filesys\1_program\Anaconda\envs\TG_WS"

if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось активировать окружение TG_WS
    echo.
    pause
    exit /b 1
)

echo ✓ Окружение активировано

:: Переходим в директорию src (где находится main.py и session файлы)
cd /d "%~dp0"

echo.
echo Запускаю Broadcaster...
echo Для остановки нажмите Ctrl+C
echo.
echo ===============================================

:: Запускаем main.py
python main.py

:: Если произошла ошибка, показываем её
if %errorlevel% neq 0 (
    echo.
    echo ===============================================
    echo ОШИБКА ВЫПОЛНЕНИЯ!
    echo Код ошибки: %errorlevel%
    echo ===============================================
    echo.
    echo Возможные причины:
    echo - PostgreSQL не запущен
    echo - Неверная конфигурация в .env
    echo - Отсутствуют session файлы юзерботов
    echo - Проблемы с сетью/API Telegram
    echo.
)

:: Не закрываем окно для просмотра ошибок/логов
echo.
echo ===============================================
echo Программа завершена. Для закрытия окна нажмите любую клавишу...
pause >nul
