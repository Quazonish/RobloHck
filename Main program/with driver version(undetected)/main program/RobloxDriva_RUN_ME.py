print('Loading libs...')
from rbxMemory import *
from numpy import array, float32, linalg, cross, dot, reshape
from ctypes import windll, byref, Structure, wintypes
from ctypes.wintypes import RECT, POINT
from math import sqrt, pi
from time import time, sleep
from threading import Thread
from requests import get
from subprocess import Popen, PIPE
from os import path
from imgui_bundle import imgui, immapp, hello_imgui
import sys

pi180 = pi/180

reset_enabled = False
fov_enabled = False
noclip_enabled = False
aimbot_enabled = False
esp_enabled = False
radar_enabled = False
esp_ignoreteam = False
esp_ignoredead = False
radar_ignoreteam = False
radar_ignoredead = False
aimbot_ignoreteam = False
aimbot_ignoredead = False
zoomCam_enabled = False

walkspeed_val = 16.0
jumppower_val = 50.0
fov_val = 70.0

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

camAddr = 0
dataModel = 0
mouseSensivityAddr = 0
wsAddr = 0
lightingAddr = 0
fovAddr = 0
camCFrameRotAddr = 0
startFogAddr = 0
endFogAddr = 0
plrsAddr = 0
lpAddr = 0
matrixAddr = 0
camPosAddr = 0
radar = None
esp = None

def init():
    global dataModel, wsAddr, lightingAddr, camAddr, fovAddr, camCFrameRotAddr, startFogAddr, endFogAddr, plrsAddr, lpAddr, matrixAddr, camPosAddr, radar, esp, mouseSensivityAddr
    pid = get_pid_by_name("RobloxPlayerBeta.exe")
    if pid is None:
        print('You forgot to open roblox!')
        return
    setPid(pid)
    radar.stdin.write(f'desc{pid}\n')
    radar.stdin.flush()
    esp.stdin.write(f'desc{pid}\n')
    esp.stdin.flush()
    try:
        baseAddr = find_image_base() #get_module_base(pid)

        fakeDatamodel = read_int8(baseAddr + offsets['FakeDataModelPointer'])
        print(f'Fake datamodel: {fakeDatamodel:x}')
        
        dataModel = read_int8(fakeDatamodel + offsets['FakeDataModelToDataModel'])
        print(f'Real datamodel: {dataModel:x}')
        
        wsAddr = read_int8(dataModel + offsets['Workspace']) #FindFirstChildOfClass(dataModel, 'Workspace')
        print(f'Workspace: {wsAddr:x}')
        
        camAddr = read_int8(wsAddr + offsets['Camera']) #FindFirstChildOfClass(wsAddr, 'Camera')
        fovAddr = camAddr + offsets['FOV']
        camCFrameRotAddr = camAddr + offsets['CameraRotation']
        camPosAddr = camAddr + offsets['CameraPos']
        print(f'Camera: {camAddr:x}')

        mouseSensivityAddr = baseAddr + offsets['MouseSensitivity']
        print(f'Mouse sensivity: {mouseSensivityAddr:x}')

        visualEngine = read_int8(baseAddr + offsets['VisualEnginePointer'])
        matrixAddr = visualEngine + offsets['viewmatrix']
        print(f'Matrix: {matrixAddr:x}')
        
        print('Pls wait while we getting other stuff...')
        lightingAddr = FindFirstChildOfClass(dataModel, 'Lighting')
        
        startFogAddr = lightingAddr + offsets['FogStart']
        endFogAddr = lightingAddr + offsets['FogEnd']
        print(f'Lighting service: {lightingAddr:x}')

        plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
        print(f'Players: {plrsAddr:x}')

        lpAddr = read_int8(plrsAddr + offsets['LocalPlayer'])
        print(f'Local player: {lpAddr:x}')
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
    if camAddr > 0:
        getHumAddr()
        write_float(humAddr + offsets['WalkSpeedCheck'], float('inf'))
        write_float(humAddr + offsets['WalkSpeed'], float(val))

