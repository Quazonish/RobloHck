from rbxMemory import *
from numpy import array, float32, linalg, cross, dot, reshape
from ctypes import windll, byref, Structure, wintypes
from ctypes.wintypes import HWND, RECT, POINT
from math import sqrt
from time import time, sleep
from threading import Thread
from gui import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
#from keyboard import on_release
from requests import get
from subprocess import Popen, PIPE
from os import path
import sys

open_device()

hrpGravAddr = 0
humAddr = 0
hrpAddr = 0

class RECT(Structure):
    _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

class POINT(Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

def find_window_by_title(title):
    return windll.user32.FindWindowW(None, title)

def get_client_rect_on_screen(hwnd):
    rect = RECT()
    if windll.user32.GetClientRect(hwnd, byref(rect)) == 0:
        return 0, 0, 0, 0
    top_left = POINT(rect.left, rect.top)
    bottom_right = POINT(rect.right, rect.bottom)
    windll.user32.ClientToScreen(hwnd, byref(top_left))
    windll.user32.ClientToScreen(hwnd, byref(bottom_right))
    return top_left.x, top_left.y, bottom_right.x, bottom_right.y

def world_to_screen_with_matrix(world_pos, matrix, screen_width, screen_height):
    vec = array([*world_pos, 1.0], dtype=float32)
    clip = dot(matrix, vec)
    if clip[3] == 0: return None
    ndc = clip[:3] / clip[3]
    if ndc[2] < 0 or ndc[2] > 1: return None
    x = (ndc[0] + 1) * 0.5 * screen_width
    y = (1 - ndc[1]) * 0.5 * screen_height
    return round(x), round(y)

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

camAddr = 0

def init():
    global dataModel, wsAddr, lightingAddr, camAddr, fovAddr, camCFrameRotAddr, startFogAddr, endFogAddr, plrsAddr, lpAddr, matrixAddr, camPosAddr
    pid = get_pid_by_name("RobloxPlayerBeta.exe")
    if pid is None:
        print('You forget to open roblox!')
        return
    setPid(pid)
    radar.stdin.write(f'desc{pid}\n')
    radar.stdin.flush()
    esp.stdin.write(f'desc{pid}\n')
    esp.stdin.flush()
    try:
        baseAddr = find_image_base() #get_module_base(pid)

        fakeDatamodel = read_int8(baseAddr + int(offsets['FakeDataModelPointer'], 16))
        print(f'Fake datamodel: {fakeDatamodel:x}')
        
        dataModel = read_int8(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
        print(f'Real datamodel: {dataModel:x}')
        
        wsAddr = read_int8(dataModel + int(offsets['Workspace'], 16)) #FindFirstChildOfClass(dataModel, 'Workspace')
        print(f'Workspace: {wsAddr:x}')
        
        camAddr = read_int8(wsAddr + int(offsets['Camera'], 16)) #FindFirstChildOfClass(wsAddr, 'Camera')
        fovAddr = camAddr + int(offsets['FOV'], 16)
        camCFrameRotAddr = camAddr + int(offsets['CameraRotation'], 16)
        camPosAddr = camAddr + int(offsets['CameraPos'], 16)

        print(f'Camera: {camAddr:x}')

        visualEngine = read_int8(baseAddr + int(offsets['VisualEnginePointer'], 16))
        matrixAddr = visualEngine + int(offsets['viewmatrix'], 16)
        print(f'Matrix: {matrixAddr:x}')
        
        print('Pls wait while we getting other stuff...')
        lightingAddr = FindFirstChildOfClass(dataModel, 'Lighting')
        
        startFogAddr = lightingAddr + int(offsets['FogStart'], 16)
        endFogAddr = lightingAddr + int(offsets['FogEnd'], 16)
        print(f'Lighting service: {lightingAddr:x}')

        plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
        print(f'Players: {plrsAddr:x}')

        lpAddr = read_int8(plrsAddr + int(offsets['LocalPlayer'], 16))
        print(f'Local player: {plrsAddr:x}')
    except OSError:
        print("You didn't run this program as admin, or you just forgot to drag .sys file into kdmapper(after dragging, restart this program)!")
        return

    radar.stdin.write(f'addrs{lpAddr},{camCFrameRotAddr},{plrsAddr}\n')
    radar.stdin.flush()

    esp.stdin.write(f'addrs{lpAddr},{matrixAddr},{plrsAddr}\n')
    esp.stdin.flush()
    
    print('Injected successfully\n-------------------------------')

def normalize(vec):
    norm = linalg.norm(vec)
    return vec / norm if norm != 0 else vec

def cframe_look_at(from_pos, to_pos):
    from_pos = array(from_pos, dtype=float32)
    to_pos = array(to_pos, dtype=float32)

    look_vector = normalize(to_pos - from_pos)
    up_vector = array([0, 1, 0], dtype=float32)

    if abs(look_vector[1]) > 0.999:
        up_vector = array([0, 0, -1], dtype=float32)

    right_vector = normalize(cross(up_vector, look_vector))
    recalculated_up = cross(look_vector, right_vector)

    return look_vector, recalculated_up, right_vector

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

def fovChange(val):
    write_float(fovAddr, float(val))

def gravChange(val):
    getHrpAddr()
    write_float(read_int8(hrpAddr + int(offsets['Primitive'], 16)) + int(offsets['PrimitiveGravity'], 16), float(val))

def resetChr():
    getHumAddr()
    write_float(humAddr + int(offsets['Health'], 16), float(0))

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

print('Loaded libs and stuff! Getting offsets...')
offsets = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json').json()
print('Supported versions:')
print(offsets['RobloxVersion'])
print(offsets['ByfronVersion'])
print('Current latest roblox version:', get('https://weao.xyz/api/versions/current', headers={'User-Agent': 'WEAO-3PService'}).json()['Windows'])
print('Got some offsets! Init...')
setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))

