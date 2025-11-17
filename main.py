# main.py
# SMS Reader App (Kivy) - reads SMS inbox, extracts UTR, amount, date/time and shows transactions
# Passcode: 9398
#
# Requirements: kivy, pyjnius, plyer
#
# Notes:
# - Run on an Android device (WSL Ubuntu won't access SMS)
# - You must allow the READ_SMS permission when the app asks for it

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import mainthread
from kivy.properties import ListProperty, StringProperty
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput

import re
from datetime import datetime

# Android-specific imports
try:
    from jnius import autoclass, cast
    from android import mActivity
    from android.permissions import request_permissions, Permission, check_permission
    ANDROID = True
except Exception:
    ANDROID = False

# TTS (optional) - plyer has a tts facade on many devices
try:
    from plyer import tts
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

KV = r"""
<RootWidget>:
    orientation: "vertical"
    padding: dp(8)
    spacing: dp(8)

    BoxLayout:
        size_hint_y: None
        height: dp(70)
        spacing: dp(8)
        TextInput:
            id: passcode
            hint_text: "Enter passcode to view SMS"
            password: True
            multiline: False
            font_size: '18sp'
            on_text_validate: root.check_passcode()
        Button:
            text: "Unlock"
            size_hint_x: None
            width: dp(120)
            on_release: root.check_passcode()

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)
        Button:
            text: "Refresh SMS"
            on_release: root.refresh_sms()
        Label:
            id: status_label
            text: root.status_text
            size_hint_x: 1
            halign: 'left'
            valign: 'middle'
            text_size: self.size

    ScrollView:
        id: scroll
        do_scroll_x: False
        GridLayout:
            id: sms_list
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(6)
"""

# Helper regex patterns
UTR_RE = re.compile(r'\bUTR[:\s\-]*([A-Za-z0-9]{6,30})', re.IGNORECASE)
AMOUNT_RE = re.compile(r'(?:INR|Rs\.?|Rs|₹)\s?([0-9\.,]+(?:\.\d{1,2})?)', re.IGNORECASE)
ALT_AMT_RE = re.compile(r'([0-9\.,]+)\s?(?:INR|Rs\.?|Rs|₹)\b', re.IGNORECASE)