def jpChange(val):
    if camAddr > 0:
        getHumAddr()
        write_float(humAddr + offsets['JumpPower'], float(val))

startTime = 0
def getHumAddr(changeTime=True):
    global humAddr, startTime
    if time()-startTime > 10:
        humAddr = read_int8(camAddr + offsets['CameraSubject'])
    if changeTime:
        startTime = time()

#def getHrpAddr(changeTime=True): #currently unused, but may be used later
#    global hrpAddr, humAddr, startTime
#    if time()-startTime > 10:
#        humAddr = read_int8(camAddr + offsets['CameraSubject'])
#        char = read_int8(humAddr + offsets['Parent'])
#        hrpAddr = FindFirstChild(char, 'HumanoidRootPart')
#    if changeTime:
#        startTime = time()

def writeAtmosphere(child):
    try:
        if GetClassName(child) == 'Atmosphere':
            write_float(child+0xE0, float(0))
            write_float(child+0xE8, float(0))
            print('Wrote atmosphere')
    except OSError:
        pass

def delFog():
    if lightingAddr > 0:
        print('Removing fog...')
        DoForEveryChild(lightingAddr, writeAtmosphere)
        write_float(endFogAddr, float('inf'))
        write_float(startFogAddr, float('inf'))
        print('Fog removed')

def fovChange(val):
    if fovAddr > 0:
        write_float(fovAddr, float(val * pi180))

def resetChr():
    if camAddr > 0:
        getHumAddr()
        write_float(humAddr + offsets['Health'], float(0))

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

print('Converting strings to ints...')
for key, val in offsets.items():
    offsets[key] = int(val, 16)

print('Got some offsets! Init...')
setOffsets(offsets['Name'], offsets['Children'])

if hasattr(sys, '_MEIPASS'):
    radar = Popen([
        path.abspath(path.join(sys._MEIPASS, '..', 'radar.exe')),
        str(offsets['ModelInstance']),
        str(offsets['Primitive']),
        str(offsets['Position']),
        str(offsets['Team']),
        str(offsets['TeamColor']),
        str(offsets['Health']),
        str(offsets['Name']),
        str(offsets['Children'])
    ], stdin=PIPE, text=True)

    esp = Popen([
        path.abspath(path.join(sys._MEIPASS, '..', 'esp.exe')),
        str(offsets['ModelInstance']),
        str(offsets['Primitive']),
        str(offsets['Position']),
        str(offsets['Team']),
        str(offsets['TeamColor']),
        str(offsets['Health']),
        str(offsets['Name']),
        str(offsets['Children'])
    ], stdin=PIPE, text=True)
else:
    radar = Popen([
        'python', 'radar.py',
        str(offsets['ModelInstance']),
        str(offsets['Primitive']),
        str(offsets['Position']),
        str(offsets['Team']),
        str(offsets['TeamColor']),
        str(offsets['Health']),
        str(offsets['Name']),
        str(offsets['Children'])
    ], stdin=PIPE, text=True)

    esp = Popen([
        'python', 'esp.py',
        str(offsets['ModelInstance']),
        str(offsets['Primitive']),
        str(offsets['Position']),
        str(offsets['Team']),
        str(offsets['TeamColor']),
        str(offsets['Health']),
        str(offsets['Name']),
        str(offsets['Children'])
    ], stdin=PIPE, text=True)

print('Inited! Creating GUI...')

def loopFOV():
    while True:
        if fov_enabled and fovAddr > 0:
            write_float(fovAddr, float(fov_val * pi180))
        sleep(1)

def disableCollide(child):
    try:
        if GetName(child) in ['HumanoidRootPart', 'UpperTorso', 'LowerTorso', 'Torso', 'Head']:
            write(read_int8(child + offsets['Primitive']) + offsets['CanCollide'] + offsets['CanCollideMask'] - 1, b'\x30')
    except OSError:
        pass

def noclipLoop():
    while True:
        if noclip_enabled and camAddr > 0:
            getHumAddr(False)
            DoForEveryChild(read_int8(humAddr + offsets['Parent']), disableCollide)
        else:
            sleep(1)

