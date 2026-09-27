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

    def launch_instance(self, instance_name: str, username: str = "PanaPlayer", callback=None):
        """
        Busca la instancia (puedes apoyarte en el DAO o en el directorio) y ejecuta el juego.
        """
        # Limpiamos el nombre igual que al crearlo para ubicar su directorio
        safe_name = "".join(c for c in instance_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        instance_dir = os.path.join(self.base_dir, safe_name)
        
        if not os.path.exists(instance_dir):
            if callback:
                callback("Error: La carpeta física de la instancia no existe.")
            return

        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(instance_dir)
        if not installed_versions:
            if callback:
                callback("Error: No hay ninguna versión instalada en esta instancia.")
            return

        version_id = installed_versions[0]["id"]
        for v in installed_versions:
            if "forge" in v["id"].lower() or "fabric" in v["id"].lower():
                version_id = v["id"]
                break

        if callback:
            callback(f"Preparando lanzamiento para '{instance_name}'...")

        options = {
            "username": username,
            "uuid": "",
            "token": "",
            "jvmArguments": ["-Xmx2G", "-XX:+UseG1GC"]
        }

        try:
            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=version_id,
                minecraft_directory=instance_dir,
                options=options
            )

            if callback:
                callback(f"¡Ejecutando Minecraft ({instance_name})!")

            subprocess.Popen(command)
            
        except Exception as e:
            if callback:
                callback(f"Error al iniciar el juego: {str(e)}")
            raise e