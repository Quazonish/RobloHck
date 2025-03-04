print('Loading libs...')
from pymem import Pymem
from pymem.process import is_64_bit, list_processes
from ctypes import windll
from psutil import pid_exists
from gui import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
from keyboard import on_release
from time import time, sleep
from threading import Thread
from requests import get
#import keyboard
print('Loaded libs! Getting offsets...')
offsets = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json').json()
print('Supported versions:')
print(offsets['RobloxVersion'])
print(offsets['ByfronVersion'])
print('Current latest roblox version:', get('https://weao.xyz/api/versions/current', headers={'User-Agent': 'WEAO-3PService'}).json()['Windows'])
print('Got some offsets! Init...')
baseAddr = 0

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        '''self.fly_up_key = self.FlyUpKey.keySequence().toString()
        self.fly_down_key = self.FlyDownKey.keySequence().toString()

        self.FlyUpKey.editingFinished.connect(self.update_fly_up_key)
        self.FlyDownKey.editingFinished.connect(self.update_fly_down_key)

        self.apply_keybinds()

    def update_fly_up_key(self):
        new_key = self.FlyUpKey.keySequence().toString()
        if new_key and new_key != self.fly_up_key:
            self.fly_up_key = new_key
            self.apply_keybinds()

    def update_fly_down_key(self):
        new_key = self.FlyDownKey.keySequence().toString()
        if new_key and new_key != self.fly_down_key:
            self.fly_down_key = new_key
            self.apply_keybinds()

    def apply_keybinds(self):
        keyboard.unhook_all()

        if self.fly_up_key:
            keyboard.add_hotkey(self.fly_up_key, flyUp)
        if self.fly_down_key:
            keyboard.add_hotkey(self.fly_down_key, flyDown)'''

class hyper:
    def __init__(self, ProgramName=None):
        self.ProgramName = ProgramName
        self.Pymem = Pymem()
        self.Addresses = {}
        self.Handle = None
        self.is64bit = False
        self.ProcessID = -1
        self.PID = self.ProcessID
        access_rights = 0x1038
        if type(ProgramName) == str:
            self.Pymem = Pymem(ProgramName)
            self.Handle = windll.kernel32.OpenProcess(access_rights, False, self.Pymem.process_id)
            self.is64bit = not is_64_bit(self.Handle)
            self.ProcessID = self.Pymem.process_id
            self.PID = self.ProcessID
        elif type(ProgramName) == int:
            self.Pymem.open_process_from_id(ProgramName)
            self.Handle = windll.kernel32.OpenProcess(access_rights, False, ProgramName)
            self.is64bit = not is_64_bit(self.Handle)
            self.ProcessID = self.Pymem.process_id
            self.PID = self.ProcessID

    def h2d(self, hz: str, bit: int = 16) -> int:
        if type(hz) == int:
            return hz
        return int(hz, bit)

    def DRP(self, Address: int, is64Bit: bool = None) -> int:
        Address = Address
        if type(Address) == str:
            Address = self.h2d(Address)
        return int.from_bytes(self.Pymem.read_bytes(Address, 8), "little")

    def getRawProcesses(self):
        toreturn = []
        for i in list_processes():
            toreturn.append(
                [
                    i.cntThreads,
                    i.cntUsage,
                    i.dwFlags,
                    i.dwSize,
                    i.pcPriClassBase,
                    i.szExeFile,
                    i.th32DefaultHeapID,
                    i.th32ModuleID,
                    i.th32ParentProcessID,
                    i.th32ProcessID,
                ]
            )
        return toreturn

    def SimpleGetProcesses(self):
        toreturn = []
        for i in self.getRawProcesses():
            toreturn.append({"Name": i[5].decode(), "Threads": i[0], "ProcessId": i[9]})
        return toreturn

    def YieldForProgram(self, programName):
        global baseAddr
        ProcessesList = self.SimpleGetProcesses()
        for i in ProcessesList:
            if i["Name"] == programName:
                self.Pymem.open_process_from_id(i["ProcessId"])
                self.ProgramName = programName
                access_rights = 0x1038
                self.Handle = windll.kernel32.OpenProcess(access_rights, False, i["ProcessId"])
                self.is64bit = not is_64_bit(self.Handle)
                self.ProcessID = self.Pymem.process_id
                self.PID = self.ProcessID
                print('Roblox PID:', self.ProcessID)
                for module in hyper.Pymem.list_modules():
                    if module.name == "RobloxPlayerBeta.exe":
                        baseAddr = module.lpBaseOfDll
                print(f'Roblox base addr: {baseAddr:x}')
                return True
        return False

    def isProcessDead(self):
        return not pid_exists(self.ProcessID)