target = 0
width, height = 1920, 1080
widthCenter, heightCenter = 960, 540
view_proj_matrix = None
minDistance = float('inf')
def checkIsPlayerClosest(child):
    global target, view_proj_matrix, width, height, widthCenter, heightCenter, minDistance
    try:
        if child != lpAddr:
            if not aimbot_ignoreteam or read_int8(child + offsets['Team']) != lpTeam:
                char = read_int8(child + offsets['ModelInstance'])
                head = FindFirstChild(char, 'Head')
                hum = FindFirstChildOfClass(char, 'Humanoid')
                if head and hum:
                    health = read_float(hum + offsets['Health'])
                    if aimbot_ignoredead and health <= 0:
                        return
                    primitive = read_int8(head + offsets['Primitive'])
                    targetPos = primitive + offsets['Position']
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
    except OSError:
        pass

def aimbotLoop():
    global target, view_proj_matrix, width, height, widthCenter, heightCenter, minDistance
    left, top, right, bottom = 0, 0, 1920, 1080
    while True:
        if aimbot_enabled and matrixAddr > 0:
            if windll.user32.GetAsyncKeyState(2) & 0x8000 != 0:
                if target > 0:
                    from_pos = [read_float(camPosAddr), read_float(camPosAddr+4), read_float(camPosAddr+8)]
                    to_pos = [read_float(target), read_float(target+4), read_float(target+8)]

                    look, up, right = cframe_look_at(from_pos, to_pos)

                    write(camCFrameRotAddr, pack("<fffffffff",
                        -right[0], up[0], -look[0],
                        -right[1], up[1], -look[1],
                        -right[2], up[2], -look[2]                         
                    ))
                else:
                    target = 0
                    hwnd_roblox = find_window_by_title("Roblox")
                    if hwnd_roblox:
                        left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                    matrix_flat = [read_float(matrixAddr + i * 4) for i in range(16)]
                    view_proj_matrix = reshape(array(matrix_flat, dtype=float32), (4, 4))
                    lpTeam = read_int8(lpAddr + offsets['Team'])
                    width = right - left
                    height = bottom - top
                    widthCenter = width/2
                    heightCenter = height/2
                    minDistance = float('inf')
                    DoForEveryChild(plrsAddr, checkIsPlayerClosest)
            else:
                target = 0
        else:
            sleep(1)

def afterDeath():
    oldHumAddr = 0
    while camAddr == 0:
        sleep(1)

    while True:
        if reset_enabled:
            hum = read_int8(camAddr + offsets['CameraSubject'])
            if oldHumAddr != hum:
                write_float(hum + offsets['WalkSpeedCheck'], float('inf'))
                write_float(hum + offsets['WalkSpeed'], float(walkspeed_val))
                write_float(hum + offsets['JumpPower'], float(jumppower_val))
                oldHumAddr = hum
        sleep(1)

oldRBM = False

def camZoomLoop():
    global oldRBM
    while True:
        if mouseSensivityAddr > 0 and fovAddr > 0:
            if zoomCam_enabled:
                if windll.user32.GetAsyncKeyState(2) & 0x8000 == 0 and oldRBM:
                    write_float(fovAddr, read_float(fovAddr) * 4)
                    newMouseSens = read_float(mouseSensivityAddr) * 4
                    write(mouseSensivityAddr, pack("<ffff", newMouseSens, newMouseSens, newMouseSens, newMouseSens))
                    write_float(mouseSensivityAddr + 0x44, newMouseSens)
                    oldRBM = False
                elif windll.user32.GetAsyncKeyState(2) & 0x8000 != 0 and oldRBM == False:
                    write_float(fovAddr, read_float(fovAddr) / 4)
                    newMouseSens = read_float(mouseSensivityAddr) / 4
                    write(mouseSensivityAddr, pack("<ffff", newMouseSens, newMouseSens, newMouseSens, newMouseSens))
                    write_float(mouseSensivityAddr + 0x44, newMouseSens)
                    oldRBM = True
            else:
                sleep(1)
        else:
            sleep(1)
                

