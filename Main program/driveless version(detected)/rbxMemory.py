from pymem import Pymem
from pymem.process import is_64_bit, list_processes
from ctypes import windll
from psutil import pid_exists

Handle = None
PID = -1
baseAddr = None
pm = Pymem()

def DRP(address: int | str) -> int:
    if isinstance(address, str):
        address = int(address, 16)
    return int.from_bytes(pm.read_bytes(address, 8), "little")

def get_raw_processes():
    return [[
        i.cntThreads, i.cntUsage, i.dwFlags, i.dwSize,
        i.pcPriClassBase, i.szExeFile, i.th32DefaultHeapID,
        i.th32ModuleID, i.th32ParentProcessID, i.th32ProcessID
    ] for i in list_processes()]

def simple_get_processes():
    return [{"Name": i[5].decode(), "Threads": i[0], "ProcessId": i[9]} for i in get_raw_processes()]

def yield_for_program(program_name: str, printInfo: bool = True) -> bool:
    global PID, Handle, baseAddr, pm
    for proc in simple_get_processes():
        if proc["Name"] == program_name:
            pm.open_process_from_id(proc["ProcessId"])
            PID = proc["ProcessId"]
            Handle = windll.kernel32.OpenProcess(0x1038, False, PID)
            if printInfo:
                print('Roblox PID:', PID)
            for module in pm.list_modules():
                if module.name == "RobloxPlayerBeta.exe":
                    baseAddr = module.lpBaseOfDll
                    break
            if printInfo:
                print(f'Roblox base addr: {baseAddr:x}')
            return True
    return False

def is_process_dead() -> bool:
    return not pid_exists(PID)

def get_base_addr() -> int:
    return baseAddr

def setOffsets(nameOffset2: int, childrenOffset2: int):
    global nameOffset, childrenOffset
    nameOffset = nameOffset2
    childrenOffset = childrenOffset2

def ReadRobloxString(expected_address: int) -> str:
    string_count = pm.read_int(expected_address + 0x10)
    if string_count > 15:
        ptr = DRP(expected_address)
        return pm.read_string(ptr, string_count)
    return pm.read_string(expected_address, string_count)

def GetClassName(instance: int) -> str:
    ptr = pm.read_longlong(instance + 0x18)
    ptr = pm.read_longlong(ptr + 0x8)
    fl = pm.read_longlong(ptr + 0x18)
    if fl == 0x1F:
        ptr = pm.read_longlong(ptr)
    return ReadRobloxString(ptr)

def GetNameAddress(instance: int) -> int:
    return DRP(instance + nameOffset)

def GetName(instance: int) -> str:
    return ReadRobloxString(GetNameAddress(instance))

def GetChildren(instance: int) -> list:
    if not instance:
        return []
    children = []
    start = DRP(instance + childrenOffset)
    if start == 0:
        return []
    end = DRP(start + 8)
    current = DRP(start)
    for _ in range(9000):
        if current == end:
            break
        children.append(pm.read_longlong(current))
        current += 0x10
    return children

def FindFirstChild(instance: int, child_name: str) -> int:
    for child in GetChildren(instance):
        if GetName(child) == child_name:
            return child

def FindFirstChildOfClass(instance: int, class_name: str) -> int:
    for child in GetChildren(instance):
        try:
            if GetClassName(child) == class_name:
                return child
        except:
            pass
