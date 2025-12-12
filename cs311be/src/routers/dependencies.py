from src.services.service import Service

service = Service()

async def get_service() -> Service:
    """
    Resume Flow Service
    """
    return service