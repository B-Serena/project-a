
## Pinecone DB 생성 및 데이터 저장
import os
import quandl
from pinecone import Pinecone, ServerlessSpec
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Quandl API 키 설정 (환경 변수에서 가져오기)
quandl.ApiConfig.api_key = os.getenv('QUANDL_API_KEY')

# Pinecone 초기화
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Pinecone 인덱스 생성 (또는 기존 인덱스 연결)
index_name = "stock_data"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=6,  # 6은 저장할 특성의 수입니다
        metric='euclidean',
        spec=ServerlessSpec(
            cloud=os.getenv('PINECONE_CLOUD', 'aws'),  # 'aws' 또는 'gcp'
            region=os.getenv('PINECONE_REGION', 'us-east-1')  # 예: 'us-west-2'
        )
    )
index = pc.Index(index_name)

def get_stock_data(symbol, start_date, end_date):
    """Quandl에서 주식 데이터를 가져옵니다."""
    try:
        data = quandl.get(f"WIKI/{symbol}", start_date=start_date, end_date=end_date)
        return data
    except Exception as e:
        print(f"데이터 가져오기 오류: {e}")
        return None

def prepare_vector(row):
    """주식 데이터를 벡터로 변환합니다."""
    return [
        float(row['Open']),
        float(row['High']),
        float(row['Low']),
        float(row['Close']),
        float(row['Volume']),
        float(row['Adj. Close'])
    ]

def save_to_vectordb(data, symbol):
    """데이터를 Pinecone Vector DB에 저장합니다."""
    try:
        vectors = []
        for date, row in data.iterrows():
            vector = prepare_vector(row)
            vectors.append((f"{symbol}_{date.strftime('%Y-%m-%d')}", vector, {"symbol": symbol, "date": str(date)}))
        
        # 배치로 벡터 업서트
        index.upsert(vectors=vectors)
        print(f"{symbol} 데이터가 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"데이터베이스 저장 오류: {e}")

def main():
    # API 키 확인
    if not quandl.ApiConfig.api_key:
        print("QUANDL_API_KEY 환경 변수가 설정되지 않았습니다.")
        return
    if not os.getenv('PINECONE_API_KEY'):
        print("PINECONE_API_KEY 환경 변수가 설정되지 않았습니다.")
        return

    symbols = ['AAPL', 'GOOGL', 'MSFT']  # 원하는 주식 심볼로 변경하세요
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    for symbol in symbols:
        print(f"{symbol} 데이터 수집 중...")
        stock_data = get_stock_data(symbol, start_date, end_date)
        if stock_data is not None:
            save_to_vectordb(stock_data, symbol)

if __name__ == "__main__":
    main()



## Pinecone 생성

# from pinecone import Pinecone, ServerlessSpec

# pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# pc.create_index(
#     name="quickstart",
#     dimension=2, # Replace with your model dimensions
#     metric="cosine", # Replace with your model metric
#     spec=ServerlessSpec(
#         cloud="aws",
#         region="us-east-1"
#     ) 
# )
