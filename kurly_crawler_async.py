import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

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
            EC.presence_of_element_located((By.CSS_SELECTOR, ".css-79gmk3.ezpe9l11"))
        )
        
        name = driver.find_element(By.CSS_SELECTOR, ".css-79gmk3.ezpe9l11").text
        price = driver.find_element(By.CSS_SELECTOR, ".css-9pf1ze.e1q8tigr2").text
        
        try:
            discount_rate = driver.find_element(By.CSS_SELECTOR, ".css-5nirzt.e1q8tigr3").text
        except NoSuchElementException:
            discount_rate = "할인 정보 없음"

        try:
            origin = driver.find_element(By.CSS_SELECTOR, ".css-1jali72.e17iylht2").text
        except NoSuchElementException:
            origin = "원산지 정보 없음"
        
        try:
            description = driver.find_element(By.CSS_SELECTOR, "[data-testid='product-description']").text
        except NoSuchElementException:
            description = "설명 정보 없음"
        
        additional_info = {}
        try:
            info_table = driver.find_element(By.CSS_SELECTOR, ".css-1t5l6f")
            rows = info_table.find_elements(By.CSS_SELECTOR, "tr")
            for row in rows:
                key = row.find_element(By.CSS_SELECTOR, "th").text
                value = row.find_element(By.CSS_SELECTOR, "td").text
                additional_info[key] = value
        except NoSuchElementException:
            pass
        
        return {
            "name": name,
            "price": price,
            "discount_rate": discount_rate,
            "origin": origin,
            "description": description,
            "additional_info": additional_info
        }
    
    return retry_on_exception(_crawl)

def crawl_category(number):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    
    all_data = []
    page = 1
    
    try:
        while True:
            url = f"https://www.kurly.com/categories/{number}?page={page}"
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
                    product_id = product_link.split("/")[-1]
                    product_data = crawl_product_detail(driver, product_link)
                    product_data["category"] = number
                    product_data["id"] = product_id
                    all_data.append(product_data)
                except Exception as e:
                    print(f"상품 정보 크롤링 중 오류 발생: {e}")
                    continue

            page += 1
            time.sleep(random.uniform(1, 3))  # 무작위 대기 시간 추가
    except Exception as e:
        print(f"카테고리 {number} 크롤링 중 오류 발생: {e}")
    finally:
        driver.quit()
    
    return all_data

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

    num_processes = min(cpu_count(), len(numbers))
    with Pool(num_processes) as pool:
        results = list(tqdm(pool.imap(crawl_category, numbers), total=len(numbers), desc="Crawling categories"))

    all_data = [item for sublist in results for item in sublist]
    return all_data

def save_data(data):
    with open('crawled_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    crawled_data = crawl_kurly()
    save_data(crawled_data)
    print(f"총 {len(crawled_data)}개의 상품 정보를 크롤링했습니다.")