hyper = hyper()
nameOffset = int(offsets['Name'], 16)
childrenOffset = int(offsets['Children'], 16)

def ReadRobloxString(ExpectedAddress: int) -> str:
    StringCount = hyper.Pymem.read_int(ExpectedAddress + 0x10)
    if StringCount > 15:
        shit = hyper.DRP(ExpectedAddress)
        return hyper.Pymem.read_string(shit, StringCount)
    return hyper.Pymem.read_string(ExpectedAddress, StringCount)

def GetClassName(Instance: int) -> str:
    ptr = hyper.Pymem.read_longlong(Instance + 0x18)
    ptr = hyper.Pymem.read_longlong(ptr + 0x8)
    fl = hyper.Pymem.read_longlong(ptr + 0x18)
    if fl == 0x1F:
        ptr = hyper.Pymem.read_longlong(ptr)
    return ReadRobloxString(ptr)

def GetNameAddress(Instance):
    ExpectedAddress = hyper.DRP(Instance + nameOffset, True)
    return ExpectedAddress

def GetName(Instance: int) -> str:
    ExpectedAddress = GetNameAddress(Instance)
    return ReadRobloxString(ExpectedAddress)

def GetChildren(Instance: int) -> str:
    ChildrenInstance = []
    InstanceAddress = Instance
    if not InstanceAddress:
        return False
    ChildrenStart = hyper.DRP(InstanceAddress + childrenOffset, True)
    if ChildrenStart == 0:
        return []
    ChildrenEnd = hyper.DRP(ChildrenStart + 8, True)
    OffsetAddressPerChild = 0x10
    CurrentChildAddress = hyper.DRP(ChildrenStart, True)
    for i in range(0, 9000):
        if CurrentChildAddress == ChildrenEnd:
            break
        ChildrenInstance.append(hyper.Pymem.read_longlong(CurrentChildAddress))
        CurrentChildAddress += OffsetAddressPerChild
    return ChildrenInstance

def FindFirstChild(Instance: int, ChildName: str) -> int:
    ChildrenOfInstance = GetChildren(Instance)
    for i in ChildrenOfInstance:
        if GetName(i) == ChildName:
            return i

def FindFirstChildOfClass(Instance: int, ClassName: str) -> int:
    ChildrenOfInstance = GetChildren(Instance)
    for i in ChildrenOfInstance:
        try:
            if GetClassName(i) == ClassName:
                return i
        except:
            pass

dataModel, wsAddr, lightingAddr, camAddr, fovAddr, startFogAddr, endFogAddr = [0] * 7

def init():
    global dataModel, wsAddr, lightingAddr, camAddr, fovAddr, startFogAddr, endFogAddr
    visEngine = hyper.Pymem.read_longlong(baseAddr + int(offsets['VisualEnginePointer'], 16))
    print(f'Visual engine: {visEngine:x}')
    
    fakeDatamodel = hyper.Pymem.read_longlong(visEngine + int(offsets['VisualEngineToDataModel1'], 16))
    print(f'Fake datamodel: {fakeDatamodel:x}')
    
    dataModel = hyper.Pymem.read_longlong(fakeDatamodel + int(offsets['VisualEngineToDataModel2'], 16))
    print(f'Real datamodel: {dataModel:x}')
    
    wsAddr = hyper.Pymem.read_longlong(dataModel + int(offsets['Workspace'], 16)) #FindFirstChildOfClass(dataModel, 'Workspace')
    print(f'Workspace: {wsAddr:x}')
    
    camAddr = hyper.Pymem.read_longlong(wsAddr + int(offsets['Camera'], 16)) #FindFirstChildOfClass(wsAddr, 'Camera')
    fovAddr = camAddr + int(offsets['FOV'], 16)
    print(f'Camera: {camAddr:x}')
    
    print('Pls wait while we getting lighting...')
    lightingAddr = FindFirstChildOfClass(dataModel, 'Lighting')
    
    startFogAddr = lightingAddr + int(offsets['FogStart'], 16)
    endFogAddr = lightingAddr + int(offsets['FogEnd'], 16)
    print(f'Lighting service: {lightingAddr:x}')
    
    print('Injected successfully\n-------------------------------')

