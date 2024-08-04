from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import json
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (만약 .env 파일을 사용한다면)
load_dotenv()

def load_crawled_data(file_path='crawled_data.json'):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def upload_to_pinecone(data):
    # 환경 변수에서 Pinecone 설정 가져오기
    api_key = os.getenv('PINECONE_API_KEY')
    cloud = os.getenv('PINECONE_CLOUD', 'aws')  # 기본값 'aws'
    region = os.getenv('PINECONE_REGION')

    print(api_key)
    print(cloud)
    print(region)

    if not api_key or not region:
        raise ValueError("Pinecone API 키 또는 리전이 설정되지 않았습니다. 환경 변수를 확인해주세요.")

    # Pinecone 인스턴스 생성
    pc = Pinecone(api_key=api_key)

    # 인덱스 이름 설정
    index_name = "kurly-products"
    print(index_name)

    # 인덱스가 존재하지 않으면 생성
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric='cosine',
            spec=ServerlessSpec(
                cloud=cloud,
                region=region
            )
        )

    # 인덱스 연결
    index = pc.Index(index_name)
    print("index connected")

    # 문장 임베딩 모델 로드
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # import shutil 
    # # 기존 캐시 삭제
    # cache_dir = os.path.expanduser('~/.cache/torch/sentence_transformers')
    # if os.path.exists(cache_dir):
    #     shutil.rmtree(cache_dir)

    # # sentence-transformers 재설치
    # os.system("pip uninstall -y sentence-transformers")
    # os.system("pip install sentence-transformers")

    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # model = SentenceTransformer('distilbert-base-nli-mean-tokens')
    
    print("model embeded")

    print("model uploading start")

    # 데이터를 Pinecone에 업로드
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        ids = [item["id"] for item in batch]
        texts = [f"{item['name']} {item['description']}" for item in batch]
        embeddings = model.encode(texts).tolist()
        metadata = [{
            "category": item["category"],
            "name": item["name"],
            "price": item["price"],
            "discount_rate": item.get("discount_rate", ""),
            "origin": item.get("origin", ""),
            "description": item["description"],
            "additional_info": json.dumps(item.get("additional_info", {}))  # JSON 문자열로 변환
        } for item in batch]
        
        to_upsert = list(zip(ids, embeddings, metadata))
        index.upsert(vectors=to_upsert)

        print(f"{i+len(batch)}개의 상품 정보를 Pinecone에 업로드했습니다.")

    print(f"총 {len(data)}개의 상품 정보를 Pinecone에 업로드 완료했습니다.")

if __name__ == "__main__":
    try:
        # 크롤링한 데이터 불러오기
        crawled_data = load_crawled_data()

        # Pinecone에 데이터 업로드
        upload_to_pinecone(crawled_data)
    except Exception as e:
        print(f"오류 발생: {e}")