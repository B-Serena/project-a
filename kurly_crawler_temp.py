import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.safari.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

def retry_on_exception(func, max_attempts=3, delay=5):
    for attempt in range(max_attempts):
        try:
            return func()
        except (NoSuchElementException, TimeoutException, WebDriverException) as e:
            if attempt == max_attempts - 1:
                raise
            print(f"오류 발생: {e}. {delay}초 후 재시도합니다...")
            time.sleep(delay)

def crawl_product_detail(driver, product_url):
    def _crawl():
        driver.get(product_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 페이지의 모든 텍스트 추출
        all_text = driver.find_element(By.TAG_NAME, "body").text
        
        # 제품 ID 추출 (URL에서)
        product_id = product_url.split("/")[-1]
        
        return {
            "id": product_id,
            "url": product_url,
            "all_text": all_text
        }
    
    return retry_on_exception(_crawl)

def save_progress(number, page):
    with open('crawling_progress.json', 'w') as f:
        json.dump({'last_category': number, 'last_page': page}, f)

def load_progress():
    if os.path.exists('crawling_progress.json'):
        with open('crawling_progress.json', 'r') as f:
            return json.load(f)
    return None

def save_data(data):
    with open('crawled_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def crawl_kurly():
    numbers = [
        '018', '019', '032', '085', '249', '251', '383', '722', '907', '908', '909', '910', '911', '912', '913', '914', '915', '916', '918',
        '383001', '383002', '383003', '383004', '383005', '383006', '383007', '383008', '383009', '383010', '383011',
        '907001', '907002', '907003', '907004', '907005', '907006', '907007', '907008',
        '908001', '908002', '908003', '908004', '908005', '908006', '908007', '908008',
        '909001', '909002', '909003', '909004', '909005', '909006', '909007', '909009', '909010', '909011', '909012', '909013', '909014', '909015',
        '910001', '910002', '910003', '910004', '910005', '910007', '910009', '910010', '910011', '910012',
        '912001', '912002', '912003', '912004', '912005', '912008', '912011'
    ]

    safari_options = Options()
    safari_options.add_argument("--headless")

    all_data = []

    progress = load_progress()
    start_index = numbers.index(progress['last_category']) if progress else 0
    start_page = progress['last_page'] if progress else 1

    for number in numbers[start_index:]:
        driver = webdriver.Safari(options=safari_options)
        driver.set_page_load_timeout(30)
        
        page = start_page if number == numbers[start_index] else 1
        while True:
            url = f"https://www.kurly.com/categories/{number}?page={page}"
            try:
                driver.get(url)
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".css-11kh0cw"))
                )

                products = driver.find_elements(By.CSS_SELECTOR, ".css-11kh0cw")
                
                if not products:
                    break

                for product in products:
                    try:
                        product_link = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        product_data = crawl_product_detail(driver, product_link)
                        product_data["category"] = number
                        all_data.append(product_data)
                    except Exception as e:
                        print(f"상품 정보 크롤링 중 오류 발생: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

                save_progress(number, page)
                
                if len(all_data) % 100 == 0:
                    save_data(all_data)

            except TimeoutException:
                print(f"카테고리 {number}의 페이지 {page}를 로드하는 데 실패했습니다. 다음 카테고리로 이동합니다.")
                break
            except WebDriverException:
                print(f"WebDriver 오류 발생. 카테고리 {number}의 페이지 {page}에서 크롤링을 중단합니다.")
                break

        driver.quit()

    save_data(all_data)
    return all_data

crawled_data = crawl_kurly()
print(f"총 {len(crawled_data)}개의 상품 정보를 크롤링했습니다.")

for product in crawled_data[:5]:
    print(f"ID: {product['id']}")
    print(f"Category: {product['category']}")
    print(f"URL: {product['url']}")
    print(f"Text (first 200 characters): {product['all_text'][:200]}...")
    print("-" * 50)