import platform
import os
import shutil
from pathlib import Path
import minecraft_launcher_lib
import subprocess
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
        # Limpiar el nombre para usarlo como una carpeta segura
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        instance_dir = os.path.join(self.base_dir, safe_name)
        os.makedirs(instance_dir, exist_ok=True)

        if callback:
            callback(f"Preparando instancia '{name}' ({loader_type.upper()})...")

        try:
            db = SessionLocal()
            
            # Verificar si ya existe en la base de datos
            existing_instance = InstanceDAO.get_by_name(name)
            if existing_instance:
                raise Exception(f"Ya existe una instancia registrada con el nombre '{name}'.")

            if loader_type.lower() == "forge":
                if not forge_version:
                    if callback:
                        callback(f"Buscando versión de Forge para {minecraft_version}...")
                    forge_version = minecraft_launcher_lib.forge.find_forge_version(minecraft_version)

                if callback:
                    callback(f"Instalando Forge {forge_version} (puede tardar)...")

                minecraft_launcher_lib.forge.install_forge_version(
                    forge_version,
                    instance_dir
                )
                final_loader_version = forge_version
            else:
                final_loader_version = None

                installed_versions = [v["id"] for v in minecraft_launcher_lib.utils.get_installed_versions(instance_dir)]
                if minecraft_version not in installed_versions:
                    if callback:
                        callback(f"Descargando Minecraft {minecraft_version} (Vanilla)...")

                    minecraft_launcher_lib.install.install_minecraft_version(
                        minecraft_version,
                        instance_dir
                    )
                else:
                    if callback:
                        callback(f"La versión {minecraft_version} ya está instalada.")

            # 💾 Registrar la instancia en la base de datos mediante el DAO
            InstanceDAO.create_instance(
                db=db,
                name=name,
                minecraft_version=minecraft_version,
                loader_type=loader_type.lower(),
                loader_version=final_loader_version
            )

            if callback:
                callback(f"¡Instancia '{name}' creada con éxito!")
            
            return True

        except Exception as e:
            if callback:
                print(f"Error al crear la instancia: {str(e)}")
                callback(f"Error al crear la instancia: {str(e)}")
            raise e
        finally:
            db.close()  # Asegurarnos de cerrar la sesión de la BD

    def get_instances(self):
        """
        Obtiene el listado de instancias directamente desde la base de datos usando el DAO.
        """
        db = SessionLocal()
        try:
            db_instances = InstanceDAO.get_all(db)
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
        finally:
            db.close()

    def launch_instance(self, instance_name: str, username: str, minecraft_version: str, callback=None):
        safe_name = "".join(c for c in instance_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        instance_dir = os.path.join(self.base_dir, safe_name)
        
        # Ruta de la carpeta versions de esta instancia aislada
        versions_dir = os.path.join(instance_dir, "versions")
        
        if not os.path.exists(versions_dir):
            if callback:
                callback("Error: No se encontró la carpeta 'versions' en la instancia.")
            return

        # Buscamos de forma autónoma el ID de la versión leyendo los directorios internos
        installed_subdirs = [d for d in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, d))]
        
        if not installed_subdirs:
            if callback:
                callback("Error: No hay versiones instaladas en el directorio.")
            return

        # Seleccionamos el ID basado en la carpeta existente (ej. la de Forge o Vanilla)
        version_id = installed_subdirs[0]
        
        # Si hay varias, priorizamos la que contenga forge o fabric
        for sub in installed_subdirs:
            if "forge" in sub.lower() or "fabric" in sub.lower():
                version_id = sub
                break

        print(f"--> ID de versión detectado directamente en disco: {version_id}")

        if callback:
            callback(f"Configurando entorno Java para {version_id}...")

        is_old_version = minecraft_version.startswith("1.7") or minecraft_version.startswith("1.8") or minecraft_version.startswith("1.6")
        
        java_executable = None
        if is_old_version:
            java_executable = self._find_java_8()
        else:
            try:
                minecraft_launcher_lib.runtime.install_jvm_runtime(minecraft_version, instance_dir)
                java_executable = minecraft_launcher_lib.runtime.get_executable_path(minecraft_version, instance_dir)
            except Exception:
                pass

        if not java_executable or not os.path.exists(java_executable):
            java_executable = "java"

        options = {
            "username": username,
            "uuid": "",
            "token": "",
            "executablePath": java_executable,
            "jvmArguments": ["-Xmx2G", "-XX:+UseG1GC"]
        }

        try:
            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=version_id,
                minecraft_directory=instance_dir,
                options=options
            )

            if callback:
                callback(f"¡Lanzando Minecraft ({instance_name})!")

            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
            )

            def monitor_minecraft():
                for line in process.stdout:
                    print(f"[Minecraft Output] {line.strip()}")

            import threading
            threading.Thread(target=monitor_minecraft, daemon=True).start()
            
        except Exception as e:
            if callback:
                callback(f"Error al iniciar: {str(e)}")
            raise e

    def launch_or_reinstall_instance(self, instance_name: str, username: str, minecraft_version: str, loader_type: str, callback):
        safe_name = "".join(c for c in instance_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        instance_dir = os.path.join(self.base_dir, safe_name)

        installed_version = []
        if os.path.exists(instance_dir):
            installed_version = minecraft_launcher_lib.utils.get_installed_versions(instance_dir)

        if not os.path.exists(instance_dir) or not installed_version:
            if callback:
                callback(f"La instancia '{instance_name}' no se encontró en disco. Instalando...")

            os.makedirs(instance_dir, exist_ok=True)
            if loader_type.lower() == "forge":
                forge_ver = minecraft_launcher_lib.forge.find_forge_version(minecraft_version)
                minecraft_launcher_lib.forge.install_forge_version(forge_ver, instance_dir)
            else:
                minecraft_launcher_lib.install.install_minecraft_version(minecraft_version, instance_dir)

            if callback:
                callback("¡Instalación completada con éxito!")

        self.launch_instance(instance_name, username, minecraft_version=minecraft_version, callback=callback)

    def _find_java_8(self):
        """Busca específicamente Java 8 en el equipo para tolerar versiones antiguas como 1.7.10"""
        import shutil
        # Intenta buscar el comando java general, pero idealmente busca rutas comunes de Java 8 en Windows
        if platform.system() == "Windows":
            paths_to_check = [
                r"C:\Program Files\Java\jdk1.8.0_*\bin\java.exe",
                r"C:\Program Files\Java\jre1.8.0_*\bin\java.exe",
                r"C:\Program Files (x86)\Java\jdk1.8.0_*\bin\java.exe",
                r"C:\Program Files (x86)\Java\jre1.8.0_*\bin\java.exe",
                r"C:\Clementine\Java\..." # Rutas personalizadas si las hubiera
            ]
            import glob
            for pattern in paths_to_check:
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]
        return shutil.which("java") or "java"