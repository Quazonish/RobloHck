print('ESP starting...')
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from OpenGL.GL import *
from numpy import array, float32, empty, einsum
from ctypes import windll, byref, Structure, wintypes
from rbxMemory import *
from sys import argv, stdin
from threading import Thread
from time import time, sleep
from struct import unpack_from
import ctypes

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20

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

class ESPOverlay(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.resize(1920, 1080)
        self.humOffsetCached = 0
        self.headOffsetCached = 0
        self.time = 0

        self.plr_data = []
        self.last_matrix = None
        self.prev_geometry = (0, 0, 0, 0)
        self.color = 'white'
        hwnd = self.winId().__int__()
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(3.0)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        if hidden:
            return
        
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        for x, y, color in self.plr_data:
            r, g, b = QColor(color).redF(), QColor(color).greenF(), QColor(color).blueF()

            glColor3f(r, g, b)
            glBegin(GL_LINES)
            glVertex2f(self.startLineX, self.startLineY)
            glVertex2f(x, y)

            glEnd()

    def update_players(self):
        self.plr_data.clear()

        if lpAddr == 0 or plrsAddr == 0 or matrixAddr == 0:
            sleep(1)
            return

        if hidden:
            sleep(1)
            return

        if self.signalsBlocked():
            sleep(0.1)
            return

        vecs_np = empty((50, 4), dtype=float32)
        count = 0

        if time() - self.time > 1:
            hwnd_roblox = find_window_by_title("Roblox")
            if hwnd_roblox:
                x, y, r, b = get_client_rect_on_screen(hwnd_roblox)
                new_geom = (x, y, r - x, b - y)
                if new_geom != self.prev_geometry:
                    self.setGeometry(*new_geom)
                    self.prev_geometry = new_geom
                    self.startLineX = self.width() / 2
                    self.startLineY = self.height() - self.height() / 20
            self.time = time()

        matrixRaw = read(matrixAddr, 64)
        
        view_proj_matrix = array(unpack_from("<16f", matrixRaw, 0), dtype=float32).reshape(4, 4)

        for head in heads:
            try:
                className = GetClassName(head)
                if GetName(head) == 'Head' and (className == 'Part' or className == 'BasePart' or className == 'MeshPart'):
                    vecs_np[count, :3] = unpack_from("<fff", read(read_int8(head + primitiveOffset) + positionOffset, 12), 0)
                    vecs_np[count, 3] = 1.0
                    count += 1
                else:
                    vecs_np[count, :3] = 0, 0, 0
                    vecs_np[count, 3] = 1.0
                    count += 1
            except OSError:
                vecs_np[count, :3] = 0, 0, 0
                vecs_np[count, 3] = 1.0
                count += 1

        if count == 0:
            return

        clip_coords = einsum('ij,nj->ni', view_proj_matrix, vecs_np[:count])
        for idx, clip in enumerate(clip_coords):
            if clip[3] != 0:
                ndc = clip[:3] / clip[3]
                if 0 <= ndc[2] <= 1:
                    x = int((ndc[0] + 1) * 0.5 * self.width())
                    y = int((1 - ndc[1]) * 0.5 * self.height())
                    try:
                        self.color = colors[idx]
                    except IndexError:
                        pass
                    self.plr_data.append((x, y, self.color))

        self.update()
hidden = True
def signalHandler():
    global lpAddr, matrixAddr, plrsAddr, ignoreTeam, ignoreDead, hidden
    while True:
        for line in stdin:
            line = line.strip()
            if line.startswith('addrs'):
                addrs = line[5:].split(',')
                lpAddr = int(addrs[0])
                matrixAddr = int(addrs[1])
                plrsAddr = int(addrs[2])
            elif line.startswith('desc'):
                setPid(int(line[4:]))
            elif line == 'toogle1':
                hidden = not hidden
            elif line == 'toogle2':
                ignoreTeam = not ignoreTeam
            elif line == 'toogle3':
                ignoreDead = not ignoreDead

heads = []
colors = []
def headAndHumFinder():
    global heads, colors
    while True:
        if lpAddr == 0 or plrsAddr == 0 or matrixAddr == 0:
            sleep(1)
            continue

        if hidden:
            sleep(1)
            continue

        tempColors = []
        tempHeads = []

        lpTeam = read_int8(lpAddr + teamOffset)
        for v in GetChildren(plrsAddr):
            if v == lpAddr:
                continue
            team = read_int8(v + teamOffset)
            if not ignoreTeam or (team != lpTeam and team > 0):
                char = read_int8(v + modelInstanceOffset)
                if not char:
                    continue
                ChildrenStart = DRP(char + childrenOffset, True)
                if ChildrenStart == 0:
                    continue
                head, hum = 0, 0
                ChildrenEnd = DRP(ChildrenStart + 8, True)
                OffsetAddressPerChild = 0x10
                CurrentChildAddress = DRP(ChildrenStart, True)
                for _ in range(0, 256):
                    try:
                        if CurrentChildAddress == ChildrenEnd:
                            break
                        child = read_int8(CurrentChildAddress)
                        if not(head > 0) and GetName(child) == 'Head':
                            head = child
                        elif not(hum > 0) and GetClassName(child) == 'Humanoid':
                            hum = child
                        elif head > 0 and hum > 0:
                            break
                        CurrentChildAddress += OffsetAddressPerChild
                    except OSError:
                        pass
                if head and hum:
                    try:
                        if ignoreDead and read_float(hum + healthOffset) <= 0:
                            continue
                        team = read_int8(v + teamOffset)
                        color = 'white'
                        if team > 0:
                            color = rbxColors[read_int4(team + teamColorOffset)]
                        tempColors.append(color)
                        tempHeads.append(head)
                    except OSError:
                        pass
        heads = tempHeads
        colors = tempColors
        sleep(0.1)
if __name__ == "__main__":
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

    lpAddr = 0
    matrixAddr = 0
    plrsAddr = 0
    ignoreTeam = False
    ignoreDead = False

    args = argv[1:]
    modelInstanceOffset = int(args[0])
    primitiveOffset = int(args[1])
    positionOffset = int(args[2])
    teamOffset = int(args[3])
    teamColorOffset = int(args[4])
    healthOffset = int(args[5])
    setOffsets(int(args[6]), int(args[7]))
    childrenOffset = int(args[7])
    open_device()

    Thread(target=signalHandler, daemon=True).start()
    Thread(target=headAndHumFinder, daemon=True).start()

    app = QApplication([])
    esp = ESPOverlay()
    esp.show()

    timer = QTimer()
    timer.timeout.connect(esp.update_players)
    timer.start(8)

    print('ESP started')
    app.exec_()
