import flet as ft
import threading
from view.instances.create_instance_view import CreateInstanceView
from model.dao.instance_dao import InstanceDAO
from storage.data.database import SessionLocal
from service.launcher_service import LauncherService

class InstancesView(ft.Container):
    def __init__(self, page: ft.Page, on_navigate_to_create=None):
        super().__init__()
        self.page = page
        self.on_navigate_to_create = on_navigate_to_create
        self.expand = True
        self.launcher_service = LauncherService()
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
                            ft.TextButton("Configurar", icon=ft.Icons.SETTINGS, icon_color=ft.Colors.WHITE, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, tooltip="Eliminar", on_click=lambda e: self.open_delete_dialog(name_instance=name))
                        ]
                    )
                ]
            )
        )
        
    def create_instance(self, e):
        """Método que ejecuta el callback para cambiar a la vista de creación"""
        if self.on_navigate_to_create:
            self.on_navigate_to_create(e)

    def cancel_delete_instance(self, e):
        """Cierra el diálogo de confirmación de eliminación."""
        self.delete_instance_dialog.open = False
        self.page.update()

    def confirm_delete_instance(self, name_instance:str):
        """Confirma la eliminación de la instancia y actualiza la vista."""
        
        self.delete_instance_dialog.open = False
        self.launcher_service.delete_instance(name_instance)
        self.page.update()


    def open_delete_dialog(self, name_instance: str):
        """Abre un diálogo modal para confirmar la eliminación de la instancia."""
        
        def confirm_delete(e):
            try:
                # 1. Llamar al servicio para eliminar los archivos físicos
                self.launcher_service.delete_instance(name_instance)
                
                # 2. Cerrar el modal
                self.page.close(delete_dialog)
                
                # 3. Recargar la lista de instancias en pantalla
                self.page.update() # Asegúrate de tener este método para refrescar
                self.launcher_service.get_instances()  # Método hipotético para recargar la vista de instancias
                # 4. Mostrar snackbar de éxito
                self.page.open(ft.SnackBar(ft.Text(f"Instancia '{name_instance}' eliminada correctamente"), bgcolor="#22c55e"))

            except Exception as ex:
                self.page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}"), bgcolor=ft.Colors.RED_400))

        def close_dialog(e):
            self.page.close(delete_dialog)

            # Crear el diálogo modal de confirmación
        delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar Instancia", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            content=ft.Text(f"¿Estás seguro de que deseas eliminar la instancia '{name_instance}'? Se borrarán todos sus archivos y no se podrá recuperar.", color=ft.Colors.WHITE70),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog, style=ft.ButtonStyle(color=ft.Colors.WHITE70)),
                ft.ElevatedButton("Eliminar", on_click=confirm_delete, bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1e293b",
            shape=ft.RoundedRectangleBorder(radius=10)
        )

            # Mostrar el diálogo en la página
        self.page.open(delete_dialog)