import os
import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.metrics import dp

from analyzer import analyzer as az

try:
    from android.permissions import request_permissions, Permission
    ANDROID = True
except Exception:
    ANDROID = False

# ---------- accounts ----------
PAID_USER = "xitexe"
PAID_PASS = "bossman"
FREE_USER = "guest"
FREE_PASS = "guest"
FREE_SECONDS = 300

# ---------- palette ----------
BG = (0.043, 0.039, 0.078, 1)
BG_2 = (0.063, 0.055, 0.110, 1)
PANEL = (0.086, 0.075, 0.145, 1)
PANEL_2 = (0.110, 0.094, 0.180, 1)
BORDER = (0.180, 0.157, 0.290, 1)
TEXT = (0.910, 0.902, 1.0, 1)
MUTED = (0.62, 0.58, 0.75, 1)
PURPLE = (0.72, 0.42, 1.0, 1)
PURPLE_2 = (0.54, 0.29, 0.86, 1)
GREEN = (0.24, 0.86, 0.52, 1)
GREEN_2 = (0.12, 0.65, 0.36, 1)
RED = (1.0, 0.28, 0.34, 1)
AMBER = (1.0, 0.72, 0.29, 1)

Window.clearcolor = BG


class Session:
    def __init__(self):
        self.user = ""
        self.plan = ""
        self.started = 0.0
        self.listeners_registered = False


SESSION = Session()


class Card(BoxLayout):
    def __init__(self, bg=PANEL, border=BORDER, radius=14, **kw):
        super().__init__(**kw)
        self._radius = radius
        with self.canvas.before:
            self._color = Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(radius)])
            self._border_color = Color(*border)
            self._border = Line(rounded_rectangle=(self.x, self.y,
                                                    self.width, self.height,
                                                    dp(radius)), width=1.1)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._border.rounded_rectangle = (
            self.x, self.y, self.width, self.height, dp(self._radius))


class GradientButton(ButtonBehavior, BoxLayout):
    def __init__(self, text="", color_a=GREEN, color_b=GREEN_2,
                 text_color=(1, 1, 1, 1), **kw):
        super().__init__(**kw)
        self._color_a = color_a
        self._color_b = color_b
        with self.canvas.before:
            self._color = Color(*color_a)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self._label = Label(text=text, color=text_color, bold=True, font_size="15sp")
        self.add_widget(self._label)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_colors(self, a, b, text=None):
        self._color.rgba = a
        if text is not None:
            self._label.color = text


class SigChip(Card):
    def __init__(self, weight, why, **kw):
        if weight >= 20:
            wcolor = RED
        elif weight >= 15:
            wcolor = AMBER
        else:
            wcolor = PURPLE
        super().__init__(bg=PANEL_2, border=wcolor, radius=8,
                         orientation="horizontal",
                         padding=[dp(8), dp(6)], spacing=dp(8),
                         size_hint_y=None, height=dp(34), **kw)
        self.add_widget(Label(text="+%d" % weight, color=wcolor,
                              font_size="12sp", bold=True,
                              size_hint_x=None, width=dp(30)))
        self.add_widget(Label(text=why, color=MUTED, font_size="11.5sp",
                              halign="left", valign="middle",
                              text_size=(dp(230), None)))


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        outer = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        outer.add_widget(Widget())

        card = Card(orientation="vertical", padding=dp(24), spacing=dp(12),
                    size_hint_y=None, height=dp(360))

        card.add_widget(Label(text="[b]AntiPhish[/b]", markup=True,
                              font_size="32sp", color=PURPLE,
                              size_hint_y=None, height=dp(44), bold=True))
        card.add_widget(Label(text="Sign in to access the detector",
                              color=MUTED, font_size="13sp",
                              size_hint_y=None, height=dp(24)))

        self.error = Label(text="", color=RED, font_size="12sp",
                           size_hint_y=None, height=dp(20))
        card.add_widget(self.error)

        self.user = TextInput(hint_text="Username", multiline=False,
                              size_hint_y=None, height=dp(46),
                              background_color=PANEL_2, foreground_color=TEXT,
                              cursor_color=PURPLE, padding=[dp(12), dp(12)])
        card.add_widget(self.user)

        self.pwd = TextInput(hint_text="Password", password=True, multiline=False,
                             size_hint_y=None, height=dp(46),
                             background_color=PANEL_2, foreground_color=TEXT,
                             cursor_color=PURPLE, padding=[dp(12), dp(12)])
        card.add_widget(self.pwd)

        btn = GradientButton(text="Sign in", color_a=GREEN, color_b=GREEN_2,
                             size_hint_y=None, height=dp(48))
        btn.bind(on_release=self._login)
        card.add_widget(btn)

        card.add_widget(Label(
            text="Free: guest / guest  ·  Paid: xitexe / bossman",
            color=MUTED, font_size="11sp",
            size_hint_y=None, height=dp(30),
            halign="center"))

        outer.add_widget(card)
        outer.add_widget(Widget())
        self.add_widget(outer)

    def _login(self, *a):
        u = self.user.text.strip()
        p = self.pwd.text
        if u == PAID_USER and p == PAID_PASS:
            SESSION.user = u
            SESSION.plan = "paid"
            SESSION.started = 0
            self.manager.current = "welcome"
            return
        if u == FREE_USER and p == FREE_PASS:
            SESSION.user = u
            SESSION.plan = "free"
            SESSION.started = time.time()
            self.manager.current = "welcome"
            return
        self.error.text = "Invalid credentials"


class WelcomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        root.add_widget(Widget())

        root.add_widget(Label(text="[b]WELCOME[/b]", markup=True,
                              font_size="34sp", color=PURPLE,
                              size_hint_y=None, height=dp(52), bold=True))
        root.add_widget(Label(text="[b]XITEXE BOSS MAN[/b]", markup=True,
                              font_size="26sp", color=GREEN,
                              size_hint_y=None, height=dp(44), bold=True))
        root.add_widget(Label(text="AntiPhishing Tool - Local",
                              color=MUTED, font_size="13sp",
                              size_hint_y=None, height=dp(24)))

        self.count = Label(text="5", font_size="60sp", color=PURPLE,
                           size_hint_y=None, height=dp(90), bold=True)
        root.add_widget(self.count)

        root.add_widget(Label(text="Entering dashboard",
                              color=MUTED, font_size="12sp",
                              size_hint_y=None, height=dp(22)))

        root.add_widget(Widget())

        self._n = 5
        self._ev = None

    def on_enter(self, *a):
        self._n = 5
        self.count.text = "5"
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, dt):
        self._n -= 1
        if self._n <= 0:
            if self._ev:
                self._ev.cancel()
                self._ev = None
            self.manager.current = "permissions" if ANDROID else "home"
            return False
        self.count.text = str(self._n)
        return True


class PermissionsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        root.add_widget(Widget())

        card = Card(orientation="vertical", padding=dp(24), spacing=dp(14),
                    size_hint_y=None, height=dp(400))

        card.add_widget(Label(text="[b]Permissions[/b]", markup=True,
                              font_size="24sp", color=PURPLE,
                              size_hint_y=None, height=dp(40), bold=True))
        card.add_widget(Label(
            text="AntiPhish needs these to watch for phishing:\n\n"
                 "• Read SMS - to scan incoming texts\n"
                 "• Phone state - to detect incoming calls\n"
                 "• Notifications - to alert on threats\n\n"
                 "Nothing ever leaves your device.",
            color=MUTED, font_size="12.5sp",
            halign="left", valign="top",
            size_hint_y=None, height=dp(200),
            text_size=(dp(280), None)))

        grant = GradientButton(text="Grant permissions",
                               color_a=GREEN, color_b=GREEN_2,
                               size_hint_y=None, height=dp(50))
        grant.bind(on_release=self._grant)
        card.add_widget(grant)

        skip = GradientButton(text="Skip for now",
                              color_a=PANEL_2, color_b=PANEL,
                              text_color=MUTED,
                              size_hint_y=None, height=dp(44))
        skip.bind(on_release=self._skip)
        card.add_widget(skip)

        root.add_widget(card)
        root.add_widget(Widget())
        self.add_widget(root)

    def _grant(self, *a):
        if not ANDROID:
            self.manager.current = "home"
            return
        request_permissions(
            [Permission.RECEIVE_SMS, Permission.READ_SMS,
             Permission.READ_PHONE_STATE, Permission.POST_NOTIFICATIONS],
            self._after_grant,
        )

    def _after_grant(self, perms, grants):
        try:
            from sms_listener import register_all
            register_all()
            SESSION.listeners_registered = True
        except Exception as e:
            print("register_all failed:", e)
        self.manager.current = "home"

    def _skip(self, *a):
        self.manager.current = "home"