class RootWidget(BoxLayout):
    transactions = ListProperty([])
    status_text = StringProperty("Locked")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.unlocked = False

    def check_passcode(self):
        txt = self.ids.passcode.text.strip()
        if txt == "9398":
            self.unlocked = True
            self.status_text = "Unlocked — press Refresh SMS"
            # automatically try to read sms once unlocked
            self.refresh_sms()
        else:
            self.status_text = "Wrong passcode"

    def refresh_sms(self):
        if not self.unlocked:
            self.status_text = "Enter passcode first"
            return
        self.status_text = "Requesting permission..." if ANDROID else "Not Android: can't read SMS here"
        if ANDROID:
            # Check permission first
            granted = check_permission(Permission.READ_SMS)
            if granted:
                self.status_text = "Reading SMS..."
                self._read_sms_and_display()
            else:
                # request permission, callback will call read
                request_permissions([Permission.READ_SMS], self._perm_callback)
        else:
            self.status_text = "This function runs only on Android device."

    def _perm_callback(self, permissions, grants):
        # callback invoked after permission request
        # grants is a list of booleans
        try:
            if grants and grants[0]:
                self.status_text = "Permission granted. Reading SMS..."
                self._read_sms_and_display()
            else:
                self.status_text = "Permission denied. Can't read SMS."
        except Exception as e:
            self.status_text = f"Permission error: {e}"

    @mainthread
    def _display_transactions(self, transactions):
        # Clear old
        container = self.ids.sms_list
        container.clear_widgets()
        if not transactions:
            self.ids.status_label.text = "No transactions found"
            return
        for t in transactions:
            # create a manual row (avoid relying on Builder.template)
            row = BoxLayout(orientation='vertical', size_hint_y=None)
            row.padding = dp(8)
            row.height = dp(120)

            title_lbl = Label(text=t['title'], size_hint_y=None, height=dp(24), text_size=(self.width - dp(16), None), halign='left', valign='middle')
            subtitle_lbl = Label(text=t['subtitle'], size_hint_y=None, height=dp(20), text_size=(self.width - dp(16), None), halign='left', valign='middle')
            extra_lbl = Label(text=t['extra'], size_hint_y=None, height=dp(36), text_size=(self.width - dp(16), None), halign='left', valign='top')

            speak_btn = Button(text="Speak this transaction", size_hint_y=None, height=dp(36))
            # Bind with a default argument to capture text per-row
            speak_btn.bind(on_release=lambda inst, txt=t: App.get_running_app().speak_transaction(txt['title'] + ". " + txt['subtitle'] + ". " + txt['extra']))

            row.add_widget(title_lbl)
            row.add_widget(subtitle_lbl)
            row.add_widget(extra_lbl)
            row.add_widget(speak_btn)
            container.add_widget(row)
        self.ids.status_label.text = "Done"

    def _read_sms_and_display(self):
        # Run reading logic synchronously (this is quick, but may be slow if many messages)
        try:
            transactions = self._read_sms()
            self.transactions = transactions
            self._display_transactions(transactions)
        except Exception as e:
            self.ids.status_label.text = f"Error reading SMS: {e}"

    def _read_sms(self):
        """
        Use Android content resolver to read SMS inbox and parse messages.
        Returns list of dicts: {'title': sender, 'subtitle': time_str, 'extra': parsed_info}
        """
        if not ANDROID:
            # For testing on desktop simulate some entries
            sample = [{
                'title': 'AXISBK',
                'subtitle': '2025-11-14 12:00',
                'extra': 'Amount: INR 1,234.00 UTR: ABCD123456'
            }]
            return sample

        transactions = []
        try:
            # Prepare Android classes
            Uri = autoclass('android.net.Uri')
            String = autoclass('java.lang.String')
            Cursor = autoclass('android.database.Cursor')  # for type only
            content_resolver = mActivity.getContentResolver()
            sms_uri = Uri.parse("content://sms/inbox")
            # projection None = all columns
            cursor = content_resolver.query(sms_uri, None, None, None, "date DESC")
            if cursor is None:
                return []

            # column names we will use
            # columns vary; typical: _id, address, date, body, person, type
            idx_address = cursor.getColumnIndex("address")
            idx_date = cursor.getColumnIndex("date")
            idx_body = cursor.getColumnIndex("body")

            # iterate
            if cursor.moveToFirst():
                while True:
                    try:
                        address = cursor.getString(idx_address) if idx_address != -1 else ""
                        body = cursor.getString(idx_body) if idx_body != -1 else ""
                        date_ms = cursor.getLong(idx_date) if idx_date != -1 else 0
                    except Exception:
                        # Some devices may throw on getString if column not present
                        address = ""
                        body = ""
                        date_ms = 0

                    date_str = ""
                    try:
                        date_str = datetime.fromtimestamp(date_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        date_str = str(date_ms)

                    # parse for UTR
                    utr_match = UTR_RE.search(body)
                    utr = utr_match.group(1) if utr_match else ""

                    # parse amount
                    amt_match = AMOUNT_RE.search(body)
                    if not amt_match:
                        amt_match = ALT_AMT_RE.search(body)
                    amt = amt_match.group(1) if amt_match else ""

                    # create summary
                    title = f"From: {address}"
                    subtitle = f"Date: {date_str}"
                    extra_parts = []
                    if amt:
                        extra_parts.append(f"Amount: {amt}")
                    if utr:
                        extra_parts.append(f"UTR: {utr}")
                    # include some of the body (short)
                    snippet = body.strip().replace("\n", " ")
                    if len(snippet) > 120:
                        snippet = snippet[:117] + "..."
                    extra = " | ".join(extra_parts + [snippet])

                    transactions.append({
                        'title': title,
                        'subtitle': subtitle,
                        'extra': extra
                    })

                    # move to next
                    if not cursor.moveToNext():
                        break
            # close cursor
            try:
                cursor.close()
            except Exception:
                pass

        except Exception as exc:
            # bubble up error
            raise exc

        return transactions


class SMSApp(App):
    def build(self):
        self.title = "SMS Reader"
        Builder.load_string(KV)
        return RootWidget()

    def speak_transaction(self, text):
        # use plyer tts if available, otherwise print (or attempt Android TTS)
        if TTS_AVAILABLE:
            try:
                tts.speak(text)
            except Exception:
                print("TTS error")
        else:
            # fallback: try Android TTS directly if pyjnius available
            if ANDROID:
                try:
                    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                    Locale = autoclass('java.util.Locale')
                    PythonActivity = mActivity
                    tts_client = TextToSpeech(PythonActivity, None)
                    # We won't block to set language reliably; set a best-effort language
                    # This is a lightweight fallback and may not always speak
                except Exception:
                    print("No TTS available")
            print("TTS not available. Text:", text)


if __name__ == '__main__':
    SMSApp().run()
