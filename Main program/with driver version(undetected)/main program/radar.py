print('Radar starting...')
from math import atan2, cos, sin, pi
from rbxMemory import *
from tkinter import Tk, Canvas
from sys import stdin, argv
from threading import Thread
from time import sleep
HalfPi = pi/2

WINDOW_SIZE = 300
TARGET_COUNT = 5
BORDER_PADDING = 0

windowCenter = WINDOW_SIZE/2

scale = 2

rbxColors = {
    1: "#F2F3F3",
    2: "#A1A5A2",
    3: "#F9E999",
    5: "#D7C59A",
    6: "#C2DAB8",
    9: "#E8BAC8",
    11: "#80BBDB",
    12: "#CB8442",
    18: "#CC8E69",
    21: "#C4281C",
    22: "#C470A0",
    23: "#0D69AC",
    24: "#F5CD30",
    25: "#624732",
    26: "#1B2A35",
    27: "#6D6E6C",
    28: "#287F47",
    29: "#A1C48C",
    36: "#F3CF9B",
    37: "#4B974B",
    38: "#A05F35",
    39: "#C1CADE",
    40: "#ECECEC",
    41: "#CD544B",
    42: "#C1DFF0",
    43: "#7BB6E8",
    44: "#F7F18D",
    45: "#B4D2E4",
    47: "#D9856C",
    48: "#84B68D",
    49: "#F8F184",
    50: "#ECE8DE",
    100: "#EEC4B6",
    101: "#DA867A",
    102: "#6E99CA",
    103: "#C7C1B7",
    104: "#6B327C",
    105: "#E29B40",
    106: "#DA8541",
    107: "#008F9C",
    108: "#685C43",
    110: "#435493",
    111: "#BFB7B1",
    112: "#6874AC",
    113: "#E5ADC8",
    115: "#C7D23C",
    116: "#55A5AF",
    118: "#B7D7D5",
    119: "#A4BD47",
    120: "#D9E4A7",
    121: "#E7AC58",
    123: "#D36F4C",
    124: "#923978",
    125: "#EAB892",
    126: "#A5A5CB",
    127: "#DCBC81",
    128: "#AE7A59",
    131: "#9CA3A8",
    133: "#D5733D",
    134: "#D8DD56",
    135: "#74869D",
    136: "#877C90",
    137: "#E09864",
    138: "#958A73",
    140: "#203A56",
    141: "#27462D",
    143: "#CFE2F7",
    145: "#7988A1",
    146: "#958EA3",
    147: "#938767",
    148: "#575857",
    149: "#161D32",
    150: "#ABADAC",
    151: "#789082",
    153: "#957979",
    154: "#7B2E2F",
    157: "#FFF67B",
    158: "#E1A4C2",
    168: "#756C62",
    176: "#97695B",
    178: "#B48455",
    179: "#898787",
    180: "#D7A94B",
    190: "#F9D62E",
    191: "#E8AB2D",
    192: "#694028",
    193: "#CF6024",
    194: "#A3A2A5",
    195: "#4667A4",
    196: "#23478B",
    198: "#8E4285",
    199: "#635F62",
    200: "#828A5D",
    208: "#E5E4DF",
    209: "#B08E44",
    210: "#709578",
    211: "#79B5B5",
    212: "#9FC3E9",
    213: "#6C81B7",
    216: "#904C2A",
    217: "#7C5C46",
    218: "#96709F",
    219: "#6B629B",
    220: "#A7A9CE",
    221: "#CD6298",
    222: "#E4ADC8",
    223: "#DC9095",
    224: "#F0D5A0",
    225: "#EBB87F",
    226: "#FDEA8D",
    232: "#7DBBDD",
    268: "#342B75",
    301: "#506D54",
    302: "#5B5D69",
    303: "#0010B0",
    304: "#2C651D",
    305: "#527CAE",
    306: "#335882",
    307: "#102ADC",
    308: "#3D1585",
    309: "#348E40",
    310: "#5B9A4C",
    311: "#9FA1AC",
    312: "#592259",
    313: "#1F801D",
    314: "#9FADC0",
    315: "#0989CF",
    316: "#7B007B",
    317: "#7C9C6B",
    318: "#8AAB85",
    319: "#B9C4B1",
    320: "#CACBD1",
    321: "#A75E9B",
    322: "#7B2F7B",
    323: "#94BE81",
    324: "#A8BD99",
    325: "#DFDFDE",
    327: "#970000",
    328: "#B1E5A6",
    329: "#98C2DB",
    330: "#FF98DC",
    331: "#FF5959",
    332: "#750000",
    333: "#EFB838",
    334: "#F8D96D",
    335: "#E7E7EC",
    336: "#C7D4E4",
    337: "#FF9494",
    338: "#BE6862",
    339: "#562424",
    340: "#F1E7C7",
    341: "#FEF3BB",
    342: "#E0B2D0",
    343: "#D490BD",
    344: "#965555",
    345: "#8F4C2A",
    346: "#D3BE96",
    347: "#E2DCBC",
    348: "#EDEAEA",
    349: "#E9DADA",
    350: "#883E3E",
    351: "#BC9B5D",
    352: "#C7AC78",
    353: "#CABFA3",
    354: "#BBB3B2",
    355: "#6C584B",
    356: "#A0844F",
    357: "#958988",
    358: "#ABA89E",
    359: "#AF9483",
    360: "#966766",
    361: "#564236",
    362: "#7E683F",
    363: "#69665C",
    364: "#5A4C42",
    365: "#6A3909",
    1001: "#F8F8F8",
    1002: "#CDCDCD",
    1003: "#111111",
    1004: "#FF0000",
    1005: "#FFB000",
    1006: "#B080FF",
    1007: "#A34B4B",
    1008: "#C1BE42",
    1009: "#FFFF00",
    1010: "#0000FF",
    1011: "#002060",
    1012: "#2154B9",
    1013: "#04AFEC",
    1014: "#AA5500",
    1015: "#AA00AA",
    1016: "#FF66CC",
    1017: "#FFAF00",
    1018: "#12EED4",
    1019: "#00FFFF",
    1020: "#00FF00",
    1021: "#3A7D15",
    1022: "#7F8E64",
    1023: "#8C5B9F",
    1024: "#AFDDFF",
    1025: "#FFC9C9",
    1026: "#B1A7FF",
    1027: "#9FF3E9",
    1028: "#CCFFCC",
    1029: "#FFFFCC",
    1030: "#FFCC99",
    1031: "#6225D1",
    1032: "#FF00BF"
}

