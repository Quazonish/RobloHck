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

walkspeed_val = 16.0
jumppower_val = 50.0
fov_val = 70.0
gravity_val = 196.2

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
    global dataModel, wsAddr, lightingAddr, camAddr, fovAddr, camCFrameRotAddr, startFogAddr, endFogAddr, plrsAddr, lpAddr, matrixAddr, camPosAddr, radar, esp
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
    if camAddr > 0:
        getHumAddr()
        write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
        write_float(humAddr + int(offsets['WalkSpeed'], 16), float(val))

def jpChange(val):
    if camAddr > 0:
        getHumAddr()
        write_float(humAddr + int(offsets['JumpPower'], 16), float(val))

startTime = 0
def getHumAddr(changeTime=True):
    global humAddr, startTime
    if time()-startTime > 10:
        humAddr = read_int8(camAddr + int(offsets['CameraSubject'], 16))
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
    if lightingAddr > 0:
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
    if fovAddr > 0:
        write_float(fovAddr, float(val * pi180))

def gravChange(val):
    if camAddr > 0:
        getHrpAddr()
        write_float(read_int8(hrpAddr + int(offsets['Primitive'], 16)) + int(offsets['PrimitiveGravity'], 16), float(val))

def resetChr():
    if camAddr > 0:
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

def loopFOV():
    while True:
        if fov_enabled and fovAddr > 0:
            write_float(fovAddr, float(fov_val * pi180))
        sleep(1)

def noclipLoop():
    while True:
        if noclip_enabled and camAddr > 0:
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
        if aimbot_enabled and matrixAddr > 0:
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
                            if not aimbot_ignoreteam or read_int8(v + int(offsets['Team'], 16)) != lpTeam:
                                char = read_int8(v + int(offsets['ModelInstance'], 16))
                                head = FindFirstChild(char, 'Head')
                                hum = FindFirstChildOfClass(char, 'Humanoid')
                                if head and hum:
                                    health = read_float(hum + int(offsets['Health'], 16))
                                    if aimbot_ignoredead and health <= 0:
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
        if reset_enabled:
            hum = read_int8(camAddr + int(offsets['CameraSubject'], 16))
            if oldHumAddr != hum:
                write_float(hum + int(offsets['WalkSpeedCheck'], 16), float('inf'))
                write_float(hum + int(offsets['WalkSpeed'], 16), float(walkspeed_val))
                write_float(hum + int(offsets['JumpPower'], 16), float(jumppower_val))
                oldHumAddr = hum
        sleep(1)

Thread(target=loopFOV, daemon=True).start()
Thread(target=noclipLoop, daemon=True).start()
Thread(target=aimbotLoop, daemon=True).start()
Thread(target=afterDeath, daemon=True).start()

def render_ui():
    global reset_enabled, fov_enabled
    global noclip_enabled, aimbot_enabled, esp_enabled, radar_enabled
    global esp_ignoreteam, esp_ignoredead, radar_ignoreteam, radar_ignoredead, aimbot_ignoreteam, aimbot_ignoredead
    global walkspeed_val, jumppower_val, fov_val, gravity_val
    
    changed, walkspeed_val = imgui.slider_float("WalkSpeed", walkspeed_val, 0.0, 1000.0, "%.1f")
    if changed:
        speedChange(walkspeed_val)
    
    changed, jumppower_val = imgui.slider_float("Jump Power", jumppower_val, 0.0, 1000.0, "%.1f")
    if changed:
        jpChange(jumppower_val)
    
    changed, fov_val = imgui.slider_float("FOV", fov_val, 1.0, 120.0, "%.1f")
    if changed:
        fovChange(fov_val)
    
    changed, gravity_val = imgui.slider_float("Gravity", gravity_val, 0.0, 500.0, "%.1f")
    if changed:
        gravChange(gravity_val)
    
    _, noclip_enabled = imgui.checkbox("Noclip", noclip_enabled)
    _, reset_enabled = imgui.checkbox("Apply after death", reset_enabled)
    imgui.same_line()
    _, fov_enabled = imgui.checkbox("Loop set FOV", fov_enabled)
    
    imgui.separator()
    imgui.spacing()
    
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(0.11, 0.51, 0.81, 1.0))
    imgui.text("Visual Modifications")
    imgui.pop_style_color()
    
    _, aimbot_enabled = imgui.checkbox("Aimbot", aimbot_enabled)
    
    changed, esp_enabled = imgui.checkbox("ESP", esp_enabled)
    if changed:
        toogleEsp()
        
    changed, radar_enabled = imgui.checkbox("Radar", radar_enabled)
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
