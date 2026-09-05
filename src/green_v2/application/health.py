from green_v2.domain.service_status import ServiceStatus


def get_service_status(version: str) -> ServiceStatus:
    return ServiceStatus(service="green-v2-api", status="ok", version=version)

