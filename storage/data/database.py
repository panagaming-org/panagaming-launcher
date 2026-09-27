from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ruta de la base de datos local SQLite en la raíz del proyecto del launcher
SQLALCHEMY_DATABASE_URL = "sqlite:///storage/data/database.db"

# Crear el motor de la base de datos (con check_same_thread=False para compatibilidad con hilos en Flet)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Fábrica de sesiones para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para definir los modelos/tablas
Base = declarative_base()

def init_db():
    """Crea las tablas en la base de datos si aún no existen."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Generador para obtener una sesión de base de datos de forma segura."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()