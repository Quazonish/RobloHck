from rbxMemory import *
from time import time, sleep
from threading import Thread
from gui import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
#from keyboard import on_release
from requests import get
from subprocess import Popen, PIPE
from os import path
import sys

hrpGravAddr = 0
humAddr = 0
hrpAddr = 0

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

camAddr = 0

def init():
    global dataModel, wsAddr, lightingAddr, camAddr, fovAddr, camLVAddr, startFogAddr, endFogAddr, plrsAddr, lpAddr
    pid = get_pid_by_name("RobloxPlayerBeta.exe")
    print(pid)
    openProcess(pid)
    radar.stdin.write(f'desc{pid}\n')
    radar.stdin.flush()
    baseAddr = get_module_base(pid)
    print(baseAddr)
    
    fakeDatamodel = read_int8(baseAddr + int(offsets['FakeDataModelPointer'], 16))
    print(f'Fake datamodel: {fakeDatamodel:x}')
    
    dataModel = read_int8(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
    print(f'Real datamodel: {dataModel:x}')
    
    wsAddr = read_int8(dataModel + int(offsets['Workspace'], 16)) #FindFirstChildOfClass(dataModel, 'Workspace')
    print(f'Workspace: {wsAddr:x}')
    
    camAddr = read_int8(wsAddr + int(offsets['Camera'], 16)) #FindFirstChildOfClass(wsAddr, 'Camera')
    fovAddr = camAddr + int(offsets['FOV'], 16)
    camLVAddr = read_int8(wsAddr + int(offsets['Camera'], 16)) + int(offsets['CameraRotation'], 16)

    print(f'Camera: {camAddr:x}')
    
    print('Pls wait while we getting other stuff...')
    lightingAddr = FindFirstChildOfClass(dataModel, 'Lighting')
    
    startFogAddr = lightingAddr + int(offsets['FogStart'], 16)
    endFogAddr = lightingAddr + int(offsets['FogEnd'], 16)
    print(f'Lighting service: {lightingAddr:x}')

    plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
    print(f'Players: {plrsAddr:x}')

    lpAddr = read_int8(plrsAddr + int(offsets['LocalPlayer'], 16))
    print(f'Local player: {plrsAddr:x}')

    radar.stdin.write(f'addrs{lpAddr},{camLVAddr},{plrsAddr}\n')
    radar.stdin.flush()
    
    print('Injected successfully\n-------------------------------')

'''def apply():
    global oldSpeed, oldJp#, oldEsp
    getHumAddr()

    if window.Jumppower.value() != oldJp:
        write_float(humAddr + int(offsets['JumpPower'], 16), float(window.Jumppower.value()))
        print('Wrote jump power')
        oldJp = window.Jumppower.value()
    
    if window.Speed.value() != oldSpeed:
        write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
        write_float(humAddr + int(offsets['WalkSpeed'], 16), float(window.Speed.value()))
        print('Wrote speed')
        oldSpeed = window.Speed.value()

    if window.ESP.isChecked() != oldEsp:
        if window.ESP.isChecked():
            print('ESP checked')
            #write_int4(humAddr + int(offsets['HealthDisplayDistance'], 16)+4, int(0)) #no fix for now
            write_float(humAddr + int(offsets['HealthDisplayDistance'], 16), float('inf'))
            write_float(humAddr + int(offsets['NameDisplayDistance'], 16), float('inf'))
        else:
            print('ESP not checked')
            #write_int4(humAddr + int(offsets['HealthDisplayDistance'], 16)+4, int(2)) #no fix for now
            write_float(humAddr + int(offsets['HealthDisplayDistance'], 16), float(100))
            write_float(humAddr + int(offsets['NameDisplayDistance'], 16), float(100))
        print('Wrote ESP')
        oldEsp = window.ESP.isChecked()'''
def speedChange(val):
    getHumAddr()
    write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
    write_float(humAddr + int(offsets['WalkSpeed'], 16), float(val))

def jpChange(val):
    getHumAddr()
    write_float(humAddr + int(offsets['JumpPower'], 16), float(val))

startTime = 0
def getHumAddr(changeTime=True):
    global humAddr, startTime
    if time()-startTime > 10:
        humAddr = read_int8(camAddr + int(offsets['CameraSubject'], 16)) #By default camera subject will be humanoid. Shortening path from game.Players.LocalPlayer.Character.Humanoid to workspace.CurrentCamera.CameraSubject
    if changeTime:
        startTime = time()

def getHrpAddr(changeTime=True):
    global hrpAddr, humAddr, startTime
    if time()-startTime > 10:
        humAddr = read_int8(camAddr + int(offsets['CameraSubject'], 16))
        char = read_int8(humAddr + int(offsets['Parent'], 16))
        hrpAddr = FindFirstChild(char, 'HumanoidRootPart')
    if changeTime:
        startTime = time()

def afterDeath():
    oldHumAddr = 0
    while camAddr == 0:
        sleep(1)

    while True:
        if window.AfterDeathApply.isChecked():
            hum = read_int8(camAddr + int(offsets['CameraSubject'], 16))
            if oldHumAddr != hum:
                write_float(hum + int(offsets['WalkSpeedCheck'], 16), float('inf'))
                write_float(hum + int(offsets['WalkSpeed'], 16), float(window.Speed.value()))
                print('Wrote speed')
                write_float(hum + int(offsets['JumpPower'], 16), float(window.Jumppower.value()))
                print('Wrote jump power')
                '''if window.ESP.isChecked() == 1:
                    #write_int4(hum + int(offsets['HealthDisplayDistance'], 16)+4, int(0)) #no fix for now
                    write_float(hum + int(offsets['HealthDisplayDistance'], 16), float('inf'))
                    write_float(hum + int(offsets['NameDisplayDistance'], 16), float('inf'))
                    print('Wrote ESP')'''
                oldHumAddr = hum
        sleep(1)
Thread(target=afterDeath, daemon=True).start()

def delFog():
    print('Removing fog...')
    ChildrenOfInstance = GetChildren(lightingAddr)
    print('Got children of lighting service!')
    for i in ChildrenOfInstance:
        try:
            if GetClassName(i) == 'Atmosphere':
                write_float(i+0xE0, float(0))
                write_float(i+0xE8, float(0))
                print('Wrote atmosphere')
        except:
            pass
    
    write_float(endFogAddr, float('inf'))
    write_float(startFogAddr, float('inf'))
    print('Fog removed')

'''def reEnableEspKeyBind(event):
    if event.name == 'right ctrl':
        if window.ESP.isChecked():
            getHumAddr()
            write_int4(humAddr+0x1B8, int(0))
            write_float(humAddr+0x1B4, float('inf'))
            write_float(humAddr+0x190, float('inf'))
            print('Wrote ESP')

def reEnableEsp():
    getHumAddr()
    write_int4(humAddr+0x1B8, int(0))
    write_float(humAddr+0x1B4, float('inf'))
    write_float(humAddr+0x190, float('inf'))
    print('Wrote ESP')'''

def fovChange(val):
    write_float(fovAddr, float(val))

def gravChange(val):
    getHrpAddr()
    write_float(read_int8(hrpAddr + int(offsets['Primitive'], 16)) + int(offsets['PrimitiveGravity'], 16), float(val))

def resetChr():
    getHumAddr()
    write_float(humAddr + int(offsets['Health'], 16), float(0))

'''def reEnableEspBtnToogle(state):
    if state == 2:
        window.ReEsp.show()
    elif state == 0:
        window.ReEsp.hide()'''

def toogleRadar():
    radar.stdin.write('toogle1\n')
    radar.stdin.flush()

def toogleIgnoreTeam():
    radar.stdin.write('toogle2\n')
    radar.stdin.flush()

def toogleIgnoreDead():
    radar.stdin.write('toogle3\n')
    radar.stdin.flush()

print('Loaded libs and stuff! Getting offsets...')
offsets = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json').json()
print('Supported versions:')
print(offsets['RobloxVersion'])
print(offsets['ByfronVersion'])
print('Current latest roblox version:', get('https://weao.xyz/api/versions/current', headers={'User-Agent': 'WEAO-3PService'}).json()['Windows'])
print('Got some offsets! Init...')
setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))

