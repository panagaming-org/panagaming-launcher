import flet as ft
import threading
from service.launcher_service import LauncherService

class HomeView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.launcher_service = LauncherService()
        self.expand = True
        self.padding = 20
        
        self.status_text = ft.Text("Selecciona la Instancia.", size=12, color=ft.Colors.WHITE54)

        self.version_dropdown = ft.Dropdown(
            label="Versión",
            border_color="#334155",
            focused_border_color="#22c55e",
            text_style=ft.TextStyle(color=ft.Colors.WHITE, size=13),
            label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=12),
            options=[
                ft.dropdown.Option("1.20"),
                ft.dropdown.Option("1.20.1 - World of Mithral"),
                ft.dropdown.Option("1.19.2 - Nightmares Arrival"),
            ],
            value="1.20",  # Predeterminado en 1.20 como solicitaste
            dense=True,
        )

        self.play_button = ft.ElevatedButton(
            content=ft.Text("JUGAR", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            bgcolor="#22c55e",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            width=160,
            height=45,
            on_click=self.manage_play_click
        )

        bottom_bar = ft.Container(
            bgcolor="#1e293b",
            padding=15,
            border_radius=12,
            border=ft.border.all(1, "#334155"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                bgcolor="#22c55e", width=36, height=36, border_radius=18,
                                alignment=ft.alignment.center,
                                content=ft.Text("P", color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD)
                            ),
                            ft.Column(
                                spacing=0, alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("PanaPlayer", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text("Modo Auténtico / Local", size=10, color=ft.Colors.WHITE54),
                                ]
                            )
                        ]
                    ),
                    ft.Container(width=220, content=self.version_dropdown),
                    ft.Column([self.play_button, self.status_text], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ]
            )
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=True,
            controls=[
                ft.Container(
                    expand=True, bgcolor="#1e293b", border_radius=12,
                    border=ft.border.all(1, "#334155"), padding=30,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15,
                        controls=[
                            ft.Text("PANAGAMING LAUNCHER", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ]
                    )
                ),
                bottom_bar
            ]
        )

    def update_status(self, mensaje: str):
        """Callback seguro para actualizar los textos desde el servicio."""
        self.status_text.value = mensaje
        self.page.update()

    def manage_play_click(self, e):
        version = self.version_dropdown.value
        self.play_button.disabled = True
        self.page.update()

        # Ejecutamos el servicio en un hilo separado para no congelar la UI de Flet
        def second_plane_task():
            try:
                self.launcher_service.prepare_and_launch(version, self.update_status)
            finally:
                self.play_button.disabled = False
                self.page.update()
                
        threading.Thread(target=second_plane_task).start()