from src.logger import setup_logger

logger = setup_logger(__name__)


def main():
    logger.info("Scraper Initialized")


if __name__ == "__main__":
    main()
