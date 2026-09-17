from app.database import engine, Base
from app.models import Event, Photo


def init_database():
    print("Conectando a RDS a través de las credenciales de Secrets Manager...")
    Base.metadata.create_all(bind=engine)
    print("Tablas 'events' y 'photos' verificadas y creadas exitosamente.")


if __name__ == "__main__":
    init_database()