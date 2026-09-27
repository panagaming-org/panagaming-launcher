import minecraft_launcher_lib
import xml.etree.ElementTree as ET
import requests

class VersionsService():
    def __init__(self):
        self.forge_mvn_xml = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
    
    def get_minecraft_versions() -> list:
        all_versions = minecraft_launcher_lib.utils.get_version_list()

        filtered_version = [
            v for v in all_versions
            if v["type"] not in ["snapshot", "old_beta"]
        ]

        return filtered_version

    def get_forge_versions(self, mc_version: str):
        try:
            response = requests.get(self.forge_mvn_xml)
            if response.status_code == 200:
                root =  ET.fromstring(response.content)
                forge_version = []

                for version in root.findall(".//version"):
                    if version.text.startswith(mc_version + "-"):
                        forge_version.append(version.text)

                return forge_version
            else:
                print("Error al conectar con el servidor Forge.")
                return []
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            return []



    