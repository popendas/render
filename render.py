import PySimpleGUI as sg
import re
import threading
from time import sleep
import keyboard
import mouse
from typing import Optional, Callable

TRIGGER = "trigger"
TARGET = "target"
LEFT = mouse.LEFT
MIDDLE = mouse.MIDDLE
RIGHT = mouse.RIGHT
INTERVAL = "interval"
DELAY = "starttime"
ADD = "add"
DELETE = "delete"
TITLE = "れんだー"

INIT_VALUES = {
    TRIGGER: "F8",
    TARGET: "対象",
    LEFT: False,
    MIDDLE: False,
    RIGHT: False,
    INTERVAL: 100,
    DELAY: 1000,
}

button_list = {TRIGGER, TARGET, LEFT, MIDDLE, RIGHT, ADD, DELETE}
input_list = {INTERVAL, DELAY}


class repeat(threading.Thread):
    """連打を並行して行うクラス
    """

    def __init__(self, window: sg.Window):
        self._window = window
        self.repeated = False
        super().__init__()

    def run(self):
        """ウィンドウで指定された値を連打します
        """
        event, values = self._window.read(0)

        # インターバルをセット
        if len(values[INTERVAL]) > 0:
            interval = int(values[INTERVAL]) / 1000
        else:
            return

        # ディレイをセット
        if len(values[DELAY]) > 0:
            delay = int(values[DELAY]) / 1000
        else:
            # ディレイが未入力
            delay = 0

        print("連打開始", "interval:" + str(interval), "delay:" + str(delay))

        press_list = []
        # クリックするマウスのボタンをセット
        print(values)
        if values[RIGHT]:
            press_list.append(lambda: mouse.click(button=RIGHT))
        if values[MIDDLE]:
            press_list.append(lambda: mouse.click(button=MIDDLE))
        if values[LEFT]:
            press_list.append(lambda: mouse.click(button=LEFT))
        # クリックするキーをセット
        press_key = self._window[TARGET].ButtonText
        if press_key != INIT_VALUES[TARGET]:
            def pressed():
                keyboard.press(press_key)
                keyboard.release(press_key)
            press_list.append(pressed)

        self.repeated = True
        # ディレイ分待機した後連打開始
        sleep(delay)
        while self.repeated:
            for press_button in press_list:
                press_button()
            # print("押した")
            sleep(interval)

        print("連打終わり")
        return

    def stop(self):
        """連打を終了させます
        """
        self.repeated = False


