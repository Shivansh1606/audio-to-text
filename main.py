import os
import queue
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock
from datetime import datetime

Window.clearcolor = (0.95, 0.95, 1, 1)
Window.size = (600, 550)

# Replace this with your Vosk model path
MODEL_PATH = r"C:\Users\ASUS\OneDrive\Desktop\audio to text\models\vosk-model-small-en-in-0.4"



class SpeechToTextLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(SpeechToTextLayout, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 25
        self.spacing = 15
        self.listening = False
        self.q = queue.Queue()

        # Load Vosk model
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("Please download and extract the Vosk model.")

        self.model = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000)

        # UI Components
        self.heading = Label(
            text="[b]Hello, Welcome to EaseLaw[/b]",
            markup=True,
            font_size='28sp',
            color=(0.2, 0.2, 0.5, 1),
            size_hint=(1, 0.1)
        )
        self.add_widget(self.heading)

        self.text_input = TextInput(
            hint_text="Your transcribed speech will appear here...",
            font_size='18sp',
            multiline=True,
            readonly=True,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10, 10, 10],
            size_hint=(1, 0.65)
        )
        self.add_widget(self.text_input)

        self.listen_button = Button(
            text="🎙️ Start Listening (Offline)",
            size_hint=(1, 0.15),
            background_color=(0.2, 0.4, 1, 1),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True
        )
        self.listen_button.bind(on_press=self.toggle_listening)
        self.add_widget(self.listen_button)

        self.save_button = Button(
            text="💾 Save Transcript",
            size_hint=(1, 0.1),
            background_color=(0.2, 0.7, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        self.save_button.bind(on_press=self.save_transcript)
        self.add_widget(self.save_button)

    def toggle_listening(self, instance):
        if not self.listening:
            self.listening = True
            self.listen_button.text = "⏹️ Stop Listening"
            self.listen_button.background_color = (1, 0.5, 0.2, 1)
            threading.Thread(target=self.stream_audio, daemon=True).start()
        else:
            self.listening = False
            self.listen_button.text = "🎙️ Start Listening (Offline)"
            self.listen_button.background_color = (0.2, 0.4, 1, 1)

    def stream_audio(self):
        def callback(indata, frames, time, status):
            if status:
                print(status)
            self.q.put(bytes(indata))

        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            while self.listening:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = self.recognizer.Result()
                    text = eval(result).get("text", "")
                    if text:
                        Clock.schedule_once(lambda dt: self.append_text(text))
                else:
                    partial = eval(self.recognizer.PartialResult()).get("partial", "")
                    if partial:
                        Clock.schedule_once(lambda dt: self.set_placeholder(partial))

    def append_text(self, text):
        self.text_input.text = self.text_input.text.rstrip(".") + " " + text + ". "

    def set_placeholder(self, partial):
        if not self.text_input.text.endswith("... "):
            self.text_input.text += "... "

    def save_transcript(self, instance):
        content = self.text_input.text.strip()
        if content:
            filename = f"EaseLaw_Transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            self.text_input.text += f"\n\n✔ Transcript saved to '{filename}'"
        else:
            self.text_input.text += "\n\n⚠ Nothing to save!"


class EaseLawApp(App):
    def build(self):
        self.title = "EaseLaw - Offline Audio to Text"
        return SpeechToTextLayout()


if __name__ == '__main__':
    EaseLawApp().run()
