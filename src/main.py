import sys

import pandas as pd

from src.logger import setup_logger
from src.cli import parse_arguments
from src.fetcher import DataFetcher, BrowserFetcher
from src.processor import DataProcessor
from src.exporter import DataExporter
from src.proxy_manager import ProxyManager

logger = setup_logger(__name__)


def main():
    logger.info("Scraper Initialized")

    try:
        # 1. Parse CLI arguments
        args = parse_arguments()
        logger.info(
            "Args: source=%s, search=%s, format=%s, output=%s, "
            "use_browser=%s, proxies=%s",
            args.source, args.search, args.format, args.output,
            args.use_browser, args.proxies,
        )

        # 2. Resolve proxy (if provided)
        proxy = None
        if args.proxies:
            proxy_manager = ProxyManager(args.proxies)
            proxy = proxy_manager.get_next_proxy()
            if proxy:
                logger.info("Proxy selected: %s", proxy)
            else:
                logger.warning("No usable proxy found. Proceeding without proxy.")

        # 3. Fetch data
        if args.use_browser:
            logger.info("Using BrowserFetcher (Playwright stealth mode).")
            browser_fetcher = BrowserFetcher(proxy=proxy)
            raw_html = browser_fetcher.fetch_html(args.source)

            # Attempt to extract tables from the HTML
            try:
                tables = pd.read_html(raw_html)
                if tables:
                    raw_data = tables[0].to_dict(orient="records")
                    logger.info(
                        "Extracted %d records from HTML table.", len(raw_data),
                    )
                else:
                    logger.warning("No tables found in HTML. Exiting.")
                    sys.exit(0)
            except ValueError:
                logger.warning("No tables found in HTML by pd.read_html. Exiting.")
                sys.exit(0)
        else:
            logger.info("Using DataFetcher (standard requests).")
            fetcher = DataFetcher()
            if proxy:
                fetcher.session.proxies.update(
                    {"http": proxy, "https": proxy}
                )
                logger.info("Proxy applied to DataFetcher session.")

            params = {}
            if args.search:
                params["search"] = args.search

            raw_data = fetcher.fetch_all_pages(args.source, params=params)
            logger.info("Fetched %d raw records.", len(raw_data))

        if not raw_data:
            logger.warning("No data fetched. Exiting.")
            sys.exit(0)

        # 4. Process data
        processor = DataProcessor()
        processor.load_data(raw_data)
        processor.clean_data()
        processor.deduplicate()

        # Apply optional filter
        if args.filter_key and args.filter_value:
            df = processor.apply_filter(args.filter_key, args.filter_value)
        else:
            df = processor.df

        # 5. Export data
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
