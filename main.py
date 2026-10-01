import flet as ft
from view.home_view import HomeView
from view.instances.instances_view import InstancesView
from view.instances.create_instance_view import CreateInstanceView
from storage.data.database import init_db, get_db

def main(page: ft.Page):
    page.title = "PanaGaming Launcher"
    page.window.width = 1450
    page.window.height = 1000
    page.window.resizable = False
    page.bgcolor = "#0f172a"  # Fondo oscuro cyberpunk

    content_area = ft.Container(expand=True, content=HomeView(page))

    # Declaramos los botones de navegación superior para poder controlarlos
    btn_inicio = ft.TextButton("Inicio", style=ft.ButtonStyle(color=ft.Colors.WHITE))
    btn_instancias = ft.TextButton("Instancias", style=ft.ButtonStyle(color=ft.Colors.WHITE70))
    btn_mods = ft.TextButton("Mods / Packs", style=ft.ButtonStyle(color=ft.Colors.WHITE70))
    btn_ajustes = ft.TextButton("Ajustes", style=ft.ButtonStyle(color=ft.Colors.WHITE70))

    def go_to_create_instance(e):
        content_area.content = CreateInstanceView(page, on_back_callback=go_to_instances_view)
        page.update()

    # Función para regresar a la vista de instancias
    def go_to_instances_view(e):
        content_area.content = InstancesView(page, on_navigate_to_create=go_to_create_instance)
        page.update()

    def change_view(e, view_name):
        # 1. Restablecer el color de todos los botones a inactivo
        btn_inicio.style.color = ft.Colors.WHITE70
        btn_instancias.style.color = ft.Colors.WHITE70
        btn_mods.style.color = ft.Colors.WHITE70
        btn_ajustes.style.color = ft.Colors.WHITE70

        # 2. Resaltar en blanco el botón que fue presionado
        e.control.style.color = ft.Colors.WHITE

        # 3. Intercambiar el contenido del área central según la opción
        if view_name == "Inicio":
            content_area.content = HomeView(page)
        elif view_name == "Instancias":
            # CORREGIDO: Pasamos el callback aquí también para no perderlo al cambiar de pestaña
            content_area.content = InstancesView(page, on_navigate_to_create=go_to_create_instance)
        elif view_name == "Mods":
            content_area.content = ft.Container(
                alignment=ft.alignment.center,
                content=ft.Text("Sección de Mods y Paquetes en desarrollo...", color=ft.Colors.WHITE54, size=15)
            )
        elif view_name == "Ajustes":
            content_area.content = ft.Container(
                alignment=ft.alignment.center,
                content=ft.Text("Ajustes del Launcher en desarrollo...", color=ft.Colors.WHITE54, size=15)
            )
        
        # 4. Refrescar la página para aplicar los cambios visuales
        page.update()

    # Asignamos los Eventos a los Botones
    btn_inicio.on_click = lambda e: change_view(e, "Inicio")
    btn_instancias.on_click = lambda e: change_view(e, "Instancias")
    btn_mods.on_click = lambda e: change_view(e, "Mods")
    btn_ajustes.on_click = lambda e: change_view(e, "Ajustes")

    # Menú superior estilo pestañas (Sin iconos)
    top_nav = ft.Row(
        spacing=10,
        controls=[btn_inicio, btn_instancias, btn_mods, btn_ajustes]
    )
    
    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    bgcolor="#1e293b",
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    content=top_nav
                ),
                ft.Divider(height=1, color="#334155"),
                content_area
            ]
        )
    )

if __name__ == '__main__':
    init_db()
    ft.app(target=main)