startTime = 0
startTime2 = 0
humAddr = 0

#hrpYaddr = 0
hrpGravAddr = 0
#hrpYvel = 0

#flyEnabled = False

oldSpeed = '0'
oldJp = '0'
oldEsp = False

def getHumAddr():
    global humAddr, startTime
    if time()-startTime > 10:
        humAddr = hyper.Pymem.read_longlong(camAddr + int(offsets['CameraSubject'], 16)) #By default camera subject will be humanoid. Shortening path from game.Players.LocalPlayer.Character.Humanoid to workspace.CurrentCamera.CameraSubject
    startTime = time()
def getHrpGravAddr():
    global hrpGravAddr, humAddr, startTime, startTime2
    if time()-startTime2 > 10:
        humAddr = hyper.Pymem.read_longlong(camAddr + int(offsets['CameraSubject'], 16))
        char = hyper.Pymem.read_longlong(humAddr + int(offsets['Parent'], 16))
        hrp = FindFirstChild(char, 'HumanoidRootPart')
        primitive = hyper.Pymem.read_longlong(hrp + int(offsets['Primitive'], 16))
        hrpGravAddr = primitive + int(offsets['PrimitiveGravity'], 16)
    startTime = time()
    startTime2 = startTime

def afterDeath():
    oldHumAddr = 0
    while camAddr == 0:
        sleep(1)

    while True:
        if window.AfterDeathApply.isChecked():
            hum = hyper.Pymem.read_longlong(camAddr + int(offsets['CameraSubject'], 16))
            if oldHumAddr != hum:
                hyper.Pymem.write_float(hum + int(offsets['WalkSpeedCheck'], 16), float('inf'))
                hyper.Pymem.write_float(hum + int(offsets['WalkSpeed'], 16), float(window.Speed.value()))
                print('Wrote speed')
                hyper.Pymem.write_float(hum + int(offsets['JumpPower'], 16), float(window.Jumppower.value()))
                print('Wrote jump power')
                if window.ESP.isChecked() == 1:
                    hyper.Pymem.write_int(hum + 0x1B8, int(0))
                    hyper.Pymem.write_float(hum + 0x1B4, float('inf'))
                    hyper.Pymem.write_float(hum + 0x190, float('inf'))
                    print('Wrote ESP')
                oldHumAddr = hum
        sleep(1)
Thread(target=afterDeath, daemon=True).start()

def apply():
    global oldSpeed, oldJp, oldEsp
    getHumAddr()

    if window.Jumppower.value() != oldJp:
        hyper.Pymem.write_float(humAddr + int(offsets['JumpPower'], 16), float(window.Jumppower.value()))
        print('Wrote jump power')
        oldJp = window.Jumppower.value()
    
    if window.Speed.value() != oldSpeed:
        hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
        hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeed'], 16), float(window.Speed.value()))
        print('Wrote speed')
        oldSpeed = window.Speed.value()

    if window.ESP.isChecked() != oldEsp:
        if window.ESP.isChecked():
            hyper.Pymem.write_int(humAddr + 0x1B8, int(0))
            hyper.Pymem.write_float(humAddr + 0x1B4, float('inf'))
            hyper.Pymem.write_float(humAddr + 0x190, float('inf'))
        else:
            hyper.Pymem.write_int(humAddr + 0x1B8, int(2))
            hyper.Pymem.write_float(humAddr + 0x1B4, float(100))
            hyper.Pymem.write_float(humAddr + 0x190, float(100))
        print('Wrote ESP')
        oldEsp = window.ESP.isChecked()

def delFog():
    print('Removing fog...')
    ChildrenOfInstance = GetChildren(lightingAddr)
    print('Got children of lighting service!')
    for i in ChildrenOfInstance:
        try:
            if GetClassName(i) == 'Atmosphere':
                hyper.Pymem.write_float(i+0xE0, float(0))
                hyper.Pymem.write_float(i+0xE8, float(0))
                print('Wrote atmosphere')
        except:
            pass
    
    hyper.Pymem.write_float(endFogAddr, float('inf'))
    hyper.Pymem.write_float(startFogAddr, float('inf'))
    print('Fog removed')