Thread(target=loopFOV, daemon=True).start()
Thread(target=noclipLoop, daemon=True).start()
Thread(target=aimbotLoop, daemon=True).start()
Thread(target=camZoomLoop, daemon=True).start()
Thread(target=afterDeath, daemon=True).start()

def render_ui():
    global reset_enabled, fov_enabled, zoomCam_enabled
    global noclip_enabled, aimbot_enabled, esp_enabled, radar_enabled
    global esp_ignoreteam, esp_ignoredead, radar_ignoreteam, radar_ignoredead, aimbot_ignoreteam, aimbot_ignoredead
    global walkspeed_val, jumppower_val, fov_val
    
    changed, walkspeed_val = imgui.slider_float("WalkSpeed", walkspeed_val, 0.0, 1000.0, "%.1f")
    if changed:
        speedChange(walkspeed_val)
    
    changed, jumppower_val = imgui.slider_float("Jump Power", jumppower_val, 0.0, 1000.0, "%.1f")
    if changed:
        jpChange(jumppower_val)
    
    changed, fov_val = imgui.slider_float("FOV", fov_val, 1.0, 120.0, "%.1f")
    if changed:
        fovChange(fov_val)
    
    _, noclip_enabled = imgui.checkbox("Noclip", noclip_enabled)
    imgui.same_line()
    _, zoomCam_enabled = imgui.checkbox("Zoom camera when aiming", zoomCam_enabled)

    _, reset_enabled = imgui.checkbox("Apply after death", reset_enabled)
    imgui.same_line()
    _, fov_enabled = imgui.checkbox("Loop set FOV", fov_enabled)
    
    imgui.separator()
    imgui.spacing()
    
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(0.11, 0.51, 0.81, 1.0))
    imgui.text("Visual Modifications")
    imgui.pop_style_color()
    
    _, aimbot_enabled = imgui.checkbox("Aimbot", aimbot_enabled)
    imgui.same_line()
    
    changed, esp_enabled = imgui.checkbox("ESP", esp_enabled)
    imgui.same_line()
    if changed:
        toogleEsp()
        
    changed, radar_enabled = imgui.checkbox("Radar", radar_enabled)
    imgui.same_line()
    if changed:
        toogleRadar()
    
    if imgui.button("Remove Fog"):
        delFog()

    imgui.spacing()
    imgui.separator()
    imgui.spacing()
    
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(0.11, 0.51, 0.81, 1.0))
    imgui.text("Visual Settings")
    imgui.pop_style_color()
    
    changed, esp_ignoreteam = imgui.checkbox("Ignore Team [ESP]", esp_ignoreteam)
    if changed:
        toogleIgnoreTeamEsp()
    imgui.same_line()
    changed, esp_ignoredead = imgui.checkbox("Ignore Dead [ESP]", esp_ignoredead)
    if changed:
        toogleIgnoreDeadEsp()

    changed, radar_ignoreteam = imgui.checkbox("Ignore Team [Radar]", radar_ignoreteam)
    if changed:
        toogleIgnoreTeamRadar()
    imgui.same_line()
    changed, radar_ignoredead = imgui.checkbox("Ignore Dead [Radar]", radar_ignoredead)
    if changed:
        toogleIgnoreDeadRadar()
    
    _, aimbot_ignoreteam = imgui.checkbox("Ignore Team [Aimbot]", aimbot_ignoreteam)
    imgui.same_line()
    _, aimbot_ignoredead = imgui.checkbox("Ignore Dead [Aimbot]", aimbot_ignoredead)
    
    imgui.separator()
    imgui.spacing()
    
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(0.11, 0.51, 0.81, 1.0))
    imgui.text("Misc Stuff")
    imgui.pop_style_color()

    if imgui.button("Inject"):
        init()
    imgui.same_line()
    if imgui.button("Reset"):
        resetChr()

immapp.run(
    gui_function=render_ui,
    window_title="RobloHck 3000",
    window_size_auto=True,
    with_markdown=True,
    fps_idle=10
)
esp.terminate()
radar.terminate()
