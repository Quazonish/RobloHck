@echo off
pyinstaller --noconfirm --onedir --console --icon "bruh.ico" --optimize "2" ".\Main program\main(RUN ME).py"
WinRAR a -afzip -m5 -r -ep1 -o+ "external.zip" ".\dist\main(RUN ME)\"
pause