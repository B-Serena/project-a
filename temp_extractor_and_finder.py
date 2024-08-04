
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# .env 파일에서 환경 변수 로드 (만약 .env 파일을 사용한다면)
load_dotenv()

# OpenAI 클라이언트 설정
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pinecone 설정
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("kurly-products") 

# ~~ 사용할 모델 설정
model = SentenceTransformer('all-MiniLM-L6-v2')

# 검색에서 제외할 재료
EXCLUDED_INGREDIENTS = {'물'}  # 제외할 재료들의 집합

def extract_ingredients(recipe_text: str) -> List[str]:
    prompt = f"""
    다음 레시피에서 필요한 모든 재료를 추출하여 JSON 형식의 리스트로 작성해주세요. 
    수량은 제외하고 재료명만 포함하세요. 또한, 각 재료에 대한 간단한 설명을 추가해주세요.

    레시피:
    {recipe_text}

    JSON 형식 예시:
    {{
        "ingredients": [
            {{"name": "재료1", "description": "재료1에 대한 설명"}},
            {{"name": "재료2", "description": "재료2에 대한 설명"}},
            {{"name": "재료3", "description": "재료3에 대한 설명"}}
        ]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 레시피에서 재료를 추출하고 설명하는 전문가입니다."},
            {"role": "user", "content": prompt}
        ]
    )

    # # (option) gpt-4o-mini 의 response format 고려
    # text = response.choices[0].message.content
    # if text.startswith('```json\n'):
    #     text = text[8:-4]
    # result = json.loads(text)

    # # gpt-3.5-turbo 의 response format 고려
    result = json.loads(response.choices[0].message.content)

    return [ingredient for ingredient in result['ingredients'] if ingredient['name'].lower() not in EXCLUDED_INGREDIENTS]

def get_embedding(text: str) -> List[float]:
    return model.encode([text])[0].tolist()

def search_products_in_pinecone(ingredient: Dict[str, str], top_k: int = 5) -> List[Dict[str, str]]:
    query_embedding = get_embedding(f"{ingredient['name']} {ingredient['description']}")
    results = index.query(
        vector=query_embedding,
        top_k=top_k * 2,  # 더 많은 결과를 가져와서 필터링
        include_metadata=True
    )
    
    if not results['matches']:
        print(f"No matches found for ingredient: {ingredient['name']}")
        return []
    
    filtered_matches = [
        match for match in results['matches']
        if ingredient['name'].lower() in match['metadata'].get('name', '').lower()
    ]
    
    if not filtered_matches:
        print(f"No filtered matches found for ingredient: {ingredient['name']}")
        return []
    
    # 코사인 유사도 계산
    product_embeddings = [match['values'] for match in filtered_matches]
    similarities = cosine_similarity([query_embedding], product_embeddings)[0]
    
    # 유사도에 따라 정렬
    sorted_products = sorted(zip(filtered_matches, similarities), key=lambda x: x[1], reverse=True)
    
    return [
        {
            'product_name': product['metadata'].get('name', 'Unknown Product'),
            'discount_rate': product['metadata'].get('discount_rate', '0'),
            'price': product['metadata'].get('price', 'N/A'),
            'link': f"https://www.kurly.com/goods/{product['id']}",
            'similarity': similarity
        }
        for product, similarity in sorted_products[:top_k]
    ]

def generate_product_recommendations(ingredient: Dict[str, str], products: List[Dict[str, str]]) -> str:
    prompt = f"""
    다음은 레시피의 재료 "{ingredient['name']}"에 대한 설명과 이에 맞는 상품 목록입니다:

    재료 설명: {ingredient['description']}

    상품 목록:
    {json.dumps(products, indent=2, ensure_ascii=False)}

    위 정보를 바탕으로, 요리에 가장 적합한 상품을 추천하고 그 이유를 설명해주세요. 
    가격, 할인율, 상품의 특성 등을 고려하여 추천해주세요.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 요리 재료 전문가이며, 고객에게 최적의 상품을 추천하는 역할을 합니다."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def process_recipe(recipe_text: str) -> List[Dict[str, str]]:
    ingredients = extract_ingredients(recipe_text)
    results = []
    for ingredient in ingredients:
        try:
            products = search_products_in_pinecone(ingredient)
            print(products)
            if products:
                recommendation = generate_product_recommendations(ingredient, products)
                results.append({
                    'ingredient': ingredient['name'],
                    'description': ingredient['description'],
                    'recommended_products': products,
                    'recommendation': recommendation
                })
            else:
                results.append({
                    'ingredient': ingredient['name'],
                    'description': ingredient['description'],
                    'recommended_products': [],
                    'recommendation': '해당 재료에 맞는 상품을 찾을 수 없습니다.'
                })
        except Exception as e:
            print(f"Error processing ingredient {ingredient['name']}: {str(e)}")
            results.append({
                'ingredient': ingredient['name'],
                'description': ingredient['description'],
                'recommended_products': [],
                'recommendation': '처리 중 오류가 발생했습니다.'
            })
    return results

if __name__ == "__main__":
    recipe_text = """
    맛있는 토마토 파스타 만들기:
    1. 올리브 오일을 팬에 두르고 다진 마늘을 볶는다.
    2. 방울토마토를 반으로 잘라 넣고 중불에서 익힌다.
    3. 삶은 파스타면을 넣고 소금, 후추로 간을 한다.
    4. 바질 잎을 뿌려 마무리한다.
    """

    results = process_recipe(recipe_text)
    for result in results:
        print(f"\n재료: {result['ingredient']}")
        print(f"설명: {result['description']}")
        print("추천 상품:")
        for product in result['recommended_products']:
            print(f"- {product['product_name']} (가격: {product['price']}, 할인율: {product['discount_rate']}, 유사도: {product['similarity']:.2f})")
            print(f"  구매 링크: {product['link']}")
        print(f"\n전문가 추천: {result['recommendation']}")