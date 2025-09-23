@echo off
echo ==========================================
echo     ДЕПЛОЙ НА СЕРВЕР coworking.greatideas.ru
echo ==========================================
echo.

echo 📤 Отправляем код на GitHub...
git add .
set /p commit_msg="Введите описание изменений: "
git commit -m "%commit_msg%"
git push origin main

echo.
echo 🚀 Запускаем деплой на сервере...
ssh root@89.110.123.93 "/var/www/deploy.sh"

echo.
echo ✅ Деплой завершен!
echo 🌐 Проверьте сайт: http://coworking.greatideas.ru
echo.
pause