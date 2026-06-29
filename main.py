from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
import json, os

# Optional share support
try:
    from plyer import share
    HAS_SHARE = True
except ImportError:
    HAS_SHARE = False
    from kivy.core.clipboard import Clipboard

Window.softinput_mode = 'below_target'

KV = '''
MDScreen:
    MDBoxLayout:
        orientation: "vertical"

        # Toolbar
        MDTopAppBar:
            title: "Love Notes Journal"
            elevation: 2
            left_action_items: [["menu", lambda x: None]]
            right_action_items: [["export-variant", lambda x: app.share_all()]]

        # Main content
        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: dp(16)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

                # Selected note preview
                MDLabel:
                    text: "Selected Note:"
                    font_style: "H6"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDCard:
                    size_hint_y: None
                    height: dp(100)
                    padding: dp(12)
                    MDLabel:
                        id: selected_note
                        text: app.current_note if app.current_note else "Tap a note to edit/view ❤️"
                        halign: "center"
                        valign: "center"

                # Input & action row
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(8)

                    MDTextField:
                        id: note_input
                        hint_text: "Type a new love note..."
                        multiline: False
                        size_hint_x: 0.7

                    MDFillRoundFlatButton:
                        id: save_btn
                        text: "Save"
                        size_hint_x: 0.3
                        on_release: app.save_note(note_input.text)

                # Cancel edit (visible only when editing)
                MDFlatButton:
                    id: cancel_btn
                    text: "Cancel Edit"
                    size_hint_y: None
                    height: dp(36)
                    opacity: 0 if app.edit_idx < 0 else 1
                    disabled: app.edit_idx < 0
                    on_release: app.cancel_edit()

                MDSeparator:

                # Search
                MDTextField:
                    id: search_input
                    hint_text: "Search notes..."
                    size_hint_y: None
                    height: dp(40)
                    on_text: app.filter_notes(self.text)

                # Notes list
                MDList:
                    id: notes_list
                    size_hint_y: None
                    height: self.minimum_height
'''

