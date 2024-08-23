import json
from collections import Counter
import re
from bs4 import BeautifulSoup


MIN_LENGTH = 10
THRESHOLD = 0.8

def clean_html(html):
    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html, 'html.parser')

    # 모든 스크립트와 스타일 요소 제거
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # 모든 태그를 제거하고 텍스트만 추출
    text = soup.get_text(separator=' ')

    # HTML 엔티티 디코딩
    text = soup.get_text(separator=' ')

    # 불필요한 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()

    # CSS 클래스, data-* 속성 등 제거
    text = re.sub(r'\b(?:css|js)-\w+\b', '', text)
    text = re.sub(r'data-\w+=["\']\w+["\']', '', text)

    # 남아있을 수 있는 HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)

    # URL 제거
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # 특수 문자 및 숫자 제거 (선택적)
    # text = re.sub(r'[^가-힣a-zA-Z\s]', '', text)

    return text

def get_common_phrases(texts, min_length=MIN_LENGTH, threshold=THRESHOLD):
    # 모든 텍스트에서 문장 추출
    all_sentences = []
    for text in texts:
        sentences = re.split(r'[.!?]+', text)
        all_sentences.extend([s.strip() for s in sentences if len(s.strip()) >= min_length])
    
    # 문장 빈도 계산
    sentence_counts = Counter(all_sentences)
    
    # 임계값 이상 출현하는 문장 선택
    common_phrases = [phrase for phrase, count in sentence_counts.items() 
                      if count / len(texts) >= threshold]
    
    return common_phrases

def remove_common_phrases(text, common_phrases):
    for phrase in common_phrases:
        text = text.replace(phrase, '')
    return re.sub(r'\s+', ' ', text).strip()

# JSON 파일 읽기
with open('crawled_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 모든 all_text 추출 및 HTML 제거
all_texts = [clean_html(product['all_text']) for product in data]

# 공통 문구 찾기
common_phrases = get_common_phrases(all_texts)

# 각 상품의 텍스트에서 공통 문구 제거
for product in data:
    cleaned_text = clean_html(product['all_text'])
    cleaned_text = remove_common_phrases(cleaned_text, common_phrases)
    product['cleaned_text'] = cleaned_text

# 정제된 데이터를 JSON 파일로 저장
with open('cleaned_data_0823_1512.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("텍스트 정제가 완료되었습니다. 결과는 'cleaned_data.json' 파일에 저장되었습니다.")
print(f"제거된 공통 문구: {common_phrases}")