print('Radar starting...')

from math import atan2, cos, sin, pi
from threading import Thread
from time import sleep
from sys import stdin, argv, exit

from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat

from OpenGL.GL import *

from rbxMemory import *

HalfPi = pi / 2

WINDOW_SIZE = 300
BORDER_PADDING = 0

windowCenter = WINDOW_SIZE / 2

scale = 2.0

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

def hex_to_rgbf(hexcol):
    if not hexcol or not hexcol.startswith('#'):
        return (1.0, 1.0, 1.0)
    h = hexcol.lstrip('#')
    if len(h) == 6:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return (r, g, b)
    return (1.0, 1.0, 1.0)

lpX = 0.0
lpY = 0.0
lpAddr = 0
camLVAddr = 0
plrsAddr = 0

hidden = True
ignoreDead = False
ignoreTeam = False

def signalHandler():
    global lpAddr, camLVAddr, plrsAddr, hidden, ignoreTeam, ignoreDead
    for line in stdin:
        line = line.strip()
        if line == '':
            continue
        if line == 'toogle1':
            hidden = not hidden
        elif line == 'toogle2':
            ignoreTeam = not ignoreTeam
        elif line == 'toogle3':
            ignoreDead = not ignoreDead
        elif line.startswith('addrs'):
            try:
                addrs = line[5:].split(',')
                lpAddr = int(addrs[0])
                camLVAddr = int(addrs[1])
                plrsAddr = int(addrs[2])
            except Exception:
                pass

Thread(target=signalHandler, daemon=True).start()

cos_a = 0.0
sin_a = 0.0

def _draw_filled_circle(x, y, radius, color):
    r, g, b = color
    glColor4f(r, g, b, 1.0)
    segments = 24
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    for i in range(segments + 1):
        theta = 2.0 * 3.1415926 * i / segments
        dx = radius * cos(theta)
        dy = radius * sin(theta)
        glVertex2f(x + dx, y + dy)
    glEnd()

def draw_circle_for_child(v):
    global cos_a, sin_a, lpX, lpY, scale, lpAddr
    try:
        if v == lpAddr:
            return
        team = pm.read_longlong(v + teamOffset)
        if not ignoreTeam or (team != lpTeam and team > 0):
            char = pm.read_longlong(v + modelInstanceOffset)

            if ignoreDead:
                hum = FindFirstChildOfClass(char, 'Humanoid')
                if hum is None or hum == 0 or pm.read_float(hum + healthOffset) <= 0:
                    return

            hrp = FindFirstChild(char, 'HumanoidRootPart')
            if hrp is None or hrp == 0:
                return

            primitive = pm.read_longlong(hrp + primitiveOffset)
            x = pm.read_float(primitive + positionOffset) - lpX
            y = pm.read_float(primitive + positionOffset + 8) - lpY

            dx = x / scale
            dy = y / scale
            sx = dx * cos_a - dy * sin_a
            sy = dx * sin_a + dy * cos_a

            if -WINDOW_SIZE <= sx <= WINDOW_SIZE and -WINDOW_SIZE <= sy <= WINDOW_SIZE:
                sx = windowCenter + sx
                sy = windowCenter + sy
                pcolor = (0.0, 0.0, 1.0)
                if team > 0:
                    try:
                        pcolor = hex_to_rgbf(rbxColors.get(pm.read_int(team + teamColorOffset), "#0000FF"))
                    except Exception:
                        pcolor = (0.0, 0.0, 1.0)
                _draw_filled_circle(sx, sy, 2.0, pcolor)
    except OSError:
        pass
    except Exception:
        pass

class RadarGL(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(WINDOW_SIZE, WINDOW_SIZE)
        self.setMouseTracking(True)
        self._last_hidden = hidden

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(16)

    def initializeGL(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glClearColor(0.0, 0.0, 0.0, 0.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        global lpX, lpY, lpAddr, camLVAddr, plrsAddr, cos_a, sin_a, lpTeam, scale
        if hidden:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            return

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glColor4f(0.0, 0.0, 0.0, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_SIZE, 0)
        glVertex2f(WINDOW_SIZE, WINDOW_SIZE)
        glVertex2f(0, WINDOW_SIZE)
        glEnd()

        if lpAddr == 0 or plrsAddr == 0 or camLVAddr == 0:
            pass
        else:
            try:
                char = pm.read_longlong(lpAddr + modelInstanceOffset)
                hrp = FindFirstChild(char, 'HumanoidRootPart')
                if hrp is not None and hrp > 0:
                    primitive = pm.read_longlong(hrp + primitiveOffset)
                    lpX = pm.read_float(primitive + positionOffset)
                    lpY = pm.read_float(primitive + positionOffset + 8)
            except OSError:
                pass
            except Exception:
                pass

        color = (1.0, 0.0, 0.0)
        if lpAddr != 0:
            try:
                lpTeam = pm.read_longlong(lpAddr + teamOffset)
                if lpTeam and lpTeam > 0:
                    colidx = pm.read_int(lpTeam + teamColorOffset)
                    color = hex_to_rgbf(rbxColors.get(colidx, "#FF0000"))
            except Exception:
                pass

        _draw_filled_circle(windowCenter, windowCenter, 2.0, color)

        try:
            camLVX = pm.read_float(camLVAddr) if camLVAddr != 0 else 0.0
            camLVZ = pm.read_float(camLVAddr + 8) if camLVAddr != 0 else 1.0
            camRot = atan2(camLVX, -camLVZ) - HalfPi
            cos_a = cos(camRot)
            sin_a = sin(camRot)
        except Exception:
            cos_a = 1.0
            sin_a = 0.0

        if plrsAddr != 0:
            try:
                children = GetChildren(plrsAddr)
                for v in children:
                    draw_circle_for_child(v)
            except Exception:
                pass

    def on_timer(self):
        if self._last_hidden != hidden:
            self._last_hidden = hidden
            if hidden:
                if self.parent() is not None:
                    self.parent().hide()
            else:
                if self.parent() is not None:
                    self.parent().show()
        if hidden:
            sleep(0.05)
        self.update()

    def wheelEvent(self, event):
        global scale
        delta = event.angleDelta().y()
        if delta > 0:
            if scale > 0.1:
                scale -= 0.1
        else:
            scale += 0.1

class RadarWindow(QOpenGLWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.85)
        self.setFixedSize(WINDOW_SIZE, WINDOW_SIZE)

        self.gl = RadarGL(self)
        self.gl.move(0, 0)

    def showEvent(self, ev):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + geo.width() - WINDOW_SIZE
            y = geo.y()
            self.move(x, y)
        return super().showEvent(ev)

def background_process_monitor():
    while True:
        try:
            if is_process_dead():
                while not yield_for_program("RobloxPlayerBeta.exe", False):
                    sleep(0.5)
                try:
                    base = get_base_addr()
                except Exception:
                    pass
        except Exception:
            pass
        sleep(0.1)

Thread(target=background_process_monitor, daemon=True).start()

fmt = QSurfaceFormat()
fmt.setSamples(8)
fmt.setDepthBufferSize(24)
QSurfaceFormat.setDefaultFormat(fmt)

args = argv[1:]
modelInstanceOffset = int(args[0])
primitiveOffset = int(args[1])
positionOffset = int(args[2])
teamOffset = int(args[3])
teamColorOffset = int(args[4])
healthOffset = int(args[5])
setOffsets(int(args[6]), int(args[7]))

app = QApplication([])

window = RadarWindow()
if hidden:
    window.hide()
else:
    window.show()

print('Radar started')
app.exec_()
