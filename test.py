import requests
import xml.etree.ElementTree as ET

def obtener_todas_las_versiones_forge(minecraft_version: str):
    # URL oficial del repositorio Maven de Forge donde se listan todas las versiones históricas
    url = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Analizar el archivo XML de metadatos
            root = ET.fromstring(response.content)
            forge_versions = []
            
            # Buscar todas las etiquetas <version>
            for version in root.findall(".//version"):
                # Filtrar aquellas que comiencen con la versión de Minecraft (ej: "1.7.10-")
                if version.text.startswith(minecraft_version + "-"):
                    forge_versions.append(version.text)
                    
            return forge_versions
        else:
            print("Error al conectar con el servidor de Forge.")
            return []
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return []

# Ejemplo de uso:
if __name__ == "__main__":
    version_buscada = "1.7.10"
    print(f"Buscando todas las versiones de Forge para Minecraft {version_buscada}...")
    
    lista_forge = obtener_todas_las_versiones_forge(version_buscada)
    
    for v in lista_forge:
        print(f"- {v}")