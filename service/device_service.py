import psutil
import flet as ft

class DeviceService:
    
    @staticmethod
    def get_ram_number() -> int:
        """Devuelve la cantidad de RAM en MB."""
        ram_bytes = psutil.virtual_memory().total
        ram_mb = ram_bytes // (1024 * 1024)  # Convertir bytes a MB
        return ram_mb

    @staticmethod
    def format_ram_argument(ram_value) -> str:
        clean_val = str(ram_value).upper().replace("G", "").strip()
        return f"-Xmx{int(clean_val)}G"
    