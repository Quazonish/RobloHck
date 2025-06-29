print('Loading libs...')
from rbxMemory import *
from gui import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
from time import time, sleep
from threading import Thread
from requests import get
from subprocess import Popen, PIPE
from os import path
import sys

print('Loaded libs! Getting offsets...')
offsets = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json').json()

print('Supported versions:')
print(offsets['RobloxVersion'])
print(offsets['ByfronVersion'])
print('Current latest roblox version:', get('https://weao.xyz/api/versions/current', headers={'User-Agent': 'WEAO-3PService'}).json()['Windows'])
print('Got some offsets! Init...')

setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))

baseAddr = 0
camAddr = 0
startTime = 0
humAddr = 0
hrpAddr = 0
def background_process_monitor():
    global baseAddr
    while True:
        if is_process_dead():
            while not yield_for_program("RobloxPlayerBeta.exe"):
                sleep(0.5)
            baseAddr = get_base_addr()
        sleep(0.1)

Thread(target=background_process_monitor, daemon=True).start()

def init():
    global dataModel, wsAddr, lightingAddr, camAddr, fovAddr, camLVAddr, startFogAddr, endFogAddr, plrsAddr, lpAddr
    fakeDatamodel = pm.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16))
    print(f'Fake datamodel: {fakeDatamodel:x}')

    dataModel = pm.read_longlong(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
    print(f'Real datamodel: {dataModel:x}')

    wsAddr = pm.read_longlong(dataModel + int(offsets['Workspace'], 16))
    print(f'Workspace: {wsAddr:x}')

    camAddr = pm.read_longlong(wsAddr + int(offsets['Camera'], 16))
    fovAddr = camAddr + int(offsets['FOV'], 16)
    camLVAddr = pm.read_longlong(wsAddr + int(offsets['Camera'], 16)) + int(offsets['CameraRotation'], 16)
    print(f'Camera: {camAddr:x}')

    visualEngine = pm.read_longlong(baseAddr + int(offsets['VisualEnginePointer'], 16))
    matrixAddr = visualEngine + int(offsets['viewmatrix'], 16)
    print(f'Matrix: {matrixAddr:x}')

    print('Pls wait while we other stuff...')
    lightingAddr = FindFirstChildOfClass(dataModel, 'Lighting')

    startFogAddr = lightingAddr + int(offsets['FogStart'], 16)
    endFogAddr = lightingAddr + int(offsets['FogEnd'], 16)
    print(f'Lighting service: {lightingAddr:x}')

    plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
    print(f'Players: {plrsAddr:x}')

    lpAddr = pm.read_longlong(plrsAddr + int(offsets['LocalPlayer'], 16))
    print(f'Local player: {plrsAddr:x}')

    radar.stdin.write(f'addrs{lpAddr},{camLVAddr},{plrsAddr}\n')
    radar.stdin.flush()
    esp.stdin.write(f'addrs{lpAddr},{matrixAddr},{plrsAddr}\n')
    esp.stdin.flush()

    print('Injected successfully\n-------------------------------')

def getHumAddr(changeTime=True):
    global humAddr, startTime
    if time() - startTime > 10:
        humAddr = pm.read_longlong(camAddr + int(offsets['CameraSubject'], 16))
    if changeTime:
        startTime = time()

def getHrpAddr(changeTime=True):
    global hrpAddr, humAddr, startTime
    if time() - startTime > 10:
        humAddr = pm.read_longlong(camAddr + int(offsets['CameraSubject'], 16))
        char = pm.read_longlong(humAddr + int(offsets['Parent'], 16))
        hrpAddr = FindFirstChild(char, 'HumanoidRootPart')
    if changeTime:
        startTime = time()

def afterDeath():
    oldHumAddr = 0
    while camAddr == 0:
        sleep(1)

    while True:
        if window.AfterDeathApply.isChecked():
            hum = pm.read_longlong(camAddr + int(offsets['CameraSubject'], 16))
            if oldHumAddr != hum:
                pm.write_float(hum + int(offsets['WalkSpeedCheck'], 16), float('inf'))
                pm.write_float(hum + int(offsets['WalkSpeed'], 16), float(window.Speed.value()))
                pm.write_float(hum + int(offsets['JumpPower'], 16), float(window.Jumppower.value()))
                oldHumAddr = hum
        sleep(1)

Thread(target=afterDeath, daemon=True).start()

def speedChange(val):
    getHumAddr()
    pm.write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
    pm.write_float(humAddr + int(offsets['WalkSpeed'], 16), float(val))

def jpChange(val):
    getHumAddr()
    pm.write_float(humAddr + int(offsets['JumpPower'], 16), float(val))

def delFog():
    ChildrenOfInstance = GetChildren(lightingAddr)
    for i in ChildrenOfInstance:
        try:
            if GetClassName(i) == 'Atmosphere':
                pm.write_float(i + 0xE0, float(0))
                pm.write_float(i + 0xE8, float(0))
        except:
            pass
    pm.write_float(endFogAddr, float('inf'))
    pm.write_float(startFogAddr, float('inf'))

def fovChange(val):
    pm.write_float(fovAddr, float(val))

def gravChange(val):
    getHrpAddr()
    pm.write_float(pm.read_longlong(hrpAddr + int(offsets['Primitive'], 16)) + int(offsets['PrimitiveGravity'], 16), float(val))

def resetChr():
    getHumAddr()
    pm.write_float(humAddr + int(offsets['Health'], 16), float(0))

print('Inited! Creating GUI...')

def toogleRadar():
    radar.stdin.write('toogle1\n')
    radar.stdin.flush()

def toogleIgnoreTeamRadar():
    radar.stdin.write('toogle2\n')
    radar.stdin.flush()

def toogleIgnoreDeadRadar():
    radar.stdin.write('toogle3\n')
    radar.stdin.flush()

def toogleEsp():
    esp.stdin.write('toogle1\n')
    esp.stdin.flush()

def toogleIgnoreTeamEsp():
    esp.stdin.write('toogle2\n')
    esp.stdin.flush()

def toogleIgnoreDeadEsp():
    esp.stdin.write('toogle3\n')
    esp.stdin.flush()

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

if hasattr(sys, '_MEIPASS'):
    radar = Popen([
        path.join(sys._MEIPASS, 'radar.exe'),
        str(int(offsets['ModelInstance'], 16)),
        str(int(offsets['Primitive'], 16)),
        str(int(offsets['Position'], 16)),
        str(int(offsets['Team'], 16)),
        str(int(offsets['TeamColor'], 16)),
        str(int(offsets['Health'], 16)),
        str(int(offsets['Name'], 16)),
        str(int(offsets['Children'], 16))
    ], stdin=PIPE, text=True)

    esp = Popen([
        path.join(sys._MEIPASS, 'esp.exe'),
        str(int(offsets['ModelInstance'], 16)),
        str(int(offsets['Primitive'], 16)),
        str(int(offsets['Position'], 16)),
        str(int(offsets['Team'], 16)),
        str(int(offsets['TeamColor'], 16)),
        str(int(offsets['Health'], 16)),
        str(int(offsets['Name'], 16)),
        str(int(offsets['Children'], 16))
    ], stdin=PIPE, text=True)
else:
    radar = Popen([
        'python', 'radar.py',
        str(int(offsets['ModelInstance'], 16)),
        str(int(offsets['Primitive'], 16)),
        str(int(offsets['Position'], 16)),
        str(int(offsets['Team'], 16)),
        str(int(offsets['TeamColor'], 16)),
        str(int(offsets['Health'], 16)),
        str(int(offsets['Name'], 16)),
        str(int(offsets['Children'], 16))
    ], stdin=PIPE, text=True)

    esp = Popen([
        'python', 'esp.py',
        str(int(offsets['ModelInstance'], 16)),
        str(int(offsets['Primitive'], 16)),
        str(int(offsets['Position'], 16)),
        str(int(offsets['Team'], 16)),
        str(int(offsets['TeamColor'], 16)),
        str(int(offsets['Health'], 16)),
        str(int(offsets['Name'], 16)),
        str(int(offsets['Children'], 16))
    ], stdin=PIPE, text=True)

app = QApplication([])
window = MyApp()
window.INJECT.clicked.connect(init)
window.Speed.valueChanged.connect(speedChange)
window.Jumppower.valueChanged.connect(jpChange)
window.DelFog.clicked.connect(delFog)
window.FOV.valueChanged.connect(fovChange)
window.Gravity.valueChanged.connect(gravChange)
window.Reset.clicked.connect(resetChr)
window.Radar.stateChanged.connect(toogleRadar)
window.IgnoreTeamRadar.stateChanged.connect(toogleIgnoreTeamRadar)
window.IgnoreDeadRadar.stateChanged.connect(toogleIgnoreDeadRadar)
window.ESP.stateChanged.connect(toogleEsp)
window.IgnoreTeamEsp.stateChanged.connect(toogleIgnoreTeamEsp)
window.IgnoreDeadEsp.stateChanged.connect(toogleIgnoreDeadEsp)
window.show()

def loops():
    while True:
        if window.LoopSetFOV.isChecked():
            pm.write_float(fovAddr, float(window.FOV.value()))
        if window.Noclip.isChecked():
            getHumAddr(False)
            ChildrenOfInstance = GetChildren(pm.read_longlong(humAddr + int(offsets['Parent'], 16)))
            for i in ChildrenOfInstance:
                try:
                    name = GetName(i)
                    if name in ['HumanoidRootPart', 'UpperTorso', 'LowerTorso', 'Torso']:
                        primitive = pm.read_longlong(i + int(offsets['Primitive'], 16))
                        pm.write_bytes(primitive + int(offsets['CanCollide'], 16), b'\x00', 1)
                except:
                    pass

Thread(target=loops, daemon=True).start()
sys.exit(app.exec_())
