import flet as ft
import threading
import os
from service.launcher_service import LauncherService
from model.dao.instance_dao import InstanceDAO

class HomeView(ft.Container):
    def __init__(self, page: ft.Page, on_game_state_changed=None):
        super().__init__()
        self.page = page
        self.launcher_service = LauncherService()
        self.on_game_state_changed = on_game_state_changed
        self.expand = True
        self.padding = 20
        self.instance_dao = InstanceDAO()
        self.username = "IKERO90"
        
        # 1. Obtener la instancia seleccionada o la primera disponible
        self.selected_instance = getattr(self.instance_dao, "get_selected_instance", lambda: None)()
        
        if not self.selected_instance:
            all_instances = InstanceDAO.get_all()
            self.selected_instance = all_instances[0] if all_instances else None

        inst_name = self.selected_instance.name if self.selected_instance else "Ninguna instancia seleccionada"
        self.status_text = ft.Text(f"Instancia activa: {inst_name}", size=12, color=ft.Colors.WHITE54)

        # 2. Cargar opciones del desplegable desde la base de datos
        instances_list = InstanceDAO.get_all()
        dropdown_options = []
        default_value = None

        if instances_list:
            for inst in instances_list:
                display_label = f"{inst.name} ({inst.minecraft_version})"
                dropdown_options.append(ft.dropdown.Option(text=display_label, key=str(inst.id)))
            
            if self.selected_instance:
                default_value = str(self.selected_instance.id)
        else:
            dropdown_options.append(ft.dropdown.Option(text="No hay instancias creadas", key="none"))
            default_value = "none"

        self.version_dropdown = ft.Dropdown(
            label="Instancia / Versión",
            border_color="#334155",
            focused_border_color="#22c55e",
            text_style=ft.TextStyle(color=ft.Colors.WHITE, size=13),
            label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=12),
            options=dropdown_options,
            value=default_value,
            dense=True,
            on_change=self.on_instance_changed
        )

        self.play_button = ft.ElevatedButton(
            content=ft.Text("JUGAR", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            bgcolor="#22c55e",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            width=160,
            height=45,
            on_click=self.manage_play_click
        )

        # 3. Componentes de la consola central de ejecución
        self.logs_view = ft.ListView(
            expand=True,
            spacing=5,
            auto_scroll=True,
            padding=10
        )
        
        self.console_container = ft.Container(
            content=self.logs_view,
            bgcolor="#0f172a",
            border_radius=8,
            border=ft.border.all(1, "#334155"),
            padding=10,
            expand=True,
            visible=False  # Se oculta al iniciar, aparece al presionar Jugar
        )

        self.title_text = ft.Text("PANAGAMING LAUNCHER", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

        # Contenedor central dinámico que alterna entre el título y la consola
        self.center_content_area = ft.Container(
            expand=True, 
            bgcolor="#1e293b", 
            border_radius=12, 
            border=ft.border.all(1, "#334155"), 
            padding=30, 
            alignment=ft.alignment.center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                spacing=15,
                controls=[
                    self.title_text,
                    self.console_container
                ]
            )
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
                self.center_content_area,
                bottom_bar
            ]
        )

    def update_status(self, mensaje: str):
        """Callback que añade cada mensaje del servicio a la consola visual en pantalla."""
        self.status_text.value = mensaje
        self.logs_view.controls.append(
            ft.Text(mensaje, size=12, color=ft.Colors.WHITE70, font_family="Consolas")
        )
        try:
            self.page.update()
        except Exception:
            if self.page:
                self.page.update()

    def on_instance_changed(self, e):
        selected_id = self.version_dropdown.value
        if selected_id == "none":
            return
        instances = InstanceDAO.get_all()
        for inst in instances:
            if str(inst.id) == str(selected_id):
                self.selected_instance = inst
                self.status_text.value = f"Instancia activa: {inst.name}"
                self.page.update()
                break

    def manage_play_click(self, e):
        if not self.selected_instance:
            self.update_status("Error: No hay ninguna instancia seleccionada.")
            return

        version = self.selected_instance.minecraft_version

        # 1. Deshabilitar botón de jugar y bloquear menú superior
        self.play_button.disabled = True
        self.play_button.content = ft.Text("JUGANDO...", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
        self.play_button.bgcolor = ft.Colors.ORANGE_700
        
        if self.on_game_state_changed:
            self.on_game_state_changed(True)  # Bloquea las pestañas de arriba
            
        self.page.update()

        def second_plane_task():
            try:
                self.launcher_service.launch_instance(
                    instance_name=self.selected_instance.name,
                    username="PanaPlayer", # O tu variable de usuario actual
                    minecraft_version=version,
                    callback=self.update_status
                )
            except Exception as ex:
                self.update_status(f"Error: {str(ex)}")
            finally:
                # 2. Restaurar botón y desbloquear menú superior al cerrar Minecraft
                self.play_button.disabled = False
                self.play_button.content = ft.Text("JUGAR", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
                self.play_button.bgcolor = "#22c55e"
                
                if self.on_game_state_changed:
                    self.on_game_state_changed(False) # Habilita de nuevo las pestañas
                    
                self.page.update()

        threading.Thread(target=second_plane_task, daemon=True).start()

    def update_status(self, msg):
        self.status_text.value = msg
        self.page.update()