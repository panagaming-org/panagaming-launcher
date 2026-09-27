import flet as ft
from service.launcher_service import LauncherService
from service.versions_service import VersionsService

class CreateInstanceView(ft.Container):
    def __init__(self, page: ft.Page, on_back_callback=None):
        super().__init__()

        self.page = page
        self.on_back_callback = on_back_callback
        self.launcher_service = LauncherService()

        self.expand = True
        self.padding = 20
        self.bgcolor = "#0f172a"

        # --- Campos del Formulario con colores de texto corregidos ---
        self.input_name = ft.TextField(
            label="Nombre de la Instancia",
            label_style=ft.TextStyle(color=ft.Colors.WHITE70),
            hint_text="Ej. Mi Survival 1.7.10",
            hint_style=ft.TextStyle(color=ft.Colors.WHITE38),
            bgcolor="#1e293b",
            color=ft.Colors.WHITE,
            border_color="#334155",
            focused_border_color="#3c8527"
        )
        
        self.input_version = ft.TextField(
            label="Versión de Minecraft",
            label_style=ft.TextStyle(color=ft.Colors.WHITE70),
            value="1.7.10",
            hint_text="Ej. 1.20.4",
            hint_style=ft.TextStyle(color=ft.Colors.WHITE38),
            bgcolor="#1e293b",
            color=ft.Colors.WHITE,
            border_color="#334155",
            focused_border_color="#3c8527"
        )
        
        self.dropdown_loader = ft.Dropdown(
            label="Tipo de Loader",
            label_style=ft.TextStyle(color=ft.Colors.WHITE70),
            value="vanilla",
            bgcolor="#1e293b",
            color=ft.Colors.WHITE,
            border_color="#334155",
            focused_border_color="#3c8527",
            options=[
                ft.dropdown.Option("vanilla"),
                ft.dropdown.Option("forge"),
            ],
            on_change=self.toggle_loader_fields
        )
        
        self.input_forge_version = ft.TextField(
            label="Versión de Forge (Opcional)",
            label_style=ft.TextStyle(color=ft.Colors.WHITE70),
            hint_text="Déjalo vacío para usar la recomendada",
            hint_style=ft.TextStyle(color=ft.Colors.WHITE38),
            bgcolor="#1e293b",
            color=ft.Colors.WHITE,
            border_color="#334155",
            focused_border_color="#3c8527",
            visible=False
        )
        
        # Texto de estado para mostrar progreso de instalación
        self.status_text = ft.Text("", color=ft.Colors.WHITE70, size=13)

        # --- Construcción de la Interfaz Visual ---
        self.content = ft.Column(
            expand=True,
            spacing=20,
            controls=[
                # Cabecera con botón de retroceso
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Crear Nueva Instancia", size=24, weight="bold", color=ft.Colors.WHITE),
                        ft.TextButton(
                            "Volver",
                            icon=ft.Icons.ARROW_BACK,
                            style=ft.ButtonStyle(color=ft.Colors.WHITE),
                            on_click=self.go_back
                        )
                    ]
                ),
                ft.Divider(height=1, color="#334155"),
                
                # Tarjeta contenedora del formulario centrado
                ft.Container(
                    bgcolor="#1e293b",
                    padding=25,
                    border_radius=10,
                    border=ft.border.all(1, "#3CFF00"),
                    content=ft.Column(
                        tight=True,
                        spacing=15,
                        controls=[
                            self.input_name,
                            self.input_version,
                            self.dropdown_loader,
                            self.input_forge_version,
                            ft.Divider(height=10, color="#334155"),
                            self.status_text,
                            # Botón de acción principal
                            ft.Row(
                                alignment=ft.MainAxisAlignment.END,
                                controls=[
                                    ft.ElevatedButton(
                                        "Crear e Instalar",
                                        icon=ft.Icons.CHECK,
                                        bgcolor="#3c8527",
                                        color=ft.Colors.WHITE,
                                        on_click=self.execute_creation
                                    )
                                ]
                            )
                        ]
                    )
                )
            ]
        )

    def toggle_loader_fields(self, e):
        """Muestra u oculta el campo de Forge según la selección del dropdown."""
        if self.dropdown_loader.value == "forge":
            self.input_forge_version.visible = True
        else:
            self.input_forge_version.visible = False
            self.input_forge_version.value = ""
        self.update()

    def execute_creation(self, e):
        """Ejecuta la lógica de creación utilizando el LauncherService."""
        name = self.input_name.value.strip()
        version = self.input_version.value.strip()
        loader = self.dropdown_loader.value
        forge_ver = self.input_forge_version.value.strip() if self.input_forge_version.visible else None

        if not name:
            self.status_text.value = "⚠️ Debes asignarle un nombre a la instancia."
            self.update()
            return

        self.status_text.value = "⏳ Preparando e instalando archivos... Por favor espera."
        self.update()

        try:
            # Llamada al servicio para descargar e instalar
            self.launcher_service.create_instance(
                name=name,
                minecraft_version=version,
                loader_type=loader,
                forge_version=forge_ver if forge_ver else None,
                callback=self.update_status_callback
            )
            self.status_text.value = "✅ ¡Instancia creada con éxito!"
            self.update()

            if self.on_back_callback:
                import threading
                threading.Timer(1.0, lambda: self.on_back_callback(e)).start()
        
        except Exception as ex:
            self.status_text.value = f"❌ Error: {str(ex)}"
            self.update()
            

    def update_status_callback(self, message):
        """Actualiza el texto de estado en tiempo real mediante el callback del servicio."""
        self.status_text.value = message
        self.update()

    def go_back(self, e):
        """Vuelve a la vista anterior si se proporciona un callback."""
        if self.on_back_callback:
            self.on_back_callback(e)