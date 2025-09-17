from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout


class TouchPadUI(App):
    def build(self):
        # Outer layout to center content towards the top
        outer_layout = AnchorLayout(anchor_x="center", anchor_y="top", padding=20)

        # Inner horizontal layout for the two dropdowns
        main_layout = BoxLayout(orientation="horizontal", spacing=40, size_hint=(None, None))
        main_layout.size = (500, 100)

        # First dropdown
        dropdown_one = DropDown()
        for index in range(10):
            btn = Button(text=f'Stop {index}', size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: dropdown_one.select(btn.text))
            dropdown_one.add_widget(btn)

        select_one = Button(text='Select first stop', size_hint=(None, None), size=(200, 50))
        select_one.bind(on_release=dropdown_one.open)
        dropdown_one.bind(on_select=lambda instance, x: setattr(select_one, 'text', x))

        # Second dropdown
        dropdown_two = DropDown()
        for index in range(10):
            btn2 = Button(text=f'Stop {index}', size_hint_y=None, height=40)
            btn2.bind(on_release=lambda btn2: dropdown_two.select(btn2.text))
            dropdown_two.add_widget(btn2)

        select_two = Button(text='Select second stop', size_hint=(None, None), size=(200, 50))
        select_two.bind(on_release=dropdown_two.open)
        dropdown_two.bind(on_select=lambda instance, x: setattr(select_two, 'text', x))

        # Add both dropdown triggers to horizontal layout
        main_layout.add_widget(select_one)
        main_layout.add_widget(select_two)

        # Center horizontal layout at the top of screen
        outer_layout.add_widget(main_layout)

        return outer_layout


if __name__ == '__main__':
    TouchPadUI().run()