def draw_radar():
    global lpX, lpY
    if lpAddr == 0 or plrsAddr == 0 or camLVAddr == 0:
        return
    canvas.delete("all")

    canvas.create_rectangle(0, 0, WINDOW_SIZE, WINDOW_SIZE, fill="black", outline="")

    char = read_int8(lpAddr + modelInstanceOffset)
    try:
        hrp = FindFirstChild(char, 'HumanoidRootPart')
        if hrp is not None and hrp > 0:
            primitive = read_int8(hrp + primitiveOffset)
            lpX = read_float(primitive + positionOffset)
            lpY = read_float(primitive + positionOffset + 8)
    except OSError:
        pass

    color = 'red'
    lpTeam = read_int8(lpAddr + teamOffset)
    if lpTeam > 0:
        color = rbxColors[read_int4(lpTeam + teamColorOffset)]

    center_size = 2
    canvas.create_oval(
        windowCenter - center_size, windowCenter - center_size,
        windowCenter + center_size, windowCenter + center_size,
        fill=color, outline=""
    )

    camLVX = read_float(camLVAddr)
    camLVZ = read_float(camLVAddr + 8)
    camRot = atan2(camLVX, -camLVZ) - HalfPi
    cos_a = cos(camRot)
    sin_a = sin(camRot)

    for v in GetChildren(plrsAddr):
        try:
            if v == lpAddr:
                continue
            team = read_int8(v + teamOffset)
            if not ignoreTeam or team != lpTeam:
                char = read_int8(v + modelInstanceOffset)

                if ignoreDead:
                    hum = FindFirstChildOfClass(char, 'Humanoid')
                    if hum == 0 or hum is None or read_float(hum + healthOffset) <= 0:
                        continue

                hrp = FindFirstChild(char, 'HumanoidRootPart')
                if hrp == 0 or hrp is None:
                    continue

                primitive = read_int8(hrp + primitiveOffset)
                x = read_float(primitive + positionOffset) - lpX
                y = read_float(primitive + positionOffset + 8) - lpY

                dx = x / scale
                dy = y / scale
                x = dx * cos_a - dy * sin_a
                y = dx * sin_a + dy * cos_a

                if -WINDOW_SIZE <= x <= WINDOW_SIZE and -WINDOW_SIZE <= y <= WINDOW_SIZE:
                    x = windowCenter + x
                    y = windowCenter + y
                    color = 'blue'
                    if team > 0:
                        color = rbxColors[read_int4(team + teamColorOffset)]

                    canvas.create_oval(
                        x - 2, y - 2, x + 2, y + 2,
                        fill=color, outline=""
                    )
        except OSError:
            pass

hidden = True
ignoreDead = False
ignoreTeam = False

def signalHandler():
    global lpAddr, camLVAddr, plrsAddr, hidden, ignoreTeam, ignoreDead
    while True:
        for line in stdin:
            line = line.strip()
            if line == 'toogle1':
                hidden = not hidden
                if hidden:
                    root.withdraw()
                else:
                    root.deiconify()
            elif line == 'toogle2':
                ignoreTeam = not ignoreTeam
            elif line == 'toogle3':
                ignoreDead = not ignoreDead
            elif line.startswith('addrs'):
                addrs = line[5:].split(',')
                lpAddr = int(addrs[0])
                camLVAddr = int(addrs[1])
                plrsAddr = int(addrs[2])
            elif line.startswith('desc'):
                line = line[4:]
                setPid(int(line))

Thread(target=signalHandler,daemon=True).start()

def update_frame():
    if hidden:
        sleep(1)
    else:
        draw_radar()
    root.after_idle(update_frame)

root = Tk()
root.overrideredirect(True)
root.attributes('-topmost', True)
root.attributes('-alpha', 0.85)

screen_width = root.winfo_screenwidth()
x_pos = screen_width - WINDOW_SIZE
root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}+{x_pos}+0")

canvas = Canvas(root, width=WINDOW_SIZE, height=WINDOW_SIZE, bg="black", highlightthickness=0)
canvas.pack()
root.update_idletasks()

def on_mouse_wheel(event):
    global scale
    if event.delta > 0:
        if scale > 0.1:
            scale -= 0.1
    else:
        scale += 0.1
args = argv[1:]

modelInstanceOffset = int(args[0])
primitiveOffset = int(args[1])
positionOffset = int(args[2])
teamOffset = int(args[3])
teamColorOffset = int(args[4])
healthOffset = int(args[5])
setOffsets(int(args[6]), int(args[7]))
open_device()
lpAddr = 0
camLVAddr = 0
plrsAddr = 0

root.bind("<MouseWheel>", on_mouse_wheel)
root.withdraw()
update_frame()
print('Radar started')
root.mainloop()
