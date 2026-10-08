import platform
import os
import shutil
import minecraft_launcher_lib
import subprocess
import requests
import urllib.request
import zipfile
from pathlib import Path
from model.dao.instance_dao import InstanceDAO
from model.entity.instance import InstanceModel

from storage.data.database import SessionLocal
# ... (demás imports que ya tienes como pathlib, os, minecraft_launcher_lib, etc.)

class LauncherService:
    def __init__(self):
        self.minecraft_dir = Path.home() / ".minecraft"
        self.base_dir = os.path.join(os.getcwd(), "instances")
        os.makedirs(self.base_dir, exist_ok=True)

    # (El método prepare_and_launch se mantiene igual...)
    def create_instance(self, name: str, minecraft_version: str, loader_type: str = "vanilla", forge_version: str = None, ram: str = "2G", callback=None):
        """
        Crea la carpeta aislada, instala Vanilla o Forge y registra los datos en la base de datos usando el DAO.
        """
        # Limpiar el nombre para usarlo de forma segura como una carpeta (evitando caracteres raros)
        instance_dir = os.path.join(self.base_dir, name)
        os.makedirs(instance_dir, exist_ok=True)

        try:
            existing_instance = InstanceDAO.get_by_name(name)
            if existing_instance:
                raise Exception(f"Ya existe una instancia con el nombre '{name}'.")

            final_loader_version = forge_version
            if loader_type.lower() == "forge" and not final_loader_version:
                if callback:
                    callback(f"Buscando la versión de Forge compatible con Minecraft {minecraft_version}...")
                final_loader_version = minecraft_launcher_lib.forge.find_forge_version(minecraft_version)

            InstanceDAO.create_instance(
                name=name,
                minecraft_version=minecraft_version,
                loader_type=loader_type,
                loader_version=final_loader_version
            )

            if callback:
                callback(f"Instancia '{name}' creada y registrada en la base de datos.")
            return True
        except Exception as e:
            if callback:
                callback(f"Error al crear la instancia: {str(e)}")
            raise e
        
    def get_instances(self):
        """
        Obtiene el listado de instancias directamente desde la base de datos usando el DAO.
        """
        try:
            db_instances = InstanceDAO.get_all()
            instances = []
            
            for inst in db_instances:
                # Opcional: Revalidar que la carpeta física todavía exista en el disco
                safe_name = "".join(c for c in inst.name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
                inst_path = os.path.join(self.base_dir, safe_name)
                
                instances.append({
                    "name": inst.name,
                    "minecraft_version": inst.minecraft_version,
                    "loader_type": inst.loader_type,
                    "loader_version": inst.loader_version,
                    "directory_path": inst_path,
                    "ram_allocation": "4G"  # Puedes añadir este campo a tu base de datos más adelante si lo deseas
                })
                
            return instances
        except Exception as e:
            print(f"Error al obtener instancias: {str(e)}")
            return []

    def launch_instance(self, instance_name: str, username: str, minecraft_version: str, callback=None):
        instance_dir = os.path.join(self.base_dir, instance_name)
        versions_dir = os.path.join(instance_dir, "versions")
        
        if not os.path.exists(versions_dir):
            msg = "Error: No se encontró la carpeta 'versions' en la instancia."
            print(f"[ERROR] {msg}")
            if callback:
                callback(msg)
            return

        installed_subdirs = [d for d in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, d))]
        
        if not installed_subdirs:
            msg = "Error: No hay versiones instaladas en el directorio."
            print(f"[ERROR] {msg}")
            if callback:
                callback(msg)
            return

        version_id = installed_subdirs[0]
        for sub in installed_subdirs:
            if "forge" in sub.lower() or "fabric" in sub.lower():
                version_id = sub
                break

        # 🔍 CORRECCIÓN ROBUSTA: Validamos que json_files no esté vacío para evitar el 'list index out of range'
        sub_path = os.path.join(versions_dir, version_id)
        os.makedirs(sub_path, exist_ok=True)
        
        version_json_path = os.path.join(sub_path, f"{version_id}.json")
        
        if not os.path.exists(version_json_path):
            json_files = [f for f in os.listdir(sub_path) if f.endswith(".json")]
            if json_files:
                import shutil
                source_json = os.path.join(sub_path, json_files[0])
                if json_files[0] != f"{version_id}.json":
                    shutil.copy(source_json, version_json_path)
            else:
                import json
                basic_json_data = {
                    "id": version_id,
                    "inheritsFrom": minecraft_version,
                    "releaseTime": "2015-01-01T00:00:00+00:00",
                    "time": "2015-01-01T00:00:00+00:00",
                    "type": "release",
                    "mainClass": "net.minecraft.launchwrapper.Launch",
                    "libraries": []
                }
                with open(version_json_path, "w", encoding="utf-8") as f:
                    json.dump(basic_json_data, f, indent=4)

        if callback:
            callback(f"Verificando entorno Java para la instancia...")

        # Descargar y configurar automáticamente el Java ideal dentro de la carpeta de la instancia
        java_executable = self._download_and_setup_java(instance_dir, minecraft_version)
        if not java_executable or not os.path.exists(java_executable):
            java_executable = "java"
            print("[ADVERTENCIA] No se encontró el Java portable, usando el comando global 'java'.")

        options = {
            "username": username,
            "uuid": "",
            "token": "",
            "executablePath": java_executable,
            "jvmArguments": ["-Xmx2G", "-XX:+UseG1GC"]
        }

        try:
            # 1. Obtener el comando base de la librería
            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=version_id,
                minecraft_directory=instance_dir,
                options=options
            )
            
            fixed_command = []
            skip_next = False
            
            for arg in command:
                if skip_next:
                    # Si venimos de -cp, -Djava.library.path, --add-exports o --add-opens:
                    # Verificamos si es una ruta de archivos real o un módulo de Java.
                    # Los módulos de Java tienen '/' y '=' (ej: java.base/sun.security.util=...) y NO son rutas de disco.
                    if "/" in arg and ("=" in arg or not os.path.exists(arg.split(";")[0])):
                        fixed_command.append(arg)  # Lo dejamos intacto con sus barras '/'
                    else:
                        fixed_command.append(arg.replace("/", os.sep))  # Es una ruta de archivo de Windows
                    skip_next = False
                elif arg in ["-cp", "-Djava.library.path", "--add-exports", "--add-opens"]:
                    fixed_command.append(arg)
                    skip_next = True
                elif arg.startswith("-"):
                    fixed_command.append(arg)
                else:
                    fixed_command.append(arg.replace("/", os.sep))
            
            command = fixed_command

            print(f"--> Comando final listo para ejecutar.")

            if callback:
                callback(f"¡Lanzando Minecraft ({instance_name})!")

            print(f"--> Comando corregido ejecutado: {' '.join(command)}")

            # 2. Lanzar el proceso con el comando corregido
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            # Hilo para imprimir en tiempo real los errores y logs de Java por pantalla
            def monitor_minecraft():
                for line in process.stdout:
                    print(f"[Minecraft Output] {line.strip()}")

            import threading
            threading.Thread(target=monitor_minecraft, daemon=True).start()

            if callback:
                callback(f"¡Minecraft ({instance_name}) está en ejecución!")

            # 🛑 CLAVE: Esperar aquí a que el proceso de Minecraft termine (se cierre el juego)
            process.wait()

            if callback:
                callback("El juego se ha cerrado.")

        except Exception as e:
            error_msg = f"Error al iniciar el proceso: {str(e)}"
            print(f"[EXCEPCIÓN CRÍTICA] {error_msg}")
            if callback:
                callback(error_msg)
            raise e

    def launch_or_reinstall_instance(self, instance_name: str, username: str, minecraft_version: str, loader_type: str, callback):
        instance_dir = os.path.join(self.base_dir, instance_name)

        installed_version = []
        if os.path.exists(instance_dir):
            installed_version = minecraft_launcher_lib.utils.get_installed_versions(instance_dir)

        if not os.path.exists(instance_dir) or not installed_version:
            if callback:
                callback(f"La instancia '{instance_name}' no se encontró en disco. Instalando...")

            os.makedirs(instance_dir, exist_ok=True)
            
            if loader_type.lower() == "forge":
                if callback:
                    callback(f"Instalando versión base de Minecraft {minecraft_version}...")
                # 1. PRIMERO instalamos el Minecraft base (indispensable para Forge)
                minecraft_launcher_lib.install.install_minecraft_version(minecraft_version, instance_dir)
                
                if callback:
                    callback(f"Buscando e instalando Forge...")
                forge_ver = minecraft_launcher_lib.forge.find_forge_version(minecraft_version)
                minecraft_launcher_lib.forge.install_forge_version(forge_ver, instance_dir)
            else:
                if callback:
                    callback(f"Instalando Minecraft {minecraft_version} (Vanilla)...")
                minecraft_launcher_lib.install.install_minecraft_version(minecraft_version, instance_dir)

            if callback:
                callback("¡Instalación completada con éxito!")

        self.launch_instance(instance_name, username, minecraft_version=minecraft_version, callback=callback)

    
    def _download_and_setup_java(self, instance_dir: str, minecraft_version: str) -> str:
        """
        Descarga automáticamente un JDK portable en la carpeta raíz de la instancia 
        (dentro de 'java_runtime') y devuelve la ruta del ejecutable java.exe.
        """
        java_folder = os.path.join(instance_dir, "java_runtime")
        
        # Si ya fue descargado anteriormente, reutilizamos su ruta directamente
        if os.path.exists(java_folder):
            found = list(Path(java_folder).glob("**/bin/java.exe"))
            if found:
                return str(found[0])

        # Decidir si necesita Java 8 (versiones antiguas) o Java 17 (versiones modernas)
        is_old_version = (
            minecraft_version.startswith("1.7") or 
            minecraft_version.startswith("1.8") or 
            minecraft_version.startswith("1.6") or 
            minecraft_version.startswith("1.12")
        )
        java_major = "8" if is_old_version else "21"
        
        # Enlace oficial de Eclipse Adoptium para Windows x64
        api_url = f"https://api.adoptium.net/v3/binary/latest/{java_major}/ga/windows/x64/jdk/hotspot/normal/eclipse"
        zip_path = os.path.join(instance_dir, f"java_{java_major}.zip")
        
        print(f"📥 Descargando Java {java_major} portable para la instancia...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(api_url, headers=headers, stream=True)
            
            if response.status_code == 200:
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                raise Exception(f"Error HTTP: {response.status_code}")
            
            print(f"📦 Descomprimiendo Java {java_major}...")
            os.makedirs(java_folder, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(java_folder)
                
            # Borrar el archivo .zip para ahorrar espacio en disco
            if os.path.exists(zip_path):
                os.remove(zip_path)
                
            # Encontrar el ejecutable dentro de la carpeta descomprimida
            found = list(Path(java_folder).glob("**/bin/java.exe"))
            if found:
                java_exe = str(found[0])
                print(f"✅ ¡Java portable listo en la instancia!: {java_exe}")
                return java_exe
                
        except Exception as e:
            print(f"❌ Error al configurar Java automáticamente: {e}")
            
        return None

    def delete_instance(self, instance_name: str, callback=None) -> bool:
        try:
            instance_dir = os.path.join(self.base_dir, instance_name)
            if os.path.exists(instance_dir):
                shutil.rmtree(instance_dir)
                if callback:
                    callback(f"Los archivos de la instancia '{instance_name}' fueron eliminados correctamente.")
                InstanceDAO.delete_instance(instance_name)
                return True
            else:
                if callback:
                    callback(f"No se encontró la carpeta de la instancia '{instance_name}' en disco.")
                InstanceDAO.delete_instance(instance_name)
                return False
        except Exception as e:
            if callback:
                callback(f"Error al eliminar la instancia '{instance_name}': {str(e)}")
            return False