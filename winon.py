import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
import json
import numpy as np
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# 현재 날짜 가져오기
current_date = datetime.now().strftime("%Y-%m-%d")
filename = f"winon_{current_date}.json"

# 웹 드라이버 실행 (헤드리스 모드)
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=service, options=options)

keyword = '위넌스터디카페'
url = f'https://map.naver.com/p/search/{keyword}'
driver.get(url)
action = ActionChains(driver)

naver_res = pd.DataFrame(columns=['title', 'address', 'phone', 'image', 'nZapA', 'menu_tab', 'reviews', 'photos', 'information'])
last_name = ''

def search_iframe():
    driver.switch_to.default_content()
    driver.switch_to.frame("searchIframe")

def entry_iframe():
    driver.switch_to.default_content()
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]')))
        for _ in range(5):
            time.sleep(0.5)
            try:
                driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="entryIframe"]'))
                break
            except:
                pass
    except:
        print("entryIframe을 찾지 못했습니다. 다음 요소로 넘어갑니다.")

def chk_names():
    search_iframe()
    elem = driver.find_elements(By.CSS_SELECTOR, '.place_bluelink')
    name_list = [e.text for e in elem]
    return elem, name_list

def ensure_equal_length(*args):
    max_len = max(len(lst) for lst in args)
    for lst in args:
        while len(lst) < max_len:
            lst.append(np.nan)

def get_tab_content(tab_name):
    try:
        tab_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f'//span[@class="veBoZ" and text()="{tab_name}"]')))
        tab_button.click()
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup
    except:
        return None

def get_menu_content(soup):
    menu_items = []
    try:
        ul_elem = soup.select_one('div.place_section_content ul')
        if ul_elem:
            for li in ul_elem.select('li.E2jtL'):
                item_name = li.text.strip()
                item_image = li.select_one('img')['src'] if li.select_one('img') else None
                menu_items.append({'name': item_name, 'image': item_image})
    except:
        pass
    return menu_items

def get_reviews_content(soup):
    reviews_data = {}
    try:
        reviews_participation = soup.select_one('div.place_section.no_margin.ySHNE span.jypaX').text
        reviews_data['participation'] = reviews_participation
    except:
        reviews_data['participation'] = None

    try:
        review_elements = soup.select('ul.mrSZf > li.MHaAm')
        reviews = [{'review_text': review.text.strip()} for review in review_elements]
        reviews_data['reviews'] = reviews
    except:
        reviews_data['reviews'] = []

    return reviews_data

def get_photos_content():
    photo_urls = []
    try:
        while True:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            images = soup.select('div.Nd2nM img')
            new_image_urls = [img['src'] for img in images if img['src'] not in photo_urls]
            if not new_image_urls:
                break
            photo_urls.extend(new_image_urls)
            action.move_to_element(images[-1]).perform()
            time.sleep(1)
    except:
        pass
    return photo_urls

def get_information_content(soup):
    info_data = {}
    try:
        introduction = soup.select_one('div.place_section.no_margin.Od79H').text.strip()
        info_data['introduction'] = introduction
    except:
        info_data['introduction'] = None

    try:
        additional_info1 = soup.select_one('div.place_section.no_margin.kBQcG').text.strip()
        info_data['additional_info1'] = additional_info1
    except:
        info_data['additional_info1'] = None

    try:
        additional_info2 = soup.select_one('div.place_section.no_margin.hK61R').text.strip()
        info_data['additional_info2'] = additional_info2
    except:
        info_data['additional_info2'] = None

    return info_data

def crawling_main():
    global naver_res, elem, name_list
    addr_list = []
    phone_list = []
    image_list = []
    nZapA_list = []
    menu_tab_list = []
    reviews_list = []
    photos_list = []
    information_list = []
    
    for e in elem:
        e.click()
        entry_iframe()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 기본 데이터 추가
        try:
            addr_list.append(soup.select('span.LDgIH')[0].text)
        except:
            addr_list.append(float('nan'))
        
        try:
            phone_list.append(soup.select('span.xlx7Q')[0].text)
        except:
            phone_list.append(float('nan'))
        
        try:
            image_list.append(soup.select('img.K0PDV')[0]['src'])
        except:
            image_list.append(float('nan'))
        
        try:
            nZapA_list.append(soup.select('div.nZapA')[0].text)
        except:
            nZapA_list.append(float('nan'))
        
        # 각 탭의 데이터 추출
        tab_names = ['메뉴', '리뷰', '사진', '정보']
        menu_tab, reviews, photos, information = None, None, None, None

        for tab in tab_names:
            tab_soup = get_tab_content(tab)
            if tab == '메뉴' and tab_soup:
                menu_tab = get_menu_content(tab_soup)
            elif tab == '리뷰' and tab_soup:
                reviews = get_reviews_content(tab_soup)
            elif tab == '사진':
                photos = get_photos_content()
            elif tab == '정보' and tab_soup:
                information = get_information_content(tab_soup)

        menu_tab_list.append(menu_tab)
        reviews_list.append(reviews)
        photos_list.append(photos)
        information_list.append(information)
        
        search_iframe()

    ensure_equal_length(addr_list, phone_list, image_list, nZapA_list, menu_tab_list, reviews_list, photos_list, information_list)
    
    naver_temp = pd.DataFrame({
        'title': name_list,
        'address': addr_list,
        'phone': phone_list,
        'image': image_list,
        'nZapA': nZapA_list,
        'menu_tab': menu_tab_list,
        'reviews': reviews_list,
        'photos': photos_list,
        'information': information_list
    })
    naver_res = pd.concat([naver_res, naver_temp], ignore_index=True)

def save_to_json():
    # 데이터를 JSON 파일로 저장
    file_name = f"winon/winon_{current_date}.json"
    
    # DataFrame을 딕셔너리 리스트로 변환
    data = naver_res.to_dict(orient='records')
    
    # JSON 파일로 저장 (들여쓰기 적용)
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"데이터가 {file_name}에 저장되었습니다.")

page_num = 1
while True:
    time.sleep(1.5)
    search_iframe()
    elem, name_list = chk_names()
    if not name_list:
        print("이름 리스트가 비어 있습니다.")
        break
    if last_name == name_list[-1]:
        break
    while True:
        # 자동 스크롤
        action.move_to_element(elem[-1]).perform()
        time.sleep(1)  # 페이지 로드 시간을 조금 더 기다림
        elem, name_list = chk_names()
        if not name_list or last_name == name_list[-1]:
            break
        else:
            last_name = name_list[-1]
    crawling_main()
    # 다음 페이지
    try:
        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[@class="eUTV2" and .//span[@class="place_blind" and text()="다음페이지"]]')))
        next_button.click()
        print(f"{page_num} 페이지 완료")
        page_num += 1
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'place_bluelink')))
    except:
        print("마지막 페이지에 도달했습니다.")
        break

# JSON 파일로 저장
save_to_json()

# 브라우저 종료
driver.quit()
