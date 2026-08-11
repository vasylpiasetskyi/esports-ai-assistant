import logging

from ingestion.service import run_reindex

logging.basicConfig(level=logging.INFO)


def main() -> None:
    run_reindex()


if __name__ == "__main__":
    main()
