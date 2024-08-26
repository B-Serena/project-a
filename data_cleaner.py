import json
import re
import nltk
from tqdm import tqdm
from io import StringIO
import sys

nltk.download('punkt', quiet=True)
from nltk.tokenize import word_tokenize

def clean_text(text):
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 특수 문자 및 숫자 제거 (단, 한글, 영문, 공백은 유지)
    text = re.sub(r'[^\w\s가-힣]', '', text)
    return text

def count_tokens(text):
    return len(word_tokenize(text))

def process_product(product_data):
    product_id = product_data.get('id', 'Unknown')
    product_url = product_data.get('url', '')
    product_text = product_data.get('all_text', '')
    cleaned_text = clean_text(product_text)
    token_count = count_tokens(cleaned_text)
    return {
        'id': product_id,
        'url': product_url,
        'token_count': token_count,
        'cleaned_text': cleaned_text,  # 전체 정제된 텍스트 저장
        'text_preview': cleaned_text[:100]  # 미리보기용 (처음 100자)
    }

# 출력을 캡처하기 위해 StringIO 객체를 사용합니다.
old_stdout = sys.stdout
result = StringIO()
sys.stdout = result

# JSON 파일 읽기
with open('crawled_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 모든 상품 처리
processed_products = []
for product in tqdm(data, desc="Processing products"):
    processed_products.append(process_product(product))

# 결과 분석
total_products = len(processed_products)
total_tokens = sum(p['token_count'] for p in processed_products)
avg_tokens = total_tokens / total_products if total_products > 0 else 0

print(f"총 상품 수: {total_products}")
print(f"총 토큰 수: {total_tokens}")
print(f"평균 토큰 수: {avg_tokens:.2f}")

# 토큰 수 분포
token_counts = [p['token_count'] for p in processed_products]
print(f"최소 토큰 수: {min(token_counts)}")
print(f"최대 토큰 수: {max(token_counts)}")

# 샘플 출력 (처음 5개 상품)
print("\n샘플 상품 정보:")
for product in processed_products[:5]:
    print(f"ID: {product['id']}")
    print(f"URL: {product['url']}")
    print(f"토큰 수: {product['token_count']}")
    print(f"텍스트 미리보기: {product['text_preview']}...")
    print()

# 토큰 수가 8192를 초과하는 상품 확인
over_limit_products = [p for p in processed_products if p['token_count'] > 8192]
print(f"\n토큰 수가 8192를 초과하는 상품 수: {len(over_limit_products)}")
if over_limit_products:
    print("초과 상품 예시:")
    for product in over_limit_products[:3]:  # 처음 3개만 출력
        print(f"ID: {product['id']}, URL: {product['url']}, 토큰 수: {product['token_count']}")

# 토큰 수 구간별 상품 수 계산
token_ranges = [(0, 1000), (1001, 2000), (2001, 4000), (4001, 8192), (8193, float('inf'))]
range_counts = {f"{start}-{end}": sum(start <= p['token_count'] <= end for p in processed_products) 
                for start, end in token_ranges}

print("\n토큰 수 구간별 상품 수:")
for range_name, count in range_counts.items():
    print(f"{range_name} 토큰: {count}개 상품")

# 출력 캡처 종료
sys.stdout = old_stdout
summary = result.getvalue()

# summary.txt 파일 저장
with open('processed_data_summary.txt', 'w', encoding='utf-8') as f:
    f.write(summary)

# processed_data.json 파일 저장
with open('processed_data.json', 'w', encoding='utf-8') as f:
    json.dump(processed_products, f, ensure_ascii=False, indent=2)

print("summary.txt와 processed_data.json 파일이 생성되었습니다.")