def reEnableEspKeyBind(event):
    if event.name == 'right ctrl':
        if window.ESP.isChecked():
            getHumAddr()
            hyper.Pymem.write_int(humAddr+0x1B8, int(0))
            hyper.Pymem.write_float(humAddr+0x1B4, float('inf'))
            hyper.Pymem.write_float(humAddr+0x190, float('inf'))
            print('Wrote ESP')

def reEnableEsp():
    getHumAddr()
    hyper.Pymem.write_int(humAddr+0x1B8, int(0))
    hyper.Pymem.write_float(humAddr+0x1B4, float('inf'))
    hyper.Pymem.write_float(humAddr+0x190, float('inf'))
    print('Wrote ESP')

def reOpenRoblox():
    while True:
        if hyper.isProcessDead():
            try:
                while not hyper.YieldForProgram("RobloxPlayerBeta.exe"):
                    pass
            except:
                pass
        sleep(0.1)

'''def flyToogle(state):
    global hrpYaddr, hrpGravAddr, hrpYvel, flyEnabled
    if state == 2:
        getHumAddr()
        char = hyper.Pymem.read_longlong(humAddr + int(offsets['Parent'], 16))
        hrp = FindFirstChild(char, 'HumanoidRootPart')
        primitive = hyper.Pymem.read_longlong(hrp + int(offsets['Primitive'], 16))
        hrpGravAddr = primitive + int(offsets['PrimitiveGravity'], 16)
        hyper.Pymem.write_float(hrpGravAddr, float(0))
        shit = hyper.Pymem.read_longlong(primitive+0x98)
        hrpYaddr = shit+0x88
        hrpYvel = shit+0x94
        hyper.Pymem.write_float(hrpYaddr, float(hyper.Pymem.read_float(hrpYaddr) + 5))
        hyper.Pymem.write_float(hrpYvel, float(0))
        flyEnabled = True
        print('Fly enabled')
    elif state == 0:
        hyper.Pymem.write_float(hrpGravAddr, float(196.2))
        flyEnabled = True
        print('Fly disabled')

def flyUp():
    if flyEnabled:
        hyper.Pymem.write_float(hrpYvel, float(0))
        hyper.Pymem.write_float(hrpYaddr, float(hyper.Pymem.read_float(hrpYaddr) + float(window.Step.value())))

def flyDown():
    if flyEnabled:
        hyper.Pymem.write_float(hrpYvel, float(0))
        hyper.Pymem.write_float(hrpYaddr, float(hyper.Pymem.read_float(hrpYaddr) - float(window.Step.value())))'''

def fovChange(val):
    hyper.Pymem.write_float(fovAddr, float(val))
    print('Wrote FOV')

def gravChange(val):
    getHrpGravAddr()
    hyper.Pymem.write_float(hrpGravAddr, float(val))
    print('Wrote grav')

def resetChr():
    getHumAddr()
    hyper.Pymem.write_float(humAddr + int(offsets['Health'], 16), float(0))

def reEnableEspBtnToogle(state):
    if state == 2:
        window.ReEsp.show()
    elif state == 0:
        window.ReEsp.hide()

Thread(target=reOpenRoblox, daemon=True).start()
on_release(reEnableEspKeyBind)

print('Inited! Creating GUI...')

app = QApplication([])
window = MyApp()
window.INJECT.clicked.connect(init)
window.Apply.clicked.connect(apply)
window.DelFog.clicked.connect(delFog)
#window.FlyToogle.stateChanged.connect(flyToogle)
#window.FlyUp.clicked.connect(flyUp)
#window.FlyDown.clicked.connect(flyDown)
window.FOV.valueChanged.connect(fovChange)
window.Gravity.valueChanged.connect(gravChange)
window.Reset.clicked.connect(resetChr)
window.ReEsp.clicked.connect(reEnableEsp)
window.ESP.stateChanged.connect(reEnableEspBtnToogle)
window.show()

def loops():
    while True:
        if window.LoopSetFOV.isChecked():
            hyper.Pymem.write_float(fovAddr, float(window.FOV.value()))
        sleep(1)

Thread(target=loops, daemon=True).start()

app.exec_()