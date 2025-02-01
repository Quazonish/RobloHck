print('Loading libs...')
from pymem import Pymem
from pymem.process import is_64_bit, list_processes
from ctypes import windll
from psutil import pid_exists
from tkinter import Tk, Entry, Button, Checkbutton, IntVar
from tkinter.font import Font
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
nameOffset = 104
childrenOffset = 112

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

data_model, wsAddr, camAddr, fovAddr = [0] * 4

def init():
    global data_model, wsAddr, camAddr, fovAddr
    fake_datamodel = hyper.Pymem.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16)) #We cant get real datamodel, so getting it from fake datamodel
    print('Fake datamodel:', fake_datamodel)
    data_model = hyper.Pymem.read_longlong(fake_datamodel + int(offsets['FakeDataModelToDataModel'], 16))
    print('Real datamodel:', data_model)
    wsAddr = hyper.Pymem.read_longlong(data_model + int(offsets['Workspace'], 16)) #FindFirstChildOfClass(data_model, 'Workspace')
    print('Workspace:', wsAddr)
    camAddr = hyper.Pymem.read_longlong(wsAddr + int(offsets['Camera'], 16)) #FindFirstChildOfClass(data_model, 'Camera')
    print('Camera:', camAddr)
    fovAddr = camAddr + 320

startTime = 0
humAddr = 0

oldSpeed = '0'
oldJp = '0'
oldFov = '0'
oldEsp = 0

def getHumAddr():
    global humAddr, startTime
    if time()-startTime > 10:
        humAddr = hyper.Pymem.read_longlong(camAddr + int(offsets['CameraSubject'], 16)) #By default camera subject will be humanoid. Shortening path from game.Players.LocalPlayer.Character.Humanoid to workspace.CurrentCamera.CameraSubject
        startTime = time()

'''def setSpeed():
    getHumAddr()
    hyper.Pymem.write_float(humAddr + 928, float('inf'))
    hyper.Pymem.write_float(humAddr + 456, float(speed_lbl.get()))

def setJP():
    getHumAddr()
    hyper.Pymem.write_float(humAddr + 424, float(jp_lbl.get()))

def setFOV():
    hyper.Pymem.write_float(camAddr + 320, float(fov_lbl.get()))

def espToggle():
    getHumAddr()
    if checkbox_var.get() == 1:
        hyper.Pymem.write_int(humAddr + 0x1B8, int(0))
        hyper.Pymem.write_float(humAddr+0x1B4, float('inf'))
        hyper.Pymem.write_float(humAddr+0x190, float('inf'))
    else:
        hyper.Pymem.write_int(humAddr+0x1B8, int(2))
        hyper.Pymem.write_float(humAddr+0x1B4, float(100))
        hyper.Pymem.write_float(humAddr+0x190, float(100))'''

def afterDeath():
    oldHumAddr = 0
    while camAddr == 0:
        sleep(1)
    while True:
        if checkbox_var3.get() == 1:
            hum = hyper.Pymem.read_longlong(camAddr + int(offsets['CameraSubject'], 16))
            if oldHumAddr != hum:
                hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
                hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeed'], 16), float(speed_lbl.get()))
                print('Wrote speed')
                hyper.Pymem.write_float(humAddr + int(offsets['JumpPower'], 16), float(jp_lbl.get()))
                print('Wrote jump power')
                if checkbox_var.get() == 1:
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

    if fov_lbl.get() != oldFov:
        hyper.Pymem.write_float(fovAddr, float(fov_lbl.get()))
        print('Wrote FOV')
        oldFov = fov_lbl.get()

    if jp_lbl.get() != oldJp:
        hyper.Pymem.write_float(humAddr + int(offsets['JumpPower'], 16), float(jp_lbl.get()))
        print('Wrote jump power')
        oldJp = jp_lbl.get()
    
    if speed_lbl.get() != oldSpeed:
        hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeedCheck'], 16), float('inf'))
        hyper.Pymem.write_float(humAddr + int(offsets['WalkSpeed'], 16), float(speed_lbl.get()))
        print('Wrote speed')
        oldSpeed = speed_lbl.get()

    if checkbox_var.get() != oldEsp:
        if checkbox_var.get() == 1:
            hyper.Pymem.write_int(humAddr + 0x1B8, int(0))
            hyper.Pymem.write_float(humAddr + 0x1B4, float('inf'))
            hyper.Pymem.write_float(humAddr + 0x190, float('inf'))
        else:
            hyper.Pymem.write_int(humAddr + 0x1B8, int(2))
            hyper.Pymem.write_float(humAddr + 0x1B4, float(100))
            hyper.Pymem.write_float(humAddr + 0x190, float(100))
        print('Wrote ESP')
        oldEsp = checkbox_var.get()

