from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.config import Config

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "480")
Config.set("graphics", "fullscreen", "1")
Config.set("graphics", "resizable", False)
Config.set("graphics", "show_cursor", 0)


class AudioMixerApp(App):
    def build(self):
        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Grid layout for sliders, icons, and mute buttons
        grid_layout = GridLayout(cols=5, size_hint_y=0.8)

        self.sliders = []
        self.mute_buttons = []
        self.previous_values = [50] * 5  # Store previous values for each slider
        self.labels = ["App1", "App2", "App3", "App4", "Master"]
        self.icons = ["app1.png", "app2.png", "app3.png", "app4.png", "master.png"]

        for i in range(5):
            vbox = BoxLayout(orientation="vertical", spacing=10)

            if i < 4:  # Only add icons above the first four sliders
                icon = Image(source=self.icons[i], size_hint=(1, None), height=128)  # Adjust icon size
                vbox.add_widget(icon)

            slider = Slider(min=0, max=100, value=50, orientation="vertical", size_hint=(1, 1))
            vbox.add_widget(slider)
            self.sliders.append(slider)

            mute_button = Button(text="Mute", size_hint=(1, None), height=100)  # Adjust button size
            mute_button.bind(on_press=self.create_toggle_mute_callback(i))
            vbox.add_widget(mute_button)
            self.mute_buttons.append(mute_button)

            grid_layout.add_widget(vbox)

        main_layout.add_widget(grid_layout)

        return main_layout

    def create_toggle_mute_callback(self, index):
        def toggle_mute(instance):
            if instance.text == "Mute":
                instance.text = "Unmute"
                self.previous_values[index] = self.sliders[index].value
                animation = Animation(value=0, duration=0.2, t="out_expo")
                animation.start(self.sliders[index])
            else:
                instance.text = "Mute"
                animation = Animation(
                    value=self.previous_values[index], duration=0.5, t="out_expo"
                )  # Return to previous value
                animation.start(self.sliders[index])

        return toggle_mute


if __name__ == "__main__":
    AudioMixerApp().run()
