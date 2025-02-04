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
        
        if is64Bit:
            return int.from_bytes(self.Pymem.read_bytes(Address, 8), "little")
        if self.is64bit:
            return int.from_bytes(self.Pymem.read_bytes(Address, 8), "little")
        return int.from_bytes(self.Pymem.read_bytes(Address, 4), "little")

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
                print('Roblox base addr:', baseAddr)
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
        return hyper.Pymem.read_string(hyper.DRP(ExpectedAddress), StringCount)
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

data_model, wsAddr, lightingAddr, camAddr, fovAddr, startFogAddr, endFogAddr = [0] * 7

def init():
    global data_model, wsAddr, lightingAddr, camAddr, fovAddr, startFogAddr, endFogAddr
    fake_datamodel = hyper.Pymem.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16)) #We cant get real datamodel, so getting it from fake datamodel
    print('Fake datamodel:', fake_datamodel)
    data_model = hyper.Pymem.read_longlong(fake_datamodel + int(offsets['FakeDataModelToDataModel'], 16))
    print('Real datamodel:', data_model)
    wsAddr = hyper.Pymem.read_longlong(data_model + int(offsets['Workspace'], 16)) #FindFirstChildOfClass(data_model, 'Workspace')
    print('Workspace:', wsAddr)
    camAddr = hyper.Pymem.read_longlong(wsAddr + int(offsets['Camera'], 16)) #FindFirstChildOfClass(wsAddr, 'Camera')
    fovAddr = camAddr + int(offsets['FOV'], 16)
    print('Camera:', camAddr)
    print('Pls wait while we getting lighting...')
    lightingAddr = FindFirstChildOfClass(data_model, 'Lighting')
    startFogAddr = lightingAddr + int(offsets['FogStart'], 16)
    endFogAddr = lightingAddr + int(offsets['FogEnd'], 16)
    print('Lighting service:', lightingAddr)
    print('Injected successfully')

startTime = 0
humAddr = 0

oldSpeed = '0'
oldJp = '0'
oldFov = '0'
oldEsp = False

def getHumAddr():
    global humAddr, startTime
    if time()-startTime > 10:
        humAddr = hyper.Pymem.read_longlong(camAddr + int(offsets['CameraSubject'], 16)) #By default camera subject will be humanoid. Shortening path from game.Players.LocalPlayer.Character.Humanoid to workspace.CurrentCamera.CameraSubject
        startTime = time()

def afterDeath():
    oldHumAddr = 0
    while camAddr == 0:
        sleep(1)
    print('W')
    while True:
        if window.AfterDeathApply.isChecked():
            hum = hyper.Pymem.read_longlong(camAddr + int(offsets['CameraSubject'], 16))
            if oldHumAddr != hum:
                hyper.Pymem.write_float(hum + int(offsets['WalkSpeedCheck'], 16), float('inf'))
                hyper.Pymem.write_float(hum + int(offsets['WalkSpeed'], 16), float(window.Speed.text()))
                print('Wrote speed')
                hyper.Pymem.write_float(hum + int(offsets['JumpPower'], 16), float(window.Jumppower.text()))
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
    global oldSpeed, oldJp, oldFov, oldEsp
    getHumAddr()

    if window.FOV.text() != oldFov:
        hyper.Pymem.write_float(fovAddr, float(window.FOV.text()))
        print('Wrote FOV')
        oldFov = window.FOV.text()

    if window.Jumppower.text() != oldJp:
        hyper.Pymem.write_float(humAddr + int(offsets['JumpPower'], 16), float(window.Jumppower.text()))
        print('Wrote jump power')
        oldJp = window.Jumppower.text()
    
    if window.Speed.text() != oldSpeed:
        hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
        hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeed'], 16), float(window.Speed.text()))
        print('Wrote speed')
        oldSpeed = window.Speed.text()

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
                hyper.Pymem.write_float(i+0xE0, float('0'))
                hyper.Pymem.write_float(i+0xE8, float('0'))
                print('Wrote atmosphere')
        except:
            pass
    
    hyper.Pymem.write_float(endFogAddr, float('inf'))
    hyper.Pymem.write_float(startFogAddr, float('inf'))
    print('Fog removed')

def reEnableEsp(event):
    if event.name == 'right ctrl':
        if window.ESP.isChecked():
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

Thread(target=reOpenRoblox, daemon=True).start()
on_release(reEnableEsp)

print('Inited! Creating GUI...')

app = QApplication([])
window = MyApp()
window.INJECT.clicked.connect(init)
window.Apply.clicked.connect(apply)
window.DelFog.clicked.connect(delFog)
window.show()

def loops():
    while True:
        if window.LoopSetFOV.isChecked():
            hyper.Pymem.write_float(fovAddr, float(window.FOV.text()))
        sleep(1)

Thread(target=loops, daemon=True).start()
app.exec_()
