@echo off
title Проверка DNS для coworking.greatideas.ru
echo ==========================================
echo     ПРОВЕРКА DNS ЗАПИСЕЙ
echo ==========================================
echo.

:loop
echo [%date% %time%] Проверяем DNS...

echo.
echo 🔍 Проверка через nslookup:
nslookup coworking.greatideas.ru

echo.
echo 🌐 Проверка через Google DNS (8.8.8.8):
nslookup coworking.greatideas.ru 8.8.8.8

echo.
echo 🌍 Проверка через Cloudflare DNS (1.1.1.1):
nslookup coworking.greatideas.ru 1.1.1.1

echo.
echo ==========================================
echo 📋 Статус:
ping -n 1 coworking.greatideas.ru > nul 2>&1
if %errorlevel% == 0 (
    echo ✅ DNS работает! Сайт доступен.
    echo 🌐 Проверьте в браузере: http://coworking.greatideas.ru
    pause
    exit
) else (
    echo ❌ DNS еще не обновился
    echo ⏳ Ждем 60 секунд и проверяем снова...
)

echo.
timeout /t 60 /nobreak
goto loop