@echo off
echo Compiling driveless version(detected)
pyinstaller --noconfirm --onedir --console --icon "bruh.ico" --optimize "2" ".\Main program\driveless version(detected)\main(RUN ME).py"
echo Compiling radar
pyinstaller --noconfirm --onedir --console --optimize "2" ".\Main program\driveless version(detected)\radar.py"
move ".\dist\radar\radar.exe" ".\dist\main(RUN ME)\_internal"
move ".\dist\radar\_internal" ".\dist\main(RUN ME)\_internal"
WinRAR a -afzip -m5 -r -ep1 -o+ "externalDriveless(detected).zip" ".\dist\main(RUN ME)\"

echo Compiling with driver version(undetected)
pyinstaller --noconfirm --onedir --console --icon "bruh.ico" --optimize "2" --uac-admin ".\Main program\with driver version(undetected)\main program\RobloxDriva(RUN ME).py"
echo Compiling radar
pyinstaller --noconfirm --onedir --console --optimize "2" ".\Main program\with driver version(undetected)\main program\radar.py"
move ".\dist\radar\radar.exe" ".\dist\RobloxDriva(RUN ME)\_internal"
move ".\dist\radar\_internal" ".\dist\RobloxDriva(RUN ME)\_internal"
copy ".\Main program\with driver version(undetected)\driver" ".\dist\RobloxDriva(RUN ME)\"
move ".\dist\RobloxDriva(RUN ME)\drag me into kdmapper.sys " ".\dist\RobloxDriva(RUN ME)\drag me into kdmapper BEFORE running main exe file.sys"
WinRAR a -afzip -m5 -r -ep1 -o+ "externalWithDriver(undetected).zip" ".\dist\RobloxDriva(RUN ME)\"
pause