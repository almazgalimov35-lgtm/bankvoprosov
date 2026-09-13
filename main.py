# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.resources import resource_find
from collections import defaultdict
import json

Window.clearcolor = (1, 1, 1, 1)

PAGE_SIZE = 10
MAX_SUGGESTIONS = 8
QUICK_ROWS = [
    ["ПДК", "СИЗОД", "взрыв", "отравление"],
    ["50", "первая помощь", "наряд", "эвакуация"],
    ["коррозия", "растворимость", "контроль", "замер"],
]


def load_json():
    path = resource_find("data.json")
    if not path:
        raise FileNotFoundError("data.json не найден")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_index(raw):
    data = defaultdict(list)
    all_items = []
    wc = defaultdict(int)
    for code, q, a, sec in raw:
        data[sec].append((code, q, a))
        all_items.append((sec, code, q, a))
        clean = q.lower()
        for ch in ',.()[]{};:!?"\'«»':
            clean = clean.replace(ch, " ")
        for w in clean.split():
            if len(w) >= 3:
                wc[w] += 1
    sections = list(data.keys())
    popular = sorted(wc.keys(), key=lambda w: -wc[w])[:500]
    return data, all_items, sections, popular, wc


class MainApp(App):
    def build(self):
        Window.softinput_mode = "below_target"
        self.current_section = None
        self.current_page = 0
        self.results = []
        self.mode = "menu"
        self._t = None

        self.root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(5))
        self.loading = Label(text="Загрузка...", font_size=sp(20), bold=True,
                             color=(0.1, 0.1, 0.4, 1))
        self.root.add_widget(self.loading)

        Window.bind(on_keyboard=self.on_keyboard)
        Clock.schedule_once(self._load_data, 0.15)
        return self.root

    def _load_data(self, dt):
        try:
            raw = load_json()
        except Exception as e:
            self.loading.text = "Ошибка:\n" + str(e)
            return
        self.data, self.all_items, self.sections, self.popular, self.word_counter = build_index(raw)
        self.root.remove_widget(self.loading)
        self._build_ui()
        self.show_sections()

    def _build_ui(self):
        self.title_label = Label(text="Выбери раздел", font_size=sp(19),
                                 size_hint_y=None, height=dp(40), bold=True,
                                 color=(0.05, 0.05, 0.35, 1))
        self.root.add_widget(self.title_label)

        sr = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        self.search_input = TextInput(hint_text="Поиск...", multiline=False,
                                      font_size=sp(17), size_hint_x=0.7,
                                      background_color=(0.95, 0.95, 0.95, 1),
                                      foreground_color=(0, 0, 0, 1),
                                      input_type="text", write_tab=False)
        self.search_input.bind(text=self.on_search_text)

        bc = Button(text="X", font_size=sp(22), size_hint_x=0.15,
                    background_normal="", background_color=(0.8, 0.3, 0.3, 1))
        bc.bind(on_press=self.clear_search)
        bb = Button(text="=", font_size=sp(22), size_hint_x=0.15,
                    background_normal="", background_color=(0.3, 0.4, 0.7, 1))
        bb.bind(on_press=self.show_sections)
        sr.add_widget(self.search_input)
        sr.add_widget(bc)
        sr.add_widget(bb)
        self.root.add_widget(sr)

        self.sugg_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                  height=0, spacing=dp(2))
        self.root.add_widget(self.sugg_box)

        for row in QUICK_ROWS:
            qr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(4))
            for w in row:
                b = Button(text=w, font_size=sp(13), background_normal="",
                           background_color=(0.9, 0.7, 0.3, 1), color=(0, 0, 0, 1))
                b.bind(on_press=lambda x, ww=w: self.quick_search(ww))
                qr.add_widget(b)
            self.root.add_widget(qr)

        self.scroll = ScrollView(bar_width=dp(3))
        self.content = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=dp(4))
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        self.root.add_widget(self.scroll)

        nav = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        self.btn_prev = Button(text="<", font_size=sp(16), background_normal="",
                               background_color=(0.5, 0.5, 0.7, 1))
        self.btn_prev.bind(on_press=self.prev_page)
        self.btn_next = Button(text=">", font_size=sp(16), background_normal="",
                               background_color=(0.5, 0.5, 0.7, 1))
        self.btn_next.bind(on_press=self.next_page)
        nav.add_widget(self.btn_prev)
        nav.add_widget(self.btn_next)
        self.root.add_widget(nav)

    def on_keyboard(self, window, key, *args):
        if key == 27:
            if self.mode in ("search", "section"):
                self.show_sections()
                return True
        return False

    def _text_w(self):
        w = self.scroll.width - dp(30)
        return w if w > dp(120) else Window.width - dp(40)

    def show_sections(self, *a):
        self.mode = "menu"
        self.search_input.text = ""
        self.search_input.focus = False
        self.hide_sugg()
        self.title_label.text = "Выбери раздел"
        self.content.clear_widgets()
        for i, sec in enumerate(self.sections, 1):
            b = Button(text="[" + str(i) + "] " + sec + " (" + str(len(self.data[sec])) + ")",
                       font_size=sp(18), size_hint_y=None, height=dp(70),
                       background_normal="", background_color=(0.25, 0.65, 0.4, 1),
                       color=(1, 1, 1, 1))
            b.bind(on_press=lambda x, s=sec: self.open_section(s))
            self.content.add_widget(b)
        self.scroll.scroll_y = 1
        self.set_nav(False, False)

    def open_section(self, s):
        self.mode = "section"
        self.current_section = s
        self.current_page = 0
        self.search_input.text = ""
        self.search_input.focus = False
        self.hide_sugg()
        self.render_page()

    def hide_sugg(self):
        self.sugg_box.clear_widgets()
        self.sugg_box.height = 0

    def show_sugg(self, ms):
        self.sugg_box.clear_widgets()
        if not ms:
            self.sugg_box.height = 0
            return
        for w in ms[:MAX_SUGGESTIONS]:
            b = Button(text="  " + w + " (" + str(self.word_counter.get(w, 0)) + ")",
                       font_size=sp(15), size_hint_y=None, height=dp(34),
                       background_normal="", background_color=(0.75, 0.85, 0.95, 1),
                       color=(0, 0, 0, 1))
            b.bind(on_press=lambda x, ww=w: self.pick_sugg(ww))
            self.sugg_box.add_widget(b)
        n = min(len(ms), MAX_SUGGESTIONS)
        self.sugg_box.height = n * dp(34) + (n - 1) * dp(2)

    def pick_sugg(self, w):
        self.search_input.text = w
        self.search_input.focus = False
        self.hide_sugg()
        self.run_search(w)

    def on_search_text(self, inst, val):
        if self._t:
            self._t.cancel()
        t = val.strip().lower()
        if len(t) < 2:
            self.hide_sugg()
            if self.mode == "search":
                self.show_sections()
            return
        ms = [w for w in self.popular if w.startswith(t)]
        self.show_sugg(ms)
        self._t = Clock.schedule_once(lambda dt: self.run_search(t), 0.35)

    def run_search(self, q):
        ql = q.lower().strip()
        self.mode = "search"
        self.current_page = 0
        self.results = []
        for sec, c, qq, a in self.all_items:
            if ql in qq.lower() or ql in a.lower() or ql in c.lower():
                self.results.append((sec, c, qq, a))
        self.render_search()

    def quick_search(self, w):
        self.search_input.text = w
        self.search_input.focus = False
        self.hide_sugg()
        self.run_search(w)

    def clear_search(self, *a):
        self.search_input.text = ""
        self.search_input.focus = False
        self.hide_sugg()
        self.show_sections()

    def _item(self, sec, c, q, a, show_sec):
        w = self._text_w()
        if show_sec:
            self.content.add_widget(Label(text="Раздел: " + sec, font_size=sp(13),
                                          size_hint_y=None, height=dp(22), halign="left",
                                          text_size=(w, None), padding=(dp(10), 0),
                                          color=(0.3, 0.3, 0.3, 1)))
        if c:
            self.content.add_widget(Label(text="Код: " + c, font_size=sp(14),
                                          size_hint_y=None, height=dp(24), halign="left",
                                          text_size=(w, None), padding=(dp(10), 0),
                                          color=(0.2, 0.2, 0.2, 1)))
        ql = Label(text="ВОПРОС: " + q, font_size=sp(17), size_hint_y=None,
                   halign="left", valign="top", text_size=(w, None),
                   padding=(dp(10), dp(8)), color=(0, 0, 0, 1))
        ql.bind(texture_size=lambda l, v: setattr(l, "height", v[1] + dp(20)))
        self.content.add_widget(ql)
        al = Label(text="ОТВЕТ: " + a, font_size=sp(17), size_hint_y=None,
                   halign="left", valign="top", text_size=(w, None),
                   padding=(dp(10), dp(8)), color=(0.1, 0.3, 0.1, 1))
        al.bind(texture_size=lambda l, v: setattr(l, "height", v[1] + dp(20)))
        self.content.add_widget(al)
        self.content.add_widget(Label(text="-" * 20, font_size=sp(12),
                                      size_hint_y=None, height=dp(20),
                                      color=(0.6, 0.6, 0.6, 1)))

    def render_search(self):
        t = len(self.results)
        tp = max(1, (t + PAGE_SIZE - 1) // PAGE_SIZE)
        self.title_label.text = "Найдено: " + str(t) + " (" + str(self.current_page + 1) + "/" + str(tp) + ")"
        self.content.clear_widgets()
        if t == 0:
            self.content.add_widget(Label(text="Ничего не найдено", font_size=sp(18),
                                          size_hint_y=None, height=dp(80),
                                          color=(0.5, 0.1, 0.1, 1)))
            self.set_nav(False, False)
            return
        s = self.current_page * PAGE_SIZE
        e = min(s + PAGE_SIZE, t)
        for i in range(s, e):
            sec, c, q, a = self.results[i]
            self._item(sec, c, q, a, True)
        self.set_nav(self.current_page > 0, self.current_page < tp - 1)
        self.scroll.scroll_y = 1

    def render_page(self):
        sec = self.current_section
        qs = self.data[sec]
        t = len(qs)
        tp = max(1, (t + PAGE_SIZE - 1) // PAGE_SIZE)
        self.title_label.text = sec + " (" + str(self.current_page + 1) + "/" + str(tp) + ")"
        self.content.clear_widgets()
        s = self.current_page * PAGE_SIZE
        e = min(s + PAGE_SIZE, t)
        for i in range(s, e):
            c, q, a = qs[i]
            self.content.add_widget(Label(text="ВОПРОС " + str(i + 1) + ":",
                                          font_size=sp(17), size_hint_y=None, height=dp(24),
                                          bold=True, halign="left",
                                          text_size=(self._text_w(), None),
                                          padding=(dp(10), 0),
                                          color=(0.05, 0.05, 0.35, 1)))
            self._item("", c, q, a, False)
        self.set_nav(self.current_page > 0, self.current_page < tp - 1)
        self.scroll.scroll_y = 1

    def next_page(self, *a):
        if self.mode == "section":
            t = len(self.data[self.current_section])
        elif self.mode == "search":
            t = len(self.results)
        else:
            return
        tp = (t + PAGE_SIZE - 1) // PAGE_SIZE
        if self.current_page < tp - 1:
            self.current_page += 1
            (self.render_page if self.mode == "section" else self.render_search)()

    def prev_page(self, *a):
        if self.current_page > 0:
            self.current_page -= 1
            (self.render_page if self.mode == "section" else self.render_search)()

    def set_nav(self, p, n):
        self.btn_prev.disabled = not p
        self.btn_prev.opacity = 1 if p else 0.3
        self.btn_next.disabled = not n
        self.btn_next.opacity = 1 if n else 0.3


if __name__ == "__main__":
    MainApp().run()
