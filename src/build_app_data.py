"""Precompute dashboard CSVs for reproducibility and non-Streamlit inspection."""
from src import config,data_loader
from src.analysis import build_dashboard_tables

def main():
    data=data_loader.load_all()
    tables=build_dashboard_tables(data)
    config.APP_DATA_DIR.mkdir(parents=True,exist_ok=True)
    for name,frame in tables.items():
        path=config.APP_DATA_DIR/f'{name}.csv'; frame.to_csv(path,index=False,encoding='utf-8-sig')
        print(f'{name}: {len(frame):,} rows -> {path}')
    print(data_loader.data_status()['message'])
if __name__=='__main__': main()
