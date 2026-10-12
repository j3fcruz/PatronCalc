"""PatronCalc v1.4.2 — responsive programmer layout."""
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from PySide6.QtCore import Qt, QStandardPaths, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QVBoxLayout, QWidget, QScrollArea, QMenu, QMessageBox, QDialog, QComboBox, QCheckBox, QDialogButtonBox, QFormLayout, QLineEdit, QSizePolicy)
from engine import evaluate, format_number, CalculatorError
from programmer import display as bases_display, parse_value, operate, unsigned, signed, ProgrammerError

MAX_HISTORY = 100
MAX_EXPR = 160

def data_path():
    loc = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    folder = Path(loc)
    folder.mkdir(parents=True, exist_ok=True)
    return folder / 'settings.json'

def pretty(text):
    return text.replace('*', '×').replace('/', '÷').replace('-', '−')

class Calculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PatronCalc — v1.4.2')
        icon_path = Path(__file__).resolve().parent / 'assets' / 'patroncalc.ico'
        if icon_path.exists(): self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(390, 620)
        self.resize(430, 695)
        self.expression = ''
        self.just_evaluated = False
        self.memory = Decimal(0)
        self.entries = []
        self.history_open = False
        self.theme = 'dark'
        self.always_on_top = False
        self.startup_mode = 'last'
        self.mode = 'standard'
        self.angle_mode = 'DEG'
        self.prog_base = 'DEC'
        self.prog_bits = 64
        self.prog_value = 0
        self.prog_input = '0'
        self.prog_pending = None
        self.prog_operand = None
        self.load_data()
        if self.startup_mode in ('standard', 'scientific', 'programmer'):
            self.mode = self.startup_mode
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
        self.build_ui()
        self.render()
        QTimer.singleShot(0, self.fit_mode_to_screen)

    def load_data(self):
        try:
            data = json.loads(data_path().read_text(encoding='utf-8'))
            if not isinstance(data, dict): return
            self.mode = data.get('mode') if data.get('mode') in ('standard', 'scientific', 'programmer') else 'standard'
            self.prog_base = data.get('prog_base') if data.get('prog_base') in ('HEX','DEC','OCT','BIN') else 'DEC'
            self.prog_bits = data.get('prog_bits') if data.get('prog_bits') in (8,16,32,64) else 64
            self.angle_mode = data.get('angle_mode') if data.get('angle_mode') in ('DEG', 'RAD') else 'DEG'
            self.theme = data.get('theme') if data.get('theme') in ('dark', 'light') else 'dark'
            self.always_on_top = data.get('always_on_top') is True
            self.startup_mode = data.get('startup_mode') if data.get('startup_mode') in ('last','standard','scientific','programmer') else 'last'
            self.memory = Decimal(str(data.get('memory', '0')))
            if not self.memory.is_finite(): self.memory = Decimal(0)
            entries = data.get('history', [])
            if isinstance(entries, list):
                self.entries = [(x['expression'], x['result']) for x in entries[-MAX_HISTORY:]
                                if isinstance(x, dict) and isinstance(x.get('expression'), str)
                                and isinstance(x.get('result'), str) and len(x['expression']) <= MAX_EXPR
                                and len(x['result']) <= MAX_EXPR]
        except (OSError, ValueError, TypeError, KeyError, ArithmeticError):
            pass

    def save_data(self):
        payload = {'mode': self.mode, 'angle_mode': self.angle_mode, 'prog_base': self.prog_base, 'prog_bits': self.prog_bits, 'theme': self.theme, 'always_on_top': self.always_on_top, 'startup_mode': self.startup_mode, 'memory': str(self.memory),
                   'history': [{'expression': a, 'result': b} for a,b in self.entries[-MAX_HISTORY:]]}
        path = data_path()
        try:
            temp = path.with_suffix('.tmp')
            temp.write_text(json.dumps(payload, indent=2), encoding='utf-8')
            temp.replace(path)
        except OSError:
            pass

    def closeEvent(self, event):
        self.save_data()
        super().closeEvent(event)

    def create_button(self, text, callback, kind='normal'):
        button = QPushButton(text)
        button.setObjectName(kind)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        button.setMinimumHeight(49)
        button.setFocusPolicy(Qt.NoFocus)
        return button

    def build_ui(self):
        root = QWidget(); root.setObjectName('root'); self.setCentralWidget(root)
        self.outer = QVBoxLayout(root)
        self.outer.setContentsMargins(20, 19, 20, 15)
        self.outer.setSpacing(11)
        header = QHBoxLayout()
        brand = QLabel('◈  PATRONCALC'); brand.setObjectName('brand')
        header.addWidget(brand); header.addStretch()
        self.mode_toggle = self.create_button('Mode ▾', self.choose_mode, 'headerbutton')
        header.addWidget(self.mode_toggle)
        self.history_toggle = self.create_button('History', self.toggle_history, 'headerbutton')
        self.theme_btn = self.create_button('☀' if self.theme == 'dark' else '☾', self.toggle_theme, 'headerbutton')
        header.addWidget(self.history_toggle); header.addWidget(self.theme_btn)
        self.settings_btn = self.create_button('⚙', self.show_settings, 'headerbutton')
        self.settings_btn.setToolTip('Settings and About')
        header.addWidget(self.settings_btn)
        self.outer.addLayout(header)

        display = QFrame(); display.setObjectName('display')
        display_layout = QVBoxLayout(display); display_layout.setContentsMargins(17,14,17,14)
        self.detail = QLabel('READY'); self.detail.setObjectName('detail'); self.detail.setAlignment(Qt.AlignRight)
        self.result = QLabel('0'); self.result.setObjectName('result'); self.result.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.result.setMinimumHeight(65)
        self.result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.memory_flag = QLabel(''); self.memory_flag.setObjectName('memoryflag')
        display_layout.addWidget(self.detail); display_layout.addWidget(self.result); display_layout.addWidget(self.memory_flag)
        self.outer.addWidget(display)

        self.main_area = QWidget(); self.main_area.setObjectName('mainarea')
        main_layout = QVBoxLayout(self.main_area); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(9)
        memory = QHBoxLayout(); memory.setSpacing(7)
        for label in ['MC','MR','M+','M−','MS']:
            memory.addWidget(self.create_button(label, lambda checked=False, k=label: self.memory_press(k), 'memorybutton'))
        main_layout.addLayout(memory)
        self.science_area = QWidget()
        science = QGridLayout(self.science_area)
        science.setContentsMargins(0, 0, 0, 0)
        science.setSpacing(7)
        science_keys = [['DEG/RAD','sin','cos','tan'],['π','e','log','ln'],['x²','xʸ','n!','1/x']]
        for r, row in enumerate(science_keys):
            for c, key in enumerate(row):
                science.addWidget(self.create_button(key, lambda checked=False, k=key: self.scientific_press(k), 'sciencebutton'), r, c)
        main_layout.addWidget(self.science_area)
        self.science_area.setVisible(self.mode == 'scientific')
        keys = [['(', ')', 'CE', '⌫'], ['C','±','%','÷'], ['7','8','9','×'],
                ['4','5','6','−'], ['1','2','3','+'], ['√','0','.','=']]
        grid = QGridLayout(); grid.setSpacing(9)
        for r, row in enumerate(keys):
            for c, key in enumerate(row):
                kind = 'equals' if key == '=' else 'operator' if key in ('÷','×','−','+','√') else 'utility' if key in ('C','CE','⌫','±','%','(',')') else 'normal'
                grid.addWidget(self.create_button(key, lambda checked=False, k=key: self.press(k), kind), r, c)
        for i in range(len(keys)): grid.setRowStretch(i, 1)
        main_layout.addLayout(grid, 1)
        self.outer.addWidget(self.main_area, 1)
        self.create_programmer_ui()

        self.history_area = QFrame(); self.history_area.setObjectName('historypanel')
        h_layout = QVBoxLayout(self.history_area)
        h_header = QHBoxLayout(); h_title = QLabel('CALCULATION HISTORY'); h_title.setObjectName('brand')
        h_header.addWidget(h_title); h_header.addStretch()
        h_header.addWidget(self.create_button('Clear', self.clear_history, 'headerbutton'))
        h_layout.addLayout(h_header)
        self.history_scroll = QScrollArea(); self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.NoFrame)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_content = QWidget()
        self.history_list = QVBoxLayout(self.history_content)
        self.history_list.setAlignment(Qt.AlignTop)
        self.history_scroll.setWidget(self.history_content)
        h_layout.addWidget(self.history_scroll)
        self.history_area.hide()
        self.outer.addWidget(self.history_area, 1)
        self.footer = QLabel('ESC  CLEAR   •   ENTER  EQUALS   •   CTRL+H  HISTORY')
        self.footer.setObjectName('footer'); self.footer.setAlignment(Qt.AlignCenter)
        self.outer.addWidget(self.footer)
        self.main_area.setVisible(self.mode != 'programmer')
        self.programmer_scroll.setVisible(self.mode == 'programmer')
        self.apply_theme()
        shortcut = QShortcut(QKeySequence('Ctrl+H'), self)
        shortcut.activated.connect(self.toggle_history)
        shortcut2 = QShortcut(QKeySequence('Ctrl+C'), self)
        shortcut2.activated.connect(lambda: QApplication.clipboard().setText(self.expression or '0'))

    def apply_theme(self):
        dark = self.theme == 'dark'
        colors = ({'bg':'#0B1120','panel':'#151F35','border':'#293B59','text':'#F6F9FF','muted':'#92A9CE',
                   'button':'#1C2B45','hover':'#304766','op':'#243D5D','util':'#273249','accent':'#2279EA'} if dark else
                  {'bg':'#F1F5FB','panel':'#FFFFFF','border':'#C8D5E6','text':'#17233A','muted':'#576B89',
                   'button':'#E4EBF6','hover':'#D1E0F5','op':'#CCE1F8','util':'#DBE5F2','accent':'#1765CC'})
        self.setStyleSheet('''
        QWidget#root { background: %(bg)s; color: %(text)s; }
        QLabel#brand { font: 700 14px 'Segoe UI'; color: %(text)s; letter-spacing: 1px; }
        QFrame#display, QFrame#historypanel { background: %(panel)s; border: 1px solid %(border)s; border-radius: 17px; }
        QLabel#detail { color: %(muted)s; font: 12px 'Segoe UI'; border: none; }
        QLabel#result { color: %(text)s; font: 600 38px 'Segoe UI'; border: none; }
        QLabel#memoryflag { color: %(muted)s; font: 11px 'Segoe UI'; border: none; }
        QLabel#footer { color: %(muted)s; font: 10px 'Segoe UI'; }
        QPushButton { color: %(text)s; font: 600 19px 'Segoe UI'; background: %(button)s;
                      border: 1px solid %(border)s; border-radius: 13px; padding: 4px; }
        QPushButton:hover { background: %(hover)s; }
        QPushButton:pressed { border: 2px solid %(accent)s; }
        QPushButton#operator { background: %(op)s; }
        QPushButton#utility { background: %(util)s; }
        QPushButton#equals { background: %(accent)s; color: #FFFFFF; }
        QPushButton#headerbutton { font-size: 12px; padding: 4px 9px; min-height: 23px; border-radius: 8px; }
        QPushButton#memorybutton { font-size: 13px; min-height: 29px; border-radius: 8px; }
        QPushButton#sciencebutton { font-size: 14px; min-height: 34px; border-radius: 9px; background: %(op)s; }
        QPushButton#progbutton { font-size: 14px; min-height: 37px; border-radius: 9px; background: %(op)s; }
        QWidget#programmerArea { background: %(bg)s; }
        QScrollArea#programmerScroll, QScrollArea#programmerScroll > QWidget > QWidget { background: %(bg)s; }
        QLabel#progbaseName { color: %(muted)s; font: 11px 'Consolas'; border: none; }
        QLineEdit#progbaseValue { color: %(muted)s; font: 11px 'Consolas'; background: %(bg)s; border: 0px; padding: 0px 2px; }
        QComboBox, QCheckBox { color: %(text)s; background: %(panel)s; font: 12px 'Segoe UI'; padding: 6px; }
        QPushButton#historyitem { font-size: 14px; text-align: right; padding: 10px; min-height: 44px; }
        QScrollArea { background: transparent; border: none; }
        ''' % colors)

    def render(self):
        if self.mode == 'programmer':
            self.render_programmer(); return
        shown = pretty(self.expression) or '0'
        self.result.setText(shown)
        count = len(shown)
        self.result.setStyleSheet(f'font-size: {38 if count <= 15 else 27 if count <= 25 else 19}px;')
        self.memory_flag.setText(('● MEMORY: ' + format_number(self.memory) + '   •   ' if self.memory else '') + (self.angle_mode if self.mode == 'scientific' else ''))

    def error(self, message):
        self.detail.setText(message.upper())
        self.result.setText('Error')
        self.expression = ''
        self.just_evaluated = False

    def current_value(self):
        if not self.expression: return Decimal(0)
        return evaluate(self.expression, self.angle_mode)

    def press(self, key):
        if key == 'C':
            self.expression = ''; self.detail.setText('READY'); self.just_evaluated=False
        elif key == 'CE':
            self.expression = re.sub(r'(?<![\w.])\d+(?:\.\d*)?$','', self.expression)
            self.just_evaluated = False
        elif key == '⌫':
            self.expression = self.expression[:-1]; self.just_evaluated=False
        elif key == '=':
            if not self.expression: return
            try:
                expr = self.expression
                result = format_number(evaluate(expr, self.angle_mode))
                self.entries.append((expr,result)); self.entries = self.entries[-MAX_HISTORY:]
                self.detail.setText(pretty(expr) + ' =')
                self.expression = result; self.just_evaluated = True
                self.refresh_history(); self.save_data()
            except (CalculatorError, ValueError, ArithmeticError) as exc:
                self.error(str(exc))
        elif key in ('√','±','%'):
            try:
                if key == '√':
                    val = self.current_value()
                    if val < 0: raise CalculatorError('Cannot take square root of negative number')
                    self.expression = format_number(val.sqrt())
                elif key == '±':
                    if self.expression:
                        # Negate current completed expression; not the string's leading token.
                        self.expression = format_number(-self.current_value())
                    else: self.expression = '-'
                else:
                    if self.expression: self.expression = format_number(self.current_value() / Decimal(100))
                self.just_evaluated = True
            except (CalculatorError, ValueError, ArithmeticError) as exc:
                self.error(str(exc))
        elif key in ('+', '−', '×', '÷'):
            op = {'−':'-', '×':'*','÷':'/'}.get(key,key)
            if self.just_evaluated: self.just_evaluated=False
            if self.expression and self.expression[-1] in '+-*/' and not self.expression.endswith('**'):
                self.expression = self.expression[:-1] + op
            elif self.expression: self.expression += op
            elif op == '-': self.expression='-'
        elif key in '()' and len(key) == 1:
            if self.just_evaluated and key == '(':
                self.expression=''; self.just_evaluated=False
            if key == '(' and self.expression and (self.expression[-1].isdigit() or self.expression[-1] == ')'):
                self.expression += '*'
            self.expression += key
        elif key.isdigit() or key == '.':
            if self.just_evaluated:
                self.expression=''; self.detail.setText('READY'); self.just_evaluated=False
            if self.expression.endswith(')'): self.expression += '*'
            if key == '.':
                fragment = re.split(r'[+*/()\-]', self.expression)[-1]
                if '.' in fragment or 'e' in fragment.lower(): return
                if not fragment: self.expression += '0'
            self.expression += key
        if len(self.expression) > MAX_EXPR:
            self.expression = self.expression[:MAX_EXPR]
        self.render()

    def choose_mode(self):
        menu = QMenu(self)
        for label, mode in [('Standard','standard'),('Scientific','scientific'),('Programmer','programmer')]:
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self.mode == mode)
            action.triggered.connect(lambda checked=False, m=mode: self.select_mode(m))
        menu.exec(self.mode_toggle.mapToGlobal(self.mode_toggle.rect().bottomLeft()))

    def select_mode(self, mode):
        if mode not in ('standard', 'scientific', 'programmer'): return
        self.mode = mode
        self.main_area.setVisible(mode != 'programmer' and not self.history_open)
        self.programmer_scroll.setVisible(mode == 'programmer' and not self.history_open)
        self.science_area.setVisible(mode == 'scientific')
        self.setMinimumHeight(620)
        QTimer.singleShot(0, self.fit_mode_to_screen)
        self.detail.setText(mode.upper() + ' MODE')
        self.render(); self.save_data()

    def create_programmer_ui(self):
        self.programmer_area = QWidget()
        self.programmer_area.setObjectName('programmerArea')
        self.programmer_area.setMinimumWidth(0)
        self.programmer_area.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        layout = QVBoxLayout(self.programmer_area)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(8)
        selector = QHBoxLayout()
        self.base_buttons = {}
        for base in ('HEX','DEC','OCT','BIN'):
            btn = self.create_button(base, lambda checked=False, b=base: self.programmer_set_base(b), 'progbutton')
            self.base_buttons[base] = btn; selector.addWidget(btn)
        layout.addLayout(selector)
        bitsrow = QHBoxLayout()
        self.bits_buttons = {}
        for bits in (8,16,32,64):
            btn = self.create_button(str(bits)+'-bit', lambda checked=False, b=bits: self.programmer_set_bits(b), 'progbutton')
            self.bits_buttons[bits] = btn; bitsrow.addWidget(btn)
        layout.addLayout(bitsrow)
        # Use narrow, horizontally scrollable read-only fields. A single long BIN
        # QLabel would otherwise dictate the panel's minimum width and clip keys.
        self.base_labels = {}
        for base in ('HEX','DEC','OCT','BIN'):
            base_row = QHBoxLayout()
            base_row.setSpacing(6)
            name = QLabel(base)
            name.setObjectName('progbaseName')
            name.setFixedWidth(38)
            value = QLineEdit()
            value.setObjectName('progbaseValue')
            value.setReadOnly(True)
            value.setFrame(False)
            value.setMinimumWidth(0)
            value.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            value.setFixedHeight(29)
            value.setToolTip('Select text to copy the full value')
            self.base_labels[base] = value
            base_row.addWidget(name)
            base_row.addWidget(value, 1)
            layout.addLayout(base_row)
        grid = QGridLayout(); grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)
        for column in range(6):
            grid.setColumnStretch(column, 1)
            grid.setColumnMinimumWidth(column, 0)
        keys = [
            ['A','B','C','D','E','F'],
            ['AND','OR','XOR','NOT','<<','>>'],
            ['7','8','9','+','-','⌫'],
            ['4','5','6','*','/','C'],
            ['1','2','3','(',')','='],
            ['±','0','00','%','CE','COPY']]
        self.prog_digit_buttons = {}
        for row, items in enumerate(keys):
            for col, key in enumerate(items):
                button = self.create_button(key, lambda checked=False, k=key: self.programmer_press(k),
                                            'equals' if key == '=' else 'progbutton')
                button.setMinimumWidth(0)
                button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                grid.addWidget(button,row,col)
                if len(key) == 1 and key in 'ABCDEF0123456789': self.prog_digit_buttons[key] = button
        layout.addLayout(grid, 1)
        # A scrollable container protects buttons on smaller screens and at 125–200% DPI.
        self.programmer_scroll = QScrollArea()
        self.programmer_scroll.setObjectName('programmerScroll')
        self.programmer_scroll.setWidgetResizable(True)
        self.programmer_scroll.setFrameShape(QFrame.NoFrame)
        self.programmer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.programmer_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.programmer_scroll.setMinimumWidth(0)
        self.programmer_scroll.setWidget(self.programmer_area)
        self.outer.addWidget(self.programmer_scroll, 1)

    def fit_mode_to_screen(self):
        """Fit both axes to the current mode without exceeding screen work area."""
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        work = screen.availableGeometry()
        # Six programmer keys should have readable targets. Prefer a wider
        # window, but on small displays let columns contract evenly.
        desired_width = 570 if self.mode == 'programmer' else 430
        # Limit width to the screen and avoid growing outside its work area.
        usable_width = max(320, work.width() - 24)
        target_width = min(desired_width, usable_width)
        self.outer.activate()
        if self.mode == 'programmer':
            panel_height = self.programmer_area.layout().sizeHint().height()
            # Height of header, display and footer + approximate frame overhead.
            desired_height = max(760, panel_height + 265)
        elif self.mode == 'scientific':
            desired_height = max(695, self.main_area.sizeHint().height() + 265)
        else:
            desired_height = 695
        target_height = min(desired_height, max(520, work.height() - 24))
        self.resize(target_width, target_height)

    def programmer_set_base(self, base):
        self.prog_base=base
        self.prog_input=self.programmer_format_value(self.prog_value)
        self.render_programmer(); self.save_data()

    def programmer_set_bits(self, bits):
        self.prog_bits=bits
        self.prog_value=unsigned(self.prog_value,bits)
        if self.prog_operand is not None: self.prog_operand=unsigned(self.prog_operand,bits)
        self.prog_input=self.programmer_format_value(self.prog_value)
        self.render_programmer(); self.save_data()

    def programmer_format_value(self, value):
        if self.prog_base == 'DEC': return str(signed(value,self.prog_bits))
        return bases_display(value,self.prog_bits)[self.prog_base].lstrip('0') or '0'

    def render_programmer(self):
        for base, label in self.base_labels.items():
            val=bases_display(self.prog_value,self.prog_bits)[base]
            label.setText(val)
            label.setCursorPosition(0)
        for base, button in self.base_buttons.items():
            button.setChecked(base == self.prog_base)
            button.setStyleSheet('border: 2px solid #3395FF;' if base == self.prog_base else '')
        for bits, button in self.bits_buttons.items():
            button.setStyleSheet('border: 2px solid #3395FF;' if bits == self.prog_bits else '')
        valid='0123456789ABCDEF'[:{'BIN':2,'OCT':8,'DEC':10,'HEX':16}[self.prog_base]]
        for key, button in self.prog_digit_buttons.items(): button.setEnabled(key in valid)
        self.result.setText(self.prog_input)
        n=len(self.prog_input)
        self.result.setStyleSheet(f'font-size: {38 if n < 16 else 26 if n < 26 else 19}px;')
        self.memory_flag.setText(f'{self.prog_bits}-BIT • {self.prog_base} • TWO’S COMPLEMENT')

    def programmer_press(self, key):
        try:
            if key == 'C':
                self.prog_value=0; self.prog_input='0'; self.prog_pending=None; self.prog_operand=None
            elif key == 'CE':
                self.prog_value=0; self.prog_input='0'
            elif key == '⌫':
                self.prog_input=self.prog_input[:-1] or '0'
                self.prog_value=parse_value(self.prog_input,self.prog_base,self.prog_bits)
            elif key == 'COPY':
                QApplication.clipboard().setText(self.prog_input)
            elif key == '±':
                self.prog_value=unsigned(-signed(self.prog_value,self.prog_bits),self.prog_bits)
                self.prog_input=self.programmer_format_value(self.prog_value)
            elif key == 'NOT':
                self.prog_value=operate(self.prog_value,'NOT',bits=self.prog_bits)
                self.prog_input=self.programmer_format_value(self.prog_value)
            elif key in ('AND','OR','XOR','<<','>>','+','-','*','/','%'):
                self.prog_operand=self.prog_value
                self.prog_pending=key
                self.prog_input='0'
                self.prog_value=0
                self.detail.setText('PROGRAMMER • ' + key)
            elif key == '=':
                if self.prog_pending is not None:
                    self.prog_value=operate(self.prog_operand,self.prog_pending,self.prog_value,self.prog_bits)
                    self.prog_input=self.programmer_format_value(self.prog_value)
                    self.prog_pending=None; self.prog_operand=None
            elif key in ('(',')'):
                self.detail.setText('PARENTHESES ARE NOT USED IN PROGRAMMER MODE')
            elif key == '00' or (len(key)==1 and key.upper() in '0123456789ABCDEF'):
                valid='0123456789ABCDEF'[:{'BIN':2,'OCT':8,'DEC':10,'HEX':16}[self.prog_base]]
                if key != '00' and key not in valid: return
                candidate=(self.prog_input if self.prog_input!='0' else '')+key
                if len(candidate) > 68: raise ProgrammerError('Input too long')
                self.prog_value=parse_value(candidate,self.prog_base,self.prog_bits)
                self.prog_input=candidate
            self.render_programmer()
        except ProgrammerError as exc:
            self.detail.setText('ERROR: '+str(exc).upper())
            self.render_programmer()

    def scientific_press(self, key):
        if key == 'DEG/RAD':
            self.angle_mode = 'RAD' if self.angle_mode == 'DEG' else 'DEG'
            self.detail.setText('ANGLE MODE: ' + self.angle_mode)
            self.render(); self.save_data(); return
        if self.just_evaluated and key in ('π', 'e', 'sin', 'cos', 'tan', 'log', 'ln'):
            self.expression = ''
        if key in ('π', 'e'):
            if self.expression and (self.expression[-1].isdigit() or self.expression[-1] == ')'):
                self.expression += '*'
            self.expression += 'pi' if key == 'π' else 'e'
        elif key in ('sin', 'cos', 'tan', 'log', 'ln'):
            if self.expression and (self.expression[-1].isdigit() or self.expression[-1] == ')'):
                self.expression += '*'
            self.expression += key + '('
        elif key == 'xʸ':
            if self.expression and self.expression[-1] not in '+-*/(':
                self.expression += '**'
        elif key in ('x²', 'n!', '1/x'):
            if not self.expression: return
            func = {'x²': None, 'n!': 'fact', '1/x': 'inv'}[key]
            self.expression = '(' + self.expression + ')**2' if func is None else func + '(' + self.expression + ')'
        if len(self.expression) > MAX_EXPR:
            self.expression = self.expression[:MAX_EXPR]
        self.just_evaluated = False
        self.detail.setText('SCIENTIFIC • ' + self.angle_mode)
        self.render()

    def memory_press(self, key):
        try:
            if key == 'MC': self.memory=Decimal(0)
            elif key == 'MR':
                self.expression=format_number(self.memory); self.just_evaluated=True
            else:
                value = self.current_value()
                if key == 'MS': self.memory=value
                elif key == 'M+': self.memory += value
                elif key == 'M−': self.memory -= value
            self.save_data(); self.render()
        except (CalculatorError, ValueError, ArithmeticError) as exc:
            self.error(str(exc))

    def refresh_history(self):
        while self.history_list.count():
            item = self.history_list.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not self.entries:
            message = QLabel('No calculations yet.'); message.setObjectName('detail')
            self.history_list.addWidget(message)
        for expr, result in reversed(self.entries):
            label = f'{pretty(expr)}   =   {result}'
            btn = self.create_button(label, lambda checked=False, x=result: self.recall(x), 'historyitem')
            btn.setToolTip('Reuse result: ' + result)
            self.history_list.addWidget(btn)

    def recall(self, result):
        self.expression=result; self.just_evaluated=True
        self.detail.setText('RECALLED FROM HISTORY')
        self.render(); self.toggle_history()

    def toggle_history(self):
        self.history_open = not self.history_open
        self.history_area.setVisible(self.history_open)
        self.main_area.setVisible(not self.history_open and self.mode != 'programmer')
        self.programmer_scroll.setVisible(not self.history_open and self.mode == 'programmer')
        self.history_toggle.setText('Back' if self.history_open else 'History')
        if not self.history_open: QTimer.singleShot(0, self.fit_mode_to_screen)
        if self.history_open: self.refresh_history()

    def clear_history(self):
        self.entries.clear(); self.refresh_history(); self.save_data()

    def toggle_theme(self):
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self.theme_btn.setText('☀' if self.theme == 'dark' else '☾')
        self.apply_theme(); self.save_data()

    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('PatronCalc Settings')
        dialog.setMinimumWidth(330)
        dialog.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialog)
        heading = QLabel('PATRONCALC  •  PREFERENCES')
        heading.setObjectName('brand')
        layout.addWidget(heading)
        form = QFormLayout()
        theme = QComboBox()
        theme.addItems(['Dark', 'Light'])
        theme.setCurrentText(self.theme.title())
        form.addRow('Color theme', theme)
        startup = QComboBox()
        startup.addItem('Last used mode', 'last')
        startup.addItem('Standard', 'standard')
        startup.addItem('Scientific', 'scientific')
        startup.addItem('Programmer', 'programmer')
        startup.setCurrentIndex(max(0, startup.findData(self.startup_mode)))
        form.addRow('Startup mode', startup)
        on_top = QCheckBox('Keep calculator above other windows')
        on_top.setChecked(self.always_on_top)
        form.addRow('Window behavior', on_top)
        layout.addLayout(form)
        path_label = QLabel('Settings and history are saved in your Windows user profile.')
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        actions = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        actions.accepted.connect(dialog.accept)
        actions.rejected.connect(dialog.reject)
        layout.addWidget(actions)
        if dialog.exec() == QDialog.Accepted:
            self.startup_mode = startup.currentData()
            self.always_on_top = on_top.isChecked()
            next_theme = theme.currentText().lower()
            if next_theme != self.theme:
                self.toggle_theme()
            self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
            self.show()
            self.save_data()

    def keyPressEvent(self, event):
        if self.mode == 'programmer':
            if event.key() in (Qt.Key_Return,Qt.Key_Enter): self.programmer_press('='); return
            if event.key() == Qt.Key_Escape: self.programmer_press('C'); return
            if event.key() == Qt.Key_Backspace: self.programmer_press('⌫'); return
            ch=event.text().upper()
            if ch and ch in '0123456789ABCDEF+-*/%': self.programmer_press(ch); return
            return super().keyPressEvent(event)
        mappings = {Qt.Key_Return:'=', Qt.Key_Enter:'=', Qt.Key_Escape:'C',
                    Qt.Key_Backspace:'⌫', Qt.Key_Delete:'CE'}
        if event.key() in mappings: self.press(mappings[event.key()]); return
        ch = event.text()
        if ch == '^': self.scientific_press('xʸ'); return
        if ch and ch in '0123456789.+-*/()%':
            self.press({'-':'−','*':'×','/':'÷'}.get(ch, ch)); return
        super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('PatronCalc')
    app.setApplicationVersion('1.4.1')
    icon = Path(__file__).resolve().parent / 'assets' / 'patroncalc.ico'
    if icon.exists(): app.setWindowIcon(QIcon(str(icon)))
    app.setOrganizationName('PatronHubDevs')
    app.setStyle('Fusion')
    window = Calculator(); window.show()
    sys.exit(app.exec())

if __name__ == '__main__': main()
