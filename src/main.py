import sys

from src.logger import setup_logger
from src.cli import parse_arguments
from src.fetcher import DataFetcher
from src.processor import DataProcessor
from src.exporter import DataExporter

logger = setup_logger(__name__)


def main():
    logger.info("Scraper Initialized")

    try:
        # 1. Parse CLI arguments
        args = parse_arguments()
        logger.info(
            "Args: source=%s, search=%s, format=%s, output=%s",
            args.source, args.search, args.format, args.output,
        )

        # 2. Fetch data
        fetcher = DataFetcher()
        params = {}
        if args.search:
            params["search"] = args.search

        raw_data = fetcher.fetch_all_pages(args.source, params=params)
        logger.info("Fetched %d raw records.", len(raw_data))

        if not raw_data:
            logger.warning("No data fetched. Exiting.")
            sys.exit(0)

        # 3. Process data
        processor = DataProcessor()
        processor.load_data(raw_data)
        processor.clean_data()
        processor.deduplicate()

        # Apply optional filter
        if args.filter_key and args.filter_value:
            df = processor.apply_filter(args.filter_key, args.filter_value)
        else:
            df = processor.df

        # 4. Export data
        exporter = DataExporter(df)
        if args.format == "json":
            output_path = exporter.export_to_json(args.output)
        else:
            output_path = exporter.export_to_csv(args.output)

        logger.info("Pipeline complete. Output saved to: %s", output_path)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
