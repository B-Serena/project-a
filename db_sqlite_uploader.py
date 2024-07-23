
## SQLite DB 생성 및 데이터 저장

import os
import quandl
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# Quandl API 키 설정 (환경 변수에서 가져오기)
quandl.ApiConfig.api_key = os.getenv('QUANDL_API_KEY')

# SQLite 데이터베이스 엔진 생성
engine = create_engine('sqlite:///stock_data.db')

def get_stock_data(symbol, start_date, end_date):
    """Quandl에서 주식 데이터를 가져옵니다."""
    try:
        data = quandl.get(f"WIKI/{symbol}", start_date=start_date, end_date=end_date)
        return data
    except Exception as e:
        print(f"데이터 가져오기 오류: {e}")
        return None

def save_to_database(data, symbol):
    """데이터를 SQLite 데이터베이스에 저장합니다."""
    try:
        data['Symbol'] = symbol
        data.to_sql('stock_prices', engine, if_exists='append', index=True)
        print(f"{symbol} 데이터가 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"데이터베이스 저장 오류: {e}")

def main():
    if not quandl.ApiConfig.api_key:
        print("QUANDL_API_KEY 환경 변수를 설정해주세요.")
        return

    symbols = ['AAPL', 'GOOGL', 'MSFT']  # 원하는 주식 심볼로 변경하세요
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    for symbol in symbols:
        print(f"{symbol} 데이터 수집 중...")
        stock_data = get_stock_data(symbol, start_date, end_date)
        if stock_data is not None:
            save_to_database(stock_data, symbol)

if __name__ == "__main__":
    main()