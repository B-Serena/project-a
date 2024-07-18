

## Kurly 데이터 크롤링 및 Pinecone DB 에 저장

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def crawl_kurly():
    driver = webdriver.Safari()
    try:
        driver.get("https://www.kurly.com/main")
        
        # 페이지가 완전히 로드될 때까지 대기 (최대 30초)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "css-1ud9i0q"))
        )
        
        # 페이지 스크롤
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # 페이지 소스 가져오기
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 상품 정보 추출
        products = []
        for product in soup.find_all("div", class_="css-1ud9i0q"):
            name = product.find("h3")
            price = product.find("span", class_="sales-price")
            
            name_text = name.text.strip() if name else "No name"
            price_text = price.text.strip() if price else "No price"
            products.append(f"{name_text}: {price_text}")
        
        return products
    finally:
        driver.quit()

# 크롤링 실행
crawled_data = crawl_kurly()

# 결과 출력
print(f"크롤링된 상품 수: {len(crawled_data)}")
for product in crawled_data[:5]:  # 처음 5개 상품만 출력
    print(product)

# 여기에 Pinecone 업로드 코드를 추가할 수 있습니다.

# =======


# if not crawled_data:
#     print("No products were crawled. Exiting.")
# else:
#     # 벡터 임베딩 생성
#     model = SentenceTransformer('distilbert-base-nli-mean-tokens')
#     embeddings = model.encode(crawled_data)

#     # Pinecone 설정 (최신 버전)
#     pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

#     index_name = "kurly-products"

#     # 인덱스가 없으면 생성
#     if index_name not in pc.list_indexes():
#         pc.create_index(
#             name=index_name,
#             dimension=model.get_sentence_embedding_dimension(),
#             metric='cosine',
#             spec=ServerlessSpec(
#                 cloud='aws',
#                 region='us-east-1'  # 사용하려는 리전으로 변경하세요
#             )
#         )

#     # 인덱스에 연결
#     index = pc.Index(index_name)

#     # 데이터를 Pinecone에 업로드
#     for i, (text, embedding) in enumerate(zip(crawled_data, embeddings)):
#         index.upsert(vectors=[(str(i), embedding.tolist(), {"text": text})])
#         if i % 100 == 0:  # 매 100개 항목마다 잠시 대기
#             time.sleep(1)

#     print(f"{len(crawled_data)} 개의 상품 정보가 Pinecone에 업로드되었습니다.")