if hasattr(sys, '_MEIPASS'):
    radar = Popen([
        path.abspath(path.join(sys._MEIPASS, '..', 'radar.exe')),
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
        path.abspath(path.join(sys._MEIPASS, '..', 'esp.exe')),
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

print('Inited! Creating GUI...')

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

def loopFOV():
    while True:
        if window.LoopSetFOV.isChecked():
            write_float(fovAddr, float(window.FOV.value()))
        sleep(1)

def noclipLoop():
    while True:
        if window.Noclip.isChecked():
            getHumAddr(False)
            ChildrenOfInstance = GetChildren(read_int8(humAddr + int(offsets['Parent'], 16)))
            for i in ChildrenOfInstance:
                try:
                    name = GetName(i)
                    if name in ['HumanoidRootPart', 'UpperTorso', 'LowerTorso', 'Torso', 'Head']:
                        write_bool(read_int8(i + int(offsets['Primitive'], 16)) + int(offsets['CanCollide'], 16), False)
                except:
                    pass
        else:
            sleep(1)

def aimbotLoop():
    target = 0
    left, top, right, bottom = 0, 0, 1920, 1080
    while True:
        if window.Aimbot.isChecked():
            if windll.user32.GetAsyncKeyState(2) & 0x8000 != 0:
                if target > 0:
                    from_pos = [read_float(camPosAddr), read_float(camPosAddr+4), read_float(camPosAddr+8)]
                    to_pos = [read_float(target), read_float(target+4), read_float(target+8)]

                    look, up, right = cframe_look_at(from_pos, to_pos)

                    write_float(camCFrameRotAddr, -right[0])
                    write_float(camCFrameRotAddr+4, up[0])
                    write_float(camCFrameRotAddr+8, -look[0])

                    write_float(camCFrameRotAddr+12, -right[1])
                    write_float(camCFrameRotAddr+16, up[1])
                    write_float(camCFrameRotAddr+20, -look[1])

                    write_float(camCFrameRotAddr+24, -right[2])
                    write_float(camCFrameRotAddr+28, up[2])
                    write_float(camCFrameRotAddr+32, -look[2])
                else:
                    target = 0
                    hwnd_roblox = find_window_by_title("Roblox")
                    if hwnd_roblox:
                        left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                    matrix_flat = [read_float(matrixAddr + i * 4) for i in range(16)]
                    view_proj_matrix = reshape(array(matrix_flat, dtype=float32), (4, 4))
                    lpTeam = read_int8(lpAddr + int(offsets['Team'], 16))
                    width = right - left
                    height = bottom - top
                    widthCenter = width/2
                    heightCenter = height/2
                    minDistance = float('inf')
                    for v in GetChildren(plrsAddr):
                        if v != lpAddr:
                            if not window.IgnoreTeamAimbot.isChecked() or read_int8(v + int(offsets['Team'], 16)) != lpTeam:
                                char = read_int8(v + int(offsets['ModelInstance'], 16))
                                head = FindFirstChild(char, 'Head')
                                hum = FindFirstChildOfClass(char, 'Humanoid')
                                if head and hum:
                                    health = read_float(hum + int(offsets['Health'], 16))
                                    if window.IgnoreDeadAimbot.isChecked() and health <= 0:
                                        continue
                                    primitive = read_int8(head + int(offsets['Primitive'], 16))
                                    targetPos = primitive + int(offsets['Position'], 16)
                                    obj_pos = array([
                                        read_float(targetPos),
                                        read_float(targetPos + 4),
                                        read_float(targetPos + 8)
                                    ], dtype=float32)
                                    screen_coords = world_to_screen_with_matrix(obj_pos, view_proj_matrix, width, height)
                                    if screen_coords is not None:
                                        distance = sqrt((widthCenter - screen_coords[0])**2 + (heightCenter - screen_coords[1])**2)
                                        if distance < minDistance:
                                            minDistance = distance
                                            target = targetPos
            else:
                target = 0
        else:
            sleep(1)

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
                write_float(hum + int(offsets['JumpPower'], 16), float(window.Jumppower.value()))
                oldHumAddr = hum
        sleep(1)

Thread(target=loopFOV, daemon=True).start()
Thread(target=noclipLoop, daemon=True).start()
Thread(target=aimbotLoop, daemon=True).start()
Thread(target=afterDeath, daemon=True).start()
sys.exit(app.exec_())
