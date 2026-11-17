import uvicorn

from pos.settings import Settings


def main() -> None:
    settings = Settings()
    uvicorn.run(
        "pos.adapters.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
    )


if __name__ == "__main__":
    main()
