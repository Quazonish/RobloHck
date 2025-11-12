@echo off
echo Compiling driveless version(detected)
pyinstaller --noconfirm --onedir --console --icon "bruh.ico" --optimize "2" ".\Main program\driveless version(detected)\main_RUN_ME.py"
echo Compiling radar
pyinstaller --noconfirm --onedir --console --optimize "2" ".\Main program\driveless version(detected)\radar.py"
echo Compiling ESP
pyinstaller --noconfirm --onedir --console --optimize "2" ".\Main program\driveless version(detected)\esp.py"
robocopy ".\dist\radar" ".\dist\main_RUN_ME" /MOVE /E /XC /XN /XO
robocopy ".\dist\esp" ".\dist\main_RUN_ME" /MOVE /E /XC /XN /XO
xcopy assets ".\dist\main_RUN_ME\assets" /E /I /Y
"C:\Program Files\WinRAR\WinRAR.exe" a -afzip -m5 -r -ep1 -o+ "externalDriveless(detected).zip" ".\dist\main_RUN_ME\"

echo Compiling with driver version(undetected)
pyinstaller --noconfirm --onedir --console --icon "bruh.ico" --optimize "2" --uac-admin ".\Main program\with driver version(undetected)\main program\RobloxDriva_RUN_ME.py"
echo Compiling radar
pyinstaller --noconfirm --onedir --console --optimize "2" ".\Main program\with driver version(undetected)\main program\radar.py"
echo Compiling ESP
pyinstaller --noconfirm --onedir --console --optimize "2" ".\Main program\with driver version(undetected)\main program\esp.py"
robocopy ".\dist\radar" ".\dist\RobloxDriva_RUN_ME" /MOVE /E /XC /XN /XO
robocopy ".\dist\esp" ".\dist\RobloxDriva_RUN_ME" /MOVE /E /XC /XN /XO
copy ".\Main program\with driver version(undetected)\driver" ".\dist\RobloxDriva_RUN_ME\"
move ".\dist\RobloxDriva_RUN_ME\drag me into kdmapper.sys " ".\dist\RobloxDriva_RUN_ME\drag me into kdmapper BEFORE running main exe file.sys"
xcopy assets ".\dist\RobloxDriva_RUN_ME\assets" /E /I /Y
"C:\Program Files\WinRAR\WinRAR.exe" a -afzip -m5 -r -ep1 -o+ "externalWithDriver(undetected).zip" ".\dist\RobloxDriva_RUN_ME\"
pause