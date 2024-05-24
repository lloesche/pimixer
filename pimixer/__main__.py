import os
import serial
import time
from multiprocessing import Process, Queue, Event
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.config import Config


SERIAL_PORT = "/dev/ttyGS0"
BAUD_RATE = 9600

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "480")
Config.set("graphics", "fullscreen", "1")
Config.set("graphics", "resizable", False)
Config.set("graphics", "show_cursor", 0)

# Set up the device and maximum brightness variable
device, max_brightness = None, None


def get_backlight_devices():
    backlight_path = "/sys/class/backlight/"
    devices = None
    if not os.path.exists(backlight_path):
        raise FileNotFoundError(f"{backlight_path} does not exist")
    for device in os.listdir(backlight_path):
        max_brightness_path = os.path.join(backlight_path, device, "max_brightness")
        if os.path.exists(max_brightness_path):
            with open(max_brightness_path, "r") as f:
                max_brightness = int(f.read().strip())
                return device, max_brightness
    return devices


def set_brightness(percent):
    global device, max_brightness
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100
    new_brightness = int((percent / 100.0) * max_brightness)
    brightness_path = f"/sys/class/backlight/{device}/brightness"
    with open(brightness_path, "w") as f:
        f.write(str(new_brightness))


device, max_brightness = get_backlight_devices()
set_brightness(0)


def serial_process(q, stop_event):
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1) as ser:
            while not stop_event.is_set():
                if not q.empty():
                    message = q.get_nowait()
                    ser.write(message.encode())
                else:
                    time.sleep(0.01)
                if ser.in_waiting > 0:
                    incoming_data = ser.readline().decode("utf-8").strip()
                    print(f"Received: {incoming_data}")

    except Exception as e:
        print(f"Error in serial communication: {e}")


class AudioMixerApp(App):
    def build(self):
        self.q = Queue()
        self.stop_event = Event()
        self.serial_thread = Process(target=serial_process, args=(self.q, self.stop_event))
        self.serial_thread.start()

        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        grid_layout = GridLayout(cols=5, size_hint_y=0.8)
        self.sliders = []
        self.mute_buttons = []
        self.previous_values = [50] * 5
        self.last_saved_values = None

        for i in range(5):
            vbox = BoxLayout(orientation="vertical", spacing=10)
            # icon = Image(source=self.icons[i], size_hint=(1, None), height=128)  # Adjust icon size
            # vbox.add_widget(icon)
            slider = Slider(min=0, max=1023, value=1023, orientation="vertical", size_hint=(1, 1))
            # slider.bind(value=self.slider_value_changed)
            vbox.add_widget(slider)
            self.sliders.append(slider)

            mute_button = Button(text="Mute", size_hint=(1, None), height=100)
            mute_button.bind(on_press=self.create_toggle_mute_callback(i))
            vbox.add_widget(mute_button)
            self.mute_buttons.append(mute_button)

            grid_layout.add_widget(vbox)

        main_layout.add_widget(grid_layout)
        main_layout.bind(on_touch_down=self.on_touch_down)  # Bind touch event
        self.load_slider_values()

        # fixme: ugly ass hack to make the screen display the initial UI
        Clock.schedule_once(self.force_redraw, 2)
        Clock.schedule_once(self.force_redraw, 4)
        Clock.schedule_once(self.force_redraw, 6)
        Clock.schedule_interval(self.send_slider_values, 0.01)
        Clock.schedule_interval(self.save_slider_values, 1)
        return main_layout

    def force_redraw(self, dt):
        self.root.canvas.ask_update()

    def on_touch_down(self, instance, touch):
        set_brightness(100)  # Set brightness to 100% when the screen is touched
        Clock.schedule_once(lambda dt: set_brightness(0), 1)  # After 1 second, set it back to 0%

    def create_toggle_mute_callback(self, index):
        def toggle_mute(instance):
            if instance.text == "Mute":
                instance.text = "Unmute"
                self.previous_values[index] = self.sliders[index].value
                animation = Animation(value=0, duration=0.2, t="out_expo")
                animation.start(self.sliders[index])
            else:
                instance.text = "Mute"
                animation = Animation(value=self.previous_values[index], duration=0.5, t="out_expo")
                animation.start(self.sliders[index])

        return toggle_mute

    def send_slider_values(self, dt):
        values = "|".join(str(int(slider.value)) for slider in self.sliders)
        self.q.put(f"{values}\r\n")

    def save_slider_values(self, dt):
        current_values = [int(slider.value) for slider in self.sliders]
        if current_values != self.last_saved_values:
            print("Saving config file")
            config_path = os.path.expanduser("~/.pimixer.conf")
            with open(config_path, "w") as config_file:
                config_file.write("|".join(map(str, current_values)) + "\n")
            self.last_saved_values = current_values  # Update cache
            print("Saved slider values.")

    def load_slider_values(self):
        config_path = os.path.expanduser("~/.pimixer.conf")
        try:
            with open(config_path, "r") as config_file:
                print("Loading config file")
                values = config_file.readline().strip().split("|")
                for slider, value in zip(self.sliders, values):
                    slider.value = float(value)
                    print(f"Setting slider {slider} value {value}")
            print("Loaded slider values.")
        except FileNotFoundError:
            print("No configuration file found; using default values.")

    def on_stop(self):
        self.save_slider_values(None)
        self.stop_event.set()
        self.serial_thread.join()


if __name__ == "__main__":
    AudioMixerApp().run()