def reEnableEsp(event):
    if event.name == 'right ctrl':
        if checkbox_var.get() == 1:
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

form = Tk()
form.geometry("290x170")
form.title("Roblox trainer")
form.config(bg="black")
form.attributes('-alpha', 0.9)

form.resizable(False, False)

#-----------------------------------------------------------------------------------------

btn_scan = Button(form, text="INJECT", command=init, bg="red4", fg="whitesmoke")
btn_scan.place(x=10, y=10, width=130, height=35)
btn_scan_font = Font(size=20, weight='bold')
btn_scan['font'] = btn_scan_font

btn_apply = Button(form, text="Apply", command=apply, bg="blue4", fg="whitesmoke")
btn_apply.place(x=150, y=10, width=130, height=35)
btn_apply_font = Font(size=20, weight='bold')
btn_apply['font'] = btn_apply_font

#-----------------------------------------------------------------------------------------

speed_lbl = Entry(form, bg="black", fg="whitesmoke", justify='center')
speed_lbl.place(x=10, y=50, width=130, height=35)
speed_lbl.insert(0, "25")

#btn_set_speed = Button(form, text="Set speed", command=setSpeed, bg="black", fg="whitesmoke")
#btn_set_speed.place(x=150, y=50, width=130, height=35)

#-----------------------------------------------------------------------------------------

jp_lbl = Entry(form, bg="black", fg="whitesmoke", justify='center')
jp_lbl.place(x=150, y=50, width=130, height=35)
jp_lbl.insert(0, "70")

#btn_set_jp = Button(form, text="Set jump power", command=setJP, bg="black", fg="whitesmoke")
#btn_set_jp.place(x=150, y=90, width=130, height=35)

#-----------------------------------------------------------------------------------------

fov_lbl = Entry(form, bg="black", fg="whitesmoke", justify='center')
fov_lbl.place(x=10, y=90, width=130, height=35)
fov_lbl.insert(0, "1.5")

#btn_set_fov = Button(form, text="Set FOV", command=setFOV, bg="black", fg="whitesmoke")
#btn_set_fov.place(x=150, y=130, width=130, height=35)

#-----------------------------------------------------------------------------------------

checkbox_var = IntVar()
checkbox = Checkbutton(form, text="Enable ESP", variable=checkbox_var, bg="black", fg="whitesmoke", selectcolor="black", activebackground="gray10", activeforeground="white", highlightthickness=0)
checkbox.place(x=150, y=90, width=130, height=35)

#-----------------------------------------------------------------------------------------

checkbox_var2 = IntVar()
checkbox2 = Checkbutton(form, text="Loop set FOV", variable=checkbox_var2, bg="black", fg="whitesmoke", selectcolor="black", activebackground="gray10", activeforeground="white", highlightthickness=0)
checkbox2.place(x=10, y=130, width=130, height=35)

#-----------------------------------------------------------------------------------------

checkbox_var3 = IntVar()
checkbox3 = Checkbutton(form, text="After death apply", variable=checkbox_var3, bg="black", fg="whitesmoke", selectcolor="black", activebackground="gray10", activeforeground="white", highlightthickness=0)
checkbox3.place(x=150, y=130, width=130, height=35)

#-----------------------------------------------------------------------------------------

def loopFOV():
    while True:
        if checkbox_var2.get() == 1:
            hyper.Pymem.write_float(fovAddr, float(fov_lbl.get()))
        sleep(1)

Thread(target=loopFOV, daemon=True).start()

form.mainloop()
