"""Export the eight clean SQL Server tables to data/extracts/*.csv (useful for deployment without SQL Server)."""
from src import config, data_loader


def main():
    data = data_loader.load_all(source="sql")
    config.EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    for key, filename in config.TABLES.items():
        path = config.EXTRACT_DIR / filename
        data[key].to_csv(path, index=False, encoding="utf-8-sig")
        print(f"{key}: {len(data[key]):,} rows -> {path}")


if __name__ == "__main__":
    main()
