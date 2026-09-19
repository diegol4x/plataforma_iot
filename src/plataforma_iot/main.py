"""Punto de entrada principal de la aplicación."""
from plataforma_iot.ingestion.subscriber import run

def main() -> None:
    """Arranca el suscriptor MQTT que persiste lecturas en la base de datos."""
    run()


if __name__ == "__main__":
    main()