class NoteListItem(MDBoxLayout):
    """Custom list item with note text, date, and action icons."""
    def __init__(self, note_data, idx, app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = [dp(8), dp(4)]
        self.spacing = dp(8)

        # Text area (click to select)
        text_box = MDBoxLayout(orientation='vertical', size_hint_x=0.7)
        title = MDLabel(
            text=note_data['text'][:40] + '...' if len(note_data['text']) > 40 else note_data['text'],
            font_style='Subtitle1',
            halign='left',
            valign='center',
            size_hint_y=0.6
        )
        date = MDLabel(
            text=note_data['date'],
            font_style='Caption',
            halign='left',
            valign='center',
            size_hint_y=0.4,
            theme_text_color='Secondary'
        )
        text_box.add_widget(title)
        text_box.add_widget(date)
        text_box.bind(on_touch_down=lambda x, touch: app.select_note(idx) if text_box.collide_point(*touch.pos) else None)
        self.add_widget(text_box)

        # Icons
        icon_box = MDBoxLayout(size_hint_x=0.3, spacing=dp(4), orientation='horizontal')
        for icon, action in [
            ('pencil', lambda x: app.edit_note(idx)),
            ('delete', lambda x: app.confirm_delete(idx)),
            ('share-variant', lambda x: app.share_note(idx))
        ]:
            btn = MDIconButton(icon=icon, size_hint=(None, None), size=(dp(40), dp(40)))
            btn.bind(on_release=action)
            icon_box.add_widget(btn)
        self.add_widget(icon_box)

class LoveApp(MDApp):
    current_note = StringProperty("")
    notes_data = ListProperty([])      # full list
    filtered_data = ListProperty([])   # after search
    edit_idx = NumericProperty(-1)     # -1 = new mode
    dialog = None
    search_text = StringProperty("")

    def build(self):
        self.title = "Love Notes"
        self.theme_cls.primary_palette = "Pink"
        return Builder.load_string(KV)

    def on_start(self):
        self.load_all_notes()
        self.filtered_data = self.notes_data[:]
        self.refresh_list()

    def get_path(self):
        if platform == 'android':
            ext = os.environ.get('EXTERNAL_STORAGE', '/storage/emulated/0')
            data_dir = os.path.join(ext, "MOI")
        else:
            data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "notes.json")

    def load_all_notes(self):
        try:
            with open(self.get_path(), 'r', encoding='utf-8') as f:
                self.notes_data = json.load(f)
            if self.notes_data:
                self.current_note = self.notes_data[-1]['text']
        except:
            self.notes_data = []
        self.filtered_data = self.notes_data[:]

    def save_data(self):
        with open(self.get_path(), 'w', encoding='utf-8') as f:
            json.dump(self.notes_data, f, ensure_ascii=False, indent=2)

    def filter_notes(self, text):
        self.search_text = text.strip().lower()
        if not self.search_text:
            self.filtered_data = self.notes_data[:]
        else:
            self.filtered_data = [n for n in self.notes_data if self.search_text in n['text'].lower()]
        self.refresh_list()

    def refresh_list(self):
        lst = self.root.ids.notes_list
        lst.clear_widgets()
        # Show filtered list, newest first
        for i, note in enumerate(reversed(self.filtered_data)):
            real_idx = len(self.notes_data) - 1 - i
            item = NoteListItem(note, real_idx, self)
            lst.add_widget(item)
        lst.height = max(dp(60), len(self.filtered_data) * dp(60))

    def select_note(self, idx):
        self.current_note = self.notes_data[idx]['text']
        self.root.ids.selected_note.text = self.current_note

    def edit_note(self, idx):
        self.edit_idx = idx
        self.root.ids.note_input.text = self.notes_data[idx]['text']
        self.root.ids.save_btn.text = "Update"
        self.root.ids.cancel_btn.opacity = 1
        self.root.ids.cancel_btn.disabled = False
        self.current_note = self.notes_data[idx]['text']

    def cancel_edit(self):
        self.edit_idx = -1
        self.root.ids.note_input.text = ""
        self.root.ids.save_btn.text = "Save"
        self.root.ids.cancel_btn.opacity = 0
        self.root.ids.cancel_btn.disabled = True
        self.root.ids.search_input.text = ""  # clear search to show all
        self.filter_notes("")

    def save_note(self, text):
        text = text.strip()
        if not text:
            return self.show("Type something first")

        if self.edit_idx >= 0:  # update
            self.notes_data[self.edit_idx]['text'] = text
            self.notes_data[self.edit_idx]['date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            msg = "Updated ✅"
            self.cancel_edit()  # resets UI
        else:  # new
            note = {'text': text, 'date': datetime.now().strftime('%Y-%m-%d %H:%M')}
            self.notes_data.append(note)
            msg = "Saved ❤️"
            self.root.ids.note_input.text = ""

        self.save_data()
        self.current_note = text
        self.root.ids.selected_note.text = text
        self.filter_notes(self.search_text)  # refresh filtered list
        self.show(msg)

    def confirm_delete(self, idx):
        def do_delete(x):
            self.dialog.dismiss()
            del self.notes_data[idx]
            self.save_data()
            if self.edit_idx == idx:
                self.cancel_edit()
            self.filter_notes(self.search_text)
            self.show("Deleted 🗑️")

        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            text="Delete this note?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Delete", on_release=do_delete)
            ]
        )
        self.dialog.open()

    def share_note(self, idx):
        text = self.notes_data[idx]['text']
        if HAS_SHARE:
            share.share(text=text)
        else:
            Clipboard.copy(text)
            self.show("Copied to clipboard 📋")

    def share_all(self):
        if not self.notes_data:
            return self.show("No notes to share")
        all_text = "\n\n---\n\n".join([f"{n['text']}\n({n['date']})" for n in self.notes_data])
        if HAS_SHARE:
            share.share(text=all_text)
        else:
            Clipboard.copy(all_text)
            self.show("All notes copied to clipboard 📋")

    def show(self, msg):
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            text=msg,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()

if __name__ == "__main__":
    LoveApp().run()