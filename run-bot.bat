@echo off
setlocal

:: ======================================================
:: 【設定】ご自身の環境に合わせてパスを書き換えてください
:: ======================================================

:: Stable Diffusion WebUI (automatic1111) のフォルダパス
set "SD_PATH=C:\path\to\your\stable-diffusion-webui"

:: このBotがインストールされているフォルダパス
:: (%~dp0 はこのバッチファイルがあるフォルダを自動取得します)
set "BOT_PATH=%~dp0"

:: ======================================================

echo --- Stable Diffusion (4070) を起動中 ---
:: WebUIを別ウィンドウで起動
start cmd /k "cd /d %SD_PATH% && webui-user.bat"

echo --- 25秒待機 (WebUIが完全に立ち上がるのを待ちます) ---
:: SDの起動には時間がかかるため待機
timeout /t 25

echo --- Discord Bot を起動中 (専用環境 venv_bot 使用) ---
:: 仮想環境を有効化してBotを実行
start cmd /k "cd /d %BOT_PATH% && venv_bot\Scripts\activate && python image_gen_bot.py"

echo --- すべての起動指示が完了しました！ ---
echo SD WebUIとDiscord Botのウィンドウがそれぞれ開きます。
pause