class Main():

    def __init__(self, layout: list):

        sg.theme('SystemDefault')
        self._window = sg.Window(TITLE, layout, finalize=True, return_keyboard_events=True, margins=(0,0))
        self._event: str
        self._values: dict
        self._hotkey: Optional[Callable[[], None]] = None
        self.repeated_class = self.get_repeated_class()
        self._handler = {
            DELAY: self._to_int,
            INTERVAL: self._to_int,
            TRIGGER: self._replace,
            TARGET: self._replace, }
        # 変換が必要な文字の対応表
        self._keyboard = {
            "\r": "enter",
            "Control_L": "Control",
            "Control_R": "Control",
            "\t": "Tab",
            "Shift_L": "Shift",
            "Shift_R": "Shift",
            "Alt_L": "Alt",
            "Alt_R": "Alt",
            "Win_L": "Win",
            "Win_R": "Win"}
        self._change_hotkey(str(INIT_VALUES[TRIGGER]))

    def get_repeated_class(self):
        """連打を行うマルチスレッドクラスを生成して返します
        """
        # 関数をマルチスレッド化する
        return repeat(self._window)

    def _start(self):
        """ウィンドウの設定に従って連打を開始します
        """
        del self.repeated_class
        self.repeated_class = self.get_repeated_class()
        self._window.set_title(TITLE + "(連打中)")
        self.repeated_class.start()

    def _end(self):
        """連打を終了させます
        """
        self.repeated_class.stop()
        if self._event is not None:
            self._window.set_title(TITLE)
        #     self._all_disabled(False)

    def _check_int(self, nums: str) -> str:
        """文字列から数字のみを抽出します

        Args:
            nums (str): 渡す文字列

        Returns:
            str: 数字のみになった文字列
        """
        try:
            num = int(nums)
            if num <= 0 or num > 99999:
                nums = "1"
        except ValueError:
            nums = "".join(re.findall(r"[0-9]+", nums))
        return nums

    def _to_int(self, target: str):
        """_windowの要素から数字にのみを抽出しセットします

        Args:
            target (str): 対象となる_window要素
        """
        self._window[target].update(self._check_int(self._values[target]))

    def _all_disabled(self, flg: bool):
        """すべてのボタンとinput要素のdisabled属性を設定します

        Args:
            flg (bool): 設定するbool値
        """
        for button in button_list:
            self._window[button].update(disabled=flg)
        for input in input_list:
            self._window[input].update(disabled=flg)
            self._window[input].block_focus()

    def _change_hotkey(self, hotkey: Optional[str]) -> bool:
        """トリガーとなるホットキーを変更します,Noneを渡すとホットキーを消します

        Args:
            hotkey (str): 変更したいホットキー

        Returns:
            bool: ホットキーに設定できたらTrue、できなかったらFalse
        """
        if self._hotkey is not None:
            # 設定されているホットキーを削除
            keyboard.remove_hotkey(self._hotkey)
            self._hotkey = None

        if hotkey is None:
            # Noneを渡されたなら返す
            return True

        result = True
        try:
            # ホットキーを設定する
            self._hotkey = keyboard.add_hotkey(hotkey, self._change_repeat)
        except ValueError:
            # 登録に失敗したらNoneをセットしてFalseを返す
            self._hotkey = None
            result = False
        return result

    def _change_repeat(self):
        """連打モードを切り替えます
        """
        if self.repeated_class.repeated:
            print("end")
            self._end()
        else:
            print("start")
            self._start()

    def _replace(self, target: str):
        """指定したボタンに入力された値をセットします

        Args:
            target (TARGET or TRIGGER): 対象となる_window要素
        """
        # キーボード入力を取得
        if TRIGGER == target:
            self._change_hotkey(None)
        self._all_disabled(True)
        self._window[target].update(disabled=False)
        eventl, valuesl = self._window.read()
        if eventl == sg.WINDOW_CLOSED:
            # ウィンドウを消したなら戻す
            return

        # キー名を取り出す
        eventl = eventl.split(":", 1)[0]
        if eventl in self._keyboard:
            # 別名を指定してあるならそれを使う
            eventl = self._keyboard[eventl]

        # ターゲットではないボタンを取得
        non_target = TRIGGER if target == TARGET else TARGET

        if target == eventl:
            # キャンセルならデフォルトに戻す
            eventl = INIT_VALUES[target]
            if self._window[non_target].ButtonText == eventl:
                # デフォルトもかぶりなら二つとも戻す
                self._window[non_target].update(INIT_VALUES[non_target])

        # もう一つのボタンとキーが
        if self._window[non_target].ButtonText != eventl:
            # かぶって無かったら表示の更新
            self._window[target].update(eventl)

            if TRIGGER == target:
                # TRIGGERならホットキーを更新
                if not self._change_hotkey(eventl):
                    # 変更に失敗したら表示を消す
                    self._window[target].update("")

        self._all_disabled(False)

    def mainloop(self):
        """イベントループを開始します
        """
        self._event, self._values = self._window.read(0)
        # イベントループ
        while True:
            # self._all_disabled(True)
            self._event, self._values = self._window.read()
            print("Event:" + str(self._event))

            if self._event == sg.WINDOW_CLOSED:
                break

            self._event = self._event.split(":", 1)[0]

            # イベントに応じて処理の切り替え
            if self._event in self._handler:
                self._handler[self._event](self._event)
        # 終了
        print("すべての終わり")

        self._end()
        self._window.close()


# レイアウト
# 連打機能の要素
right = [
    [sg.Text("トリガー", size=(8, 1), justification='c', pad=((3, 2), (2, 2))), sg.Text("対象", size=(8, 1), justification='c', pad=((25, 2), (2, 2)))],
    [sg.Button(INIT_VALUES[TRIGGER], size=(8, 4), key=TRIGGER, pad=((2, 13), (2, 2))), sg.Button(INIT_VALUES[TARGET], size=(8, 4), key=TARGET, pad=((10, 2), (2, 2)))],
    [sg.Checkbox('左', key=LEFT, size=(1, 1), pad=((3, 30), (10, 2))), sg.Checkbox('中', key=MIDDLE, size=(1, 1), pad=((0, 30), (10, 2))), sg.Checkbox('右', key=RIGHT, size=(1, 1), pad=((0, 1), (10, 2)))],
    [sg.Text("開始まで", size=(8, 1), justification='c', pad=((3, 2), (2, 2))), sg.Text("間隔", size=(8, 1), justification='c', pad=((25, 2), (2, 2)))],
    [sg.Input(INIT_VALUES[DELAY], size=(9, 1), pad=((3, 3), (2, 2)), enable_events=True, key=DELAY), sg.Input(INIT_VALUES[INTERVAL], size=(9, 1), pad=((25, 2), (2, 2)), enable_events=True, key=INTERVAL)], ]

# プリセットの要素
preset_header = ["スイッチ", "対象", "開始まで", "間隔"]
preset_list = [
    ["F8", "e", "3", "1"],
    ["F8", "a", "3", "5"]]

left = [
    [sg.Table(preset_list, headings=preset_header, size=(300, 8))],
    [sg.Button("追加", key=ADD), sg.Button("削除", key=DELETE)]
]

layout_main = [sg.Column(right, background_color="#000000", size=(175, 200), pad=(0, 0), justification='c')]
# 追加するかもしれないプリセット機能のレイアウト
# layout_main.append(sg.Column(left, background_color="#ff0000", size=(150, 200), pad=(0, 0)))
layout = [
    [sg.Button(size=(0, 0), visible=False)],  # ボタンの枠けし
    layout_main
]

main = Main(layout)
main.mainloop()