class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._active = "message"
        self._timer_ev = None

        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(84))
        header.add_widget(Label(text="[b]AntiPhish[/b]", markup=True,
                                font_size="26sp", color=PURPLE,
                                size_hint_y=None, height=dp(40), bold=True))
        strip = BoxLayout(orientation="horizontal", size_hint_y=None,
                          height=dp(28), spacing=dp(8))
        self.plan_chip = Card(orientation="horizontal", bg=PANEL_2,
                              border=BORDER, radius=12,
                              padding=[dp(10), dp(2)], spacing=dp(6),
                              size_hint=(None, 1), width=dp(130))
        self.plan_label = Label(text="", color=MUTED, font_size="12sp")
        self.plan_chip.add_widget(self.plan_label)
        strip.add_widget(self.plan_chip)
        self.timer_label = Label(text="", color=RED, font_size="12sp",
                                 size_hint_x=None, width=dp(60))
        strip.add_widget(self.timer_label)
        strip.add_widget(Widget())
        self.upgrade_btn = GradientButton(text="Paid", color_a=GREEN,
                                          color_b=GREEN_2,
                                          size_hint=(None, 1), width=dp(70))
        self.upgrade_btn.bind(on_release=self._upgrade)
        strip.add_widget(self.upgrade_btn)
        logout = GradientButton(text="Logout", color_a=PANEL_2, color_b=PANEL,
                                text_color=MUTED,
                                size_hint=(None, 1), width=dp(80))
        logout.bind(on_release=self._logout)
        strip.add_widget(logout)
        header.add_widget(strip)
        root.add_widget(header)

        self.tab_bar = BoxLayout(orientation="horizontal", size_hint_y=None,
                                 height=dp(44), spacing=dp(4))
        self.tabs = {}
        for key, label in [("message", "SMS"), ("call", "Calls"),
                           ("video", "Video"), ("history", "History")]:
            btn = GradientButton(text=label, color_a=PANEL_2, color_b=PANEL,
                                 text_color=MUTED, size_hint=(1, 1))
            btn.bind(on_release=lambda *a, k=key: self._show(k))
            self.tabs[key] = btn
            self.tab_bar.add_widget(btn)
        root.add_widget(self.tab_bar)

        self.content = BoxLayout(orientation="vertical")
        self.panels = {
            "message": self._build_message(),
            "call": self._build_call(),
            "video": self._build_video(),
            "history": self._build_history(),
        }
        for p in self.panels.values():
            self.content.add_widget(p)
        root.add_widget(self.content)

        self._show("message")
        self.add_widget(root)

    def on_enter(self, *a):
        self._refresh_plan_ui()
        if ANDROID and not SESSION.listeners_registered:
            try:
                from sms_listener import register_all
                register_all()
                SESSION.listeners_registered = True
            except Exception as e:
                print("register_all failed:", e)
        if self._timer_ev:
            self._timer_ev.cancel()
        if SESSION.plan == "free":
            self._timer_ev = Clock.schedule_interval(self._tick_timer, 1.0)

    def on_leave(self, *a):
        if self._timer_ev:
            self._timer_ev.cancel()
            self._timer_ev = None

    def _refresh_plan_ui(self):
        if SESSION.plan == "paid":
            self.plan_label.text = "paid"
            self.plan_label.color = GREEN
            self.plan_chip._color.rgba = (0.10, 0.30, 0.20, 1)
            self.plan_chip._border_color.rgba = GREEN
            self.timer_label.text = ""
            self.upgrade_btn.opacity = 0
            self.upgrade_btn.disabled = True
        else:
            self.plan_label.text = "free"
            self.plan_label.color = RED
            self.plan_chip._color.rgba = (0.30, 0.10, 0.14, 1)
            self.plan_chip._border_color.rgba = RED
            self.upgrade_btn.opacity = 1
            self.upgrade_btn.disabled = False
            self._update_timer_text()

    def _update_timer_text(self):
        if SESSION.plan != "free":
            return
        left = max(0, int(FREE_SECONDS - (time.time() - SESSION.started)))
        m = left // 60
        s = left % 60
        self.timer_label.text = "%d:%02d" % (m, s)
        if left <= 30:
            self.timer_label.color = RED
        else:
            self.timer_label.color = MUTED

    def _tick_timer(self, dt):
        if SESSION.plan != "free":
            return False
        left = FREE_SECONDS - (time.time() - SESSION.started)
        if left <= 0:
            self._expire()
            return False
        self._update_timer_text()
        return True

    def _expire(self):
        try:
            from sms_listener import stop_all
            stop_all()
        except Exception:
            pass
        SESSION.user = ""
        SESSION.plan = ""
        SESSION.started = 0
        SESSION.listeners_registered = False
        self.manager.current = "login"

    def _logout(self, *a):
        self._expire()

    def _upgrade(self, *a):
        self.manager.current = "upgrade"

    def _show(self, key):
        self._active = key
        for k, btn in self.tabs.items():
            if k == key:
                btn.set_colors(PURPLE_2, PURPLE, TEXT)
            else:
                btn.set_colors(PANEL, PANEL_2, MUTED)
        for k, p in self.panels.items():
            p.opacity = 1 if k == key else 0
            p.disabled = (k != key)

    def _field(self, text):
        return Label(text=text, color=MUTED, font_size="12sp",
                     halign="left", valign="middle",
                     size_hint_y=None, height=dp(20),
                     text_size=(dp(300), None))

    def _input(self, hint, multiline=False):
        return TextInput(hint_text=hint, multiline=multiline,
                         size_hint_y=None,
                         height=dp(80) if multiline else dp(46),
                         background_color=PANEL_2, foreground_color=TEXT,
                         cursor_color=PURPLE, padding=[dp(12), dp(12)],
                         font_size="14sp")

    def _result_area(self):
        card = Card(orientation="vertical", padding=dp(12), spacing=dp(6),
                    size_hint_y=None, height=dp(60))
        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        inner.bind(minimum_height=inner.setter("height"))
        card.add_widget(inner)
        return card, inner

    def _render(self, area, r):
        card, box = area
        box.clear_widgets()
        color = {"safe": GREEN, "suspicious": AMBER, "phishing": RED}.get(
            r["verdict"], MUTED)
        box.add_widget(Label(
            text="[b]%s[/b]  ·  score %d/100" % (r["verdict"].upper(), r["score"]),
            markup=True, color=color, font_size="16sp",
            halign="left", size_hint_y=None, height=dp(28),
            text_size=(dp(280), None)))
        if r["recommendations"]:
            box.add_widget(Label(text="[b]What to do[/b]", markup=True,
                                 color=TEXT, font_size="12sp",
                                 halign="left", size_hint_y=None, height=dp(20),
                                 text_size=(dp(280), None)))
            for rec in r["recommendations"]:
                box.add_widget(Label(text="•  " + rec, color=MUTED,
                                     font_size="12sp", halign="left", valign="top",
                                     size_hint_y=None, height=dp(34),
                                     text_size=(dp(280), None)))
        if r["signals"]:
            box.add_widget(Label(text="[b]Signals[/b]", markup=True,
                                 color=TEXT, font_size="12sp",
                                 halign="left", size_hint_y=None, height=dp(20),
                                 text_size=(dp(280), None)))
            for s in r["signals"]:
                box.add_widget(SigChip(s["weight"], s["why"]))

    def _build_message(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8))
        root.add_widget(self._field("Sender (optional)"))
        sender = self._input("+1 555 ... or name@domain.com")
        root.add_widget(sender)
        root.add_widget(self._field("Message body"))
        body = self._input("Paste the SMS here", multiline=True)
        root.add_widget(body)
        area = self._result_area()
        root.add_widget(area[0])
        btn = GradientButton(text="Analyze message", color_a=GREEN, color_b=GREEN_2,
                             size_hint_y=None, height=dp(46))
        def run(*_):
            r = az.analyze_message({"sender": sender.text, "body": body.text})
            self._render(area, r)
        btn.bind(on_release=run)
        root.add_widget(btn)
        scroll = ScrollView()
        scroll.add_widget(area[1])
        root.add_widget(scroll)
        return root

    def _build_call(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8))
        root.add_widget(self._field("Caller number"))
        number = self._input("+44 7000 000000")
        root.add_widget(number)
        root.add_widget(self._field("Transcript (optional)"))
        transcript = self._input("What was said", multiline=True)
        root.add_widget(transcript)
        root.add_widget(self._field("Calls from this number last hour"))
        calls = self._input("0")
        root.add_widget(calls)
        area = self._result_area()
        root.add_widget(area[0])
        btn = GradientButton(text="Analyze call", color_a=GREEN, color_b=GREEN_2,
                             size_hint_y=None, height=dp(46))
        def run(*_):
            try:
                recent = int(calls.text or 0)
            except Exception:
                recent = 0
            r = az.analyze_call({
                "number": number.text,
                "transcript": transcript.text,
                "recent_calls_last_hour": recent,
                "avg_duration_seconds": 5,
                "duration_seconds": 5,
                "caller_spoke_first": True,
            })
            self._render(area, r)
        btn.bind(on_release=run)
        root.add_widget(btn)
        scroll = ScrollView()
        scroll.add_widget(area[1])
        root.add_widget(scroll)
        return root

    def _build_video(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8))
        root.add_widget(self._field("Video link"))
        link = self._input("https://...")
        root.add_widget(link)
        root.add_widget(self._field("Notes / context"))
        notes = self._input("Who sent it, what it claims", multiline=True)
        root.add_widget(notes)
        area = self._result_area()
        root.add_widget(area[0])
        btn = GradientButton(text="Analyze video", color_a=GREEN, color_b=GREEN_2,
                             size_hint_y=None, height=dp(46))
        def run(*_):
            r = az.analyze_video({"link": link.text, "notes": notes.text})
            self._render(area, r)
        btn.bind(on_release=run)
        root.add_widget(btn)
        scroll = ScrollView()
        scroll.add_widget(area[1])
        root.add_widget(scroll)
        return root

    def _build_history(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8))
        header = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        header.add_widget(Label(text="Recent scans", color=MUTED, font_size="13sp",
                                halign="left", valign="middle"))
        header.add_widget(Widget())
        refresh = GradientButton(text="Refresh", color_a=PANEL_2, color_b=PANEL,
                                 text_color=MUTED,
                                 size_hint=(None, 1), width=dp(90))
        header.add_widget(refresh)
        root.add_widget(header)
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        box.bind(minimum_height=box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(box)
        root.add_widget(scroll)

        def load(*_):
            box.clear_widgets()
            path = os.path.join(os.path.expanduser("~"), "antiphish_hits.txt")
            if not os.path.isfile(path):
                box.add_widget(Label(text="No scans yet.", color=MUTED,
                                     size_hint_y=None, height=dp(30)))
                return
            try:
                with open(path, "r", errors="replace") as f:
                    lines = f.readlines()[-60:]
            except Exception:
                lines = []
            for line in reversed(lines):
                parts = line.strip().split("|")
                if len(parts) < 5:
                    continue
                sender, kind, verdict, score, body = parts[:5]
                vcolor = {"safe": GREEN, "suspicious": AMBER,
                          "phishing": RED}.get(verdict, MUTED)
                card = Card(orientation="vertical", padding=dp(10), spacing=dp(4),
                            size_hint_y=None, height=dp(80))
                top = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(6))
                top.add_widget(Label(text="[b]%s[/b]" % verdict.upper(),
                                     markup=True, color=vcolor,
                                     font_size="12sp",
                                     size_hint_x=None, width=dp(90)))
                top.add_widget(Label(text="score " + score, color=MUTED,
                                     font_size="11sp"))
                top.add_widget(Widget())
                top.add_widget(Label(text=kind, color=PURPLE, font_size="11sp"))
                card.add_widget(top)
                card.add_widget(Label(text=sender or "(no sender)", color=TEXT,
                                      font_size="12sp", halign="left",
                                      size_hint_y=None, height=dp(18),
                                      text_size=(dp(300), None)))
                card.add_widget(Label(text=body, color=MUTED, font_size="11sp",
                                      halign="left", size_hint_y=None, height=dp(24),
                                      text_size=(dp(300), None)))
                box.add_widget(card)

        refresh.bind(on_release=load)
        load()
        return root


class UpgradeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(14))

        root.add_widget(Label(text="[b]Upgrade to Paid[/b]", markup=True,
                              font_size="24sp", color=PURPLE,
                              size_hint_y=None, height=dp(40), bold=True))
        root.add_widget(Label(
            text="Free tier: 5-minute sessions, background scanning stops at expiry.\n"
                 "Paid tier: unlimited session, background listeners always on.",
            color=MUTED, font_size="13sp", halign="left", valign="top",
            size_hint_y=None, height=dp(80), text_size=(dp(340), None)))

        free_card = Card(orientation="vertical", padding=dp(14), spacing=dp(6),
                         size_hint_y=None, height=dp(150))
        free_card.add_widget(Label(text="[b]Free[/b]", markup=True, color=MUTED,
                                   font_size="16sp", size_hint_y=None, height=dp(24)))
        free_card.add_widget(Label(text="$0 · 5-min sessions",
                                   color=MUTED, font_size="12sp",
                                   size_hint_y=None, height=dp(20)))
        free_card.add_widget(Label(text="• All four tools\n• Manual checks\n"
                                        "• Scanning stops at 5 min",
                                   color=MUTED, font_size="12sp",
                                   halign="left", size_hint_y=None, height=dp(70),
                                   text_size=(dp(340), None)))
        root.add_widget(free_card)

        paid_card = Card(bg=(0.10, 0.16, 0.12, 1), border=GREEN,
                         orientation="vertical", padding=dp(14), spacing=dp(6),
                         size_hint_y=None, height=dp(150))
        paid_card.add_widget(Label(text="[b]Paid[/b]", markup=True, color=GREEN,
                                   font_size="16sp", size_hint_y=None, height=dp(24)))
        paid_card.add_widget(Label(text="$1 · lifetime key",
                                   color=GREEN, font_size="12sp",
                                   size_hint_y=None, height=dp(20)))
        paid_card.add_widget(Label(text="• Unlimited sessions\n• No timer\n"
                                        "• Background scanning always on",
                                   color=MUTED, font_size="12sp",
                                   halign="left", size_hint_y=None, height=dp(70),
                                   text_size=(dp(340), None)))
        root.add_widget(paid_card)

        root.add_widget(Widget())

        back = GradientButton(text="Back to dashboard",
                              color_a=PANEL_2, color_b=PANEL,
                              text_color=MUTED,
                              size_hint_y=None, height=dp(46))
        back.bind(on_release=lambda *a: setattr(self.manager, "current", "home"))
        root.add_widget(back)

        self.add_widget(root)


class AntiPhishApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(WelcomeScreen(name="welcome"))
        sm.add_widget(PermissionsScreen(name="permissions"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(UpgradeScreen(name="upgrade"))
        sm.current = "login"
        return sm


if __name__ == "__main__":
    AntiPhishApp().run()
