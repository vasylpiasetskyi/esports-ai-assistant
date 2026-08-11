import logging

from crawler.service import run_crawl

logging.basicConfig(level=logging.INFO)


def main() -> None:
    run_crawl()


if __name__ == "__main__":
    main()
