import flet as ft
import requests

def main(page: ft.Page):
    page.title = "IoT IntelliRoom System"
    page.bgcolor = ft.colors.BROWN_100
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # UI components
    temperature_text = ft.Text("Temperature: -- °C", size=16)
    light_level_text = ft.Text("Light Level: --%", size=16)
    presence_text = ft.Text("Presence: Simulated", size=16)
    status_text = ft.Text("System Status: Awaiting action...", size=16)

    temp_toggle = ft.Switch(label="Manual Fan Control (Temperature Override)", value=False)
    light_toggle = ft.Switch(label="Manual Light Control", value=False)

    # Event Handlers
    def toggle_changed(e):
        fan_status = "ON" if temp_toggle.value else "AUTO"
        light_status = "ON" if light_toggle.value else "AUTO"
        status_text.value = f"Fan: {fan_status} | Light: {light_status}"
        page.update()

    def update_dashboard(e=None):
        try:
            temp_response = requests.get("http://127.0.0.1:5000/temperature_sensing", timeout=2)
            light_response = requests.get("http://127.0.0.1:5000/light_sensing", timeout=2)

            if temp_response.ok and light_response.ok:
                temp = temp_response.json().get("temperature", "--")
                light = light_response.json().get("light_level", "--")

                temperature_text.value = f"Temperature: {temp} °C"
                light_level_text.value = f"Light Level: {light}%"
                toggle_changed(None)
            else:
                raise ValueError("Bad response from API")

        except Exception as err:
            temperature_text.value = "Error: Temp fetch failed"
            light_level_text.value = "Error: Light fetch failed"
        page.update()

    # Assign events
    temp_toggle.on_change = toggle_changed
    light_toggle.on_change = toggle_changed

    # Refresh Button
    refresh_btn = ft.ElevatedButton(text="Refresh Readings", on_click=update_dashboard)

    # Layout
    page.add(
        ft.Column(
            spacing=20,
            controls=[
                ft.Text("IntelliRoom Dashboard", size=24, weight="bold"),
                temperature_text,
                light_level_text,
                presence_text,
                refresh_btn,
                ft.Divider(),
                temp_toggle,
                light_toggle,
                status_text,
            ],
        )
    )

    update_dashboard()

ft.app(target=main)
