from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from Subway_LED_Console_project.subway_API import MTA_requests

'''
PACKAGE NOTES:

- To run UI, navigate to folder above Subway_LED_Console_project and type: python3 -m Subway_LED_Console_project.ui.run_ui 
- This will avoid relative pathing issues 
'''

class TouchPadUI(App):
    def build(self):
        # Outer layout to center content towards the top
        outer_layout = AnchorLayout(anchor_x="center", anchor_y="top", padding=20)

        # Inner vertical layout (dropdown row + confirm button)
        container = BoxLayout(orientation="vertical", spacing=20, size_hint=(None, None))
        container.size = (700, 200)

        # Horizontal layout for the two dropdowns/text boxes
        main_layout = BoxLayout(orientation="horizontal", spacing=40, size_hint=(None, None))
        main_layout.size = (700, 100)

        # Layouts for each selection tool
        select_one_lay = BoxLayout(orientation="vertical", size_hint=(None, None))
        select_one_lay.size = (300, 100)
        select_two_lay = BoxLayout(orientation="vertical", size_hint=(None, None))
        select_two_lay.size = (300, 100)

        # First dropdown
        dropdown_one = DropDown()
        for index in range(10):
            btn = Button(text=f'Stop {index}', size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: dropdown_one.select(btn.text))
            dropdown_one.add_widget(btn)

        select_one = Button(text='Select first stop', size_hint=(None, None), size=(200, 50))
        select_one_text = TextInput(text='Select first stop', size_hint=(None, None), size=(200, 50))
        select_one.bind(on_release=dropdown_one.open)
        dropdown_one.bind(on_select=lambda instance, x: (
            setattr(select_one, 'text', x),
            setattr(select_one_text, 'text', x)
        ))

        # Second dropdown
        dropdown_two = DropDown()
        for index in range(10):
            btn2 = Button(text=f'Stop {index}', size_hint_y=None, height=40)
            btn2.bind(on_release=lambda btn2: dropdown_two.select(btn2.text))
            dropdown_two.add_widget(btn2)

        select_two = Button(text='Select second stop', size_hint=(None, None), size=(200, 50))
        select_two_text = TextInput(text='Select second stop', size_hint=(None, None), size=(200, 50))

        select_two.bind(on_release=dropdown_two.open)
        dropdown_two.bind(on_select=lambda instance, x: (
            setattr(select_two, 'text', x),
            setattr(select_two_text, 'text', x)
        ))

        # Add widgets to their layouts
        select_one_lay.add_widget(select_one_text)
        select_one_lay.add_widget(select_one)
        select_two_lay.add_widget(select_two_text)
        select_two_lay.add_widget(select_two)

        main_layout.add_widget(select_one_lay)
        main_layout.add_widget(select_two_lay)

        # Confirm button
        confirm_btn = Button(text="Confirm Stops", size_hint=(None, None), size=(200, 50))

        def confirm_selection(instance):
            stop1 = select_one_text.text.strip()
            stop2 = select_two_text.text.strip()
            print(f"First stop: {stop1}, Second stop: {stop2}")

        confirm_btn.bind(on_release=confirm_selection)

        # Add layouts
        container.add_widget(main_layout)
        container.add_widget(confirm_btn)

        outer_layout.add_widget(container)
        return outer_layout

if __name__ == '__main__':
    TouchPadUI().run()
