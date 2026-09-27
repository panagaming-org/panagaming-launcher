import flet as ft
import threading
from view.instances.create_instance_view import CreateInstanceView
from model.dao.instance_dao import InstanceDAO
from storage.data.database import SessionLocal

class InstancesView(ft.Container):
    def __init__(self, page: ft.Page, on_navigate_to_create=None):
        super().__init__()
        self.page = page
        self.on_navigate_to_create = on_navigate_to_create
        self.expand = True
        self.padding = 20
        self.bgcolor = "#0f172a"  # Fondo oscuro general del launcher
        
        # 1. Obtener los datos usando una sesión activa de la base de datos

        instances_data = InstanceDAO.get_all()

        instance_cards = []
        if not instances_data:
            instance_cards.append(ft.Text("No hay instancias creadas aún.", italic=True, color=ft.Colors.GREY))
        else:
            for inst in instances_data:
                version_text = f"{inst.minecraft_version} ({inst.loader_type})"
                card = self._create_instance_card(
                    name=inst.name,
                    version=version_text,
                )
                instance_cards.append(card)

        # Columna contenedora para las tarjetas de las instancias (con scroll)
        self.cards_column = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            controls=instance_cards
        )
        
        self.content = ft.Column(
            expand=True,
            spacing=20,
            controls=[
                # Cabecera con título y botón de crear
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Gestión de Instancias", size=24, weight="bold", color=ft.Colors.WHITE),
                        ft.ElevatedButton(
                            "Crear Nueva Instancia", 
                            icon=ft.Icons.ADD, 
                            bgcolor="#3c8527", 
                            color=ft.Colors.WHITE,
                            on_click=self.create_instance
                        ),
                    ]
                ),
                ft.Divider(height=1, color="#334155"),
                # 2. ¡Aquí faltaba agregar la columna con las tarjetas al contenido visual!
                self.cards_column
            ]
        )

    def _create_instance_card(self, name, version):
        """Método auxiliar para generar tarjetas de instancia estilizadas de forma limpia."""
        return ft.Container(
            bgcolor="#1e293b",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#334155"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Información de la instancia
                    ft.Column(
                        spacing=5,
                        controls=[
                            ft.Text(name, size=16, weight="bold", color=ft.Colors.WHITE),
                            ft.Row(
                                spacing=15,
                                controls=[
                                    ft.Text(f"Versión: {version}", size=12, color=ft.Colors.WHITE70),
                                ]
                            )
                        ]
                    ),
                    # Botones de acción
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.ElevatedButton("Seleccionar", icon=ft.Icons.PLAY_ARROW, bgcolor="#3c8527", color=ft.Colors.WHITE),
                            ft.TextButton("Configurar", icon=ft.Icons.SETTINGS, icon_color=ft.Colors.WHITE, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                            ft.IconButton(icon=ft.Icons.STOP, icon_color=ft.Colors.RED_400, tooltip="Detener")
                        ]
                    )
                ]
            )
        )
        
    def create_instance(self, e):
        """Método que ejecuta el callback para cambiar a la vista de creación"""
        if self.on_navigate_to_create:
            self.on_navigate_to_create(e)