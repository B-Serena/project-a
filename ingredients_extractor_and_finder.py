

import os
import json
import time
from typing import Optional, List, Dict
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai import OpenAIError, RateLimitError, APIError
from pinecone import Pinecone

from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (만약 .env 파일을 사용한다면)
load_dotenv()

# OpenAI 클라이언트 설정
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pinecone 설정
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("kurly-products") 


# 레시피 텍스트 준비 (예시)
recipe_text = """
맛있는 파스타 만들기:
1. 물 2리터를 끓인다.
2. 소금 1큰술을 넣는다.
3. 파스타 500g을 넣고 8분간 삶는다.
4. 올리브 오일 2큰술을 팬에 두르고 다진 마늘 2쪽을 볶는다.
5. 삶은 파스타를 팬에 넣고 소금, 후추로 간을 한다.
6. 파마산 치즈를 뿌려 마무리한다.
"""

# 프롬프트 설계
prompt = f"""
다음 레시피에서 필요한 모든 재료를 추출하여 JSON 형식의 리스트로 작성해주세요. 
수량은 제외하고 재료명만 포함하세요.

레시피:
{recipe_text}

JSON 형식 예시:
{{"ingredients": ["재료1", "재료2", "재료3"]}}
"""

def extract_ingredients(retry_attempts: int = 3, retry_delay: int = 5) -> List[str]:
    for attempt in range(retry_attempts):
        try:
            response: ChatCompletion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 레시피에서 재료를 추출하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            result = json.loads(response.choices[0].message.content)
            return result['ingredients']
        except (RateLimitError, APIError, OpenAIError) as e:
            if attempt < retry_attempts - 1:
                print(f"Error occurred: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Error after {retry_attempts} attempts: {e}")
                raise e

def search_product_in_pinecone(ingredient: str) -> Optional[Dict[str, str]]:
    try:
        response = client.embeddings.create(input=[ingredient], model="text-embedding-ada-002")
        query_embedding = response.data[0].embedding
        results = index.query(vector=query_embedding, top_k=1, include_metadata=True)
        if results['matches']:
            return results['matches'][0]['metadata']
        return None
    except Exception as e:
        print(f"Error searching for {ingredient}: {e}")
        return None

try:
    ingredients = extract_ingredients()
    print("추출된 재료와 구매 링크:")
    for ingredient in ingredients:
        product_info = search_product_in_pinecone(ingredient)
        if product_info:
            print(f"- {ingredient}: {product_info['product_name']} - 구매 링크: {product_info['link']}")
        else:
            print(f"- {ingredient}: 구매 링크를 찾을 수 없습니다.")
except Exception as e:
    print(f"처리 중 오류가 발생했습니다: {e}")