if hasattr(sys, '_MEIPASS'):
    radarPath = path.join(sys._MEIPASS, 'radar.exe')
else:
    radarPath = 'radar.py'

radar = Popen([
    radarPath,
    str(int(offsets['ModelInstance'], 16)),
    str(int(offsets['Primitive'], 16)),
    str(int(offsets['Position'], 16)),
    str(int(offsets['Team'], 16)),
    str(int(offsets['TeamColor'], 16)),
    str(int(offsets['Health'], 16)),
    str(int(offsets['Name'], 16)),
    str(int(offsets['Children'], 16))
], stdin=PIPE, text=True)

#on_release(reEnableEspKeyBind)

print('Inited! Creating GUI...')

app = QApplication([])
window = MyApp()
window.INJECT.clicked.connect(init)
#window.Apply.clicked.connect(apply)
window.Speed.valueChanged.connect(speedChange)
window.Jumppower.valueChanged.connect(jpChange)
window.DelFog.clicked.connect(delFog)
window.FOV.valueChanged.connect(fovChange)
window.Gravity.valueChanged.connect(gravChange)
window.Reset.clicked.connect(resetChr)
window.Radar.stateChanged.connect(toogleRadar)
window.IgnoreTeam.stateChanged.connect(toogleIgnoreTeam)
window.IgnoreDead.stateChanged.connect(toogleIgnoreDead)
#window.ReEsp.clicked.connect(reEnableEsp)
#window.ESP.stateChanged.connect(reEnableEspBtnToogle)
window.show()

def loops():
    while True:
        if window.LoopSetFOV.isChecked():
            write_float(fovAddr, float(window.FOV.value()))
        if window.Noclip.isChecked():
            getHumAddr(False)
            ChildrenOfInstance = GetChildren(read_int8(humAddr + int(offsets['Parent'], 16)))
            for i in ChildrenOfInstance:
                try:
                    name = GetName(i)
                    if name == 'HumanoidRootPart' or name == 'UpperTorso' or name == 'LowerTorso' or name == 'Torso':
                        print(name)
                        primitive = read_int8(i + int(offsets['Primitive'], 16))
                        write_bool(primitive + int(offsets['CanCollide'], 16), False)
                except:
                    pass
        #sleep(1)

Thread(target=loops, daemon=True).start()
sys.exit(app.exec_())
