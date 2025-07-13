from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time
import os 

# 크롬드라이버 실행
driver = webdriver.Chrome() 
driver.get('https://www.airportal.go.kr/airplane/airspace01.do')

# 데이터 리스트 초기화
data_list = []
data_list_child1 = []
data_list_child2 = []
data_list_child3 = []
data_list_child4 = []

# selenium 조작
def select_parent_tag():
    full_html = driver.find_element(By.ID, 'wrap')
    body_html = full_html.find_element(By.ID, 'body')
    main_content = body_html.find_element(By.TAG_NAME, 'main')
    div_container_parent = driver.find_element(By.CSS_SELECTOR, 'div.bx_1440.pb_160')
    div_container = div_container_parent.find_element(By.CSS_SELECTOR, 'div.leisure_content.pb_0')
    right_div = div_container.find_element(By.CSS_SELECTOR, 'div.right')
    return right_div

# 각 카테고리별로 데이터 수집
right_div = select_parent_tag()

'''초경량비행장치 비행공역'''
table_container_1 = right_div.find_element(By.CSS_SELECTOR, 'table.table_list.space')
for num in range(1, 33):
    tr = table_container_1.find_element(By.CSS_SELECTOR, f'tr.p{num}')
    td = tr.find_elements(By.TAG_NAME, 'td')
    name = td[1].text
    pos = td[2].text
    height = td[3].text

    airspace_data = {
        'type': '초경량비행장치 비행공역',
        'name': name,
        'pos': pos,
        'height': height
    }

    data_list_child1.append(airspace_data)

# 드라이버 종료
driver.quit()
driver = webdriver.Chrome() 
driver.get('https://www.airportal.go.kr/airplane/airspace02.do')

'''비행금지구역'''
right_div = select_parent_tag()
table_container_2 = right_div.find_element(By.CSS_SELECTOR, 'table.table_list.space.inhib.milit_mb')
tbody = table_container_2.find_element(By.TAG_NAME, 'tbody')

tr_list = []
for i in range(len(tbody.find_elements(By.TAG_NAME, 'tr'))):
    tr = tbody.find_element(By.CSS_SELECTOR, f'tr:nth-child({i + 1})')
    td_elements = tr.find_elements(By.TAG_NAME, 'td')
    processed_td = [td.text for td in td_elements]
    tr_list.append(processed_td)

for i in range(len(tr_list)-1):
    row_data = tr_list[i+1]
    airspace_data = {
        'type': '비행금지구역',
        'pos': row_data[1],
        'height': row_data[2]
    }
    data_list_child2.append(airspace_data)

# 드라이버 종료
driver.quit()
driver = webdriver.Chrome() 
driver.get('https://www.airportal.go.kr/airplane/airspace03.do')

'''비행제한구역/군훈련공역'''
right_div = select_parent_tag()

# 비행 제한 구역 
table_container_3 = right_div.find_element(By.CSS_SELECTOR, 'table.table_list.space.milit_mb')
tbody = table_container_3.find_element(By.TAG_NAME, 'tbody')

tr_elements = tbody.find_elements(By.TAG_NAME, 'tr')
for tr in tr_elements[1:]:
    td_elements = tr.find_elements(By.TAG_NAME, 'td')
    
    airspace_data = {
        'type': '비행 제한 구역',
        'name': td_elements[0].text,
        'pos': td_elements[1].text,
        'height': td_elements[3].text
    }

    data_list_child3.append(airspace_data)

table_container_4 = right_div.find_element(By.CSS_SELECTOR, 'table.table_list.space.milit_mb')
tbody = table_container_3.find_element(By.TAG_NAME, 'tbody')

tr_elements = tbody.find_elements(By.TAG_NAME, 'tr')
for tr in tr_elements[1:]:
    td_elements = tr.find_elements(By.TAG_NAME, 'td')
    
    airspace_data = {
        'type': '비행 제한 구역',
        'name': td_elements[0].text,
        'pos': td_elements[1].text,
        'height': td_elements[3].text
    }

    data_list_child3.append(airspace_data)

table_container_all = right_div.find_elements(By.CSS_SELECTOR, '.bx_section')
table_container_5 = table_container_all[0]
table_container_6 = table_container_all[1]

tbody1 = table_container_5.find_element(By.TAG_NAME, 'tbody')
tbody2 = table_container_6.find_element(By.TAG_NAME, 'tbody')

tr_elements1 = tbody1.find_elements(By.TAG_NAME, 'tr')
tr_elements2 = tbody2.find_elements(By.TAG_NAME, 'tr')

for tr in tr_elements1[1:]:
    td_elements = tr.find_elements(By.TAG_NAME, 'td')
    
    airspace_data = {
        'type': 'ALERT 구역',
        'name': td_elements[0].text,
        'pos': td_elements[1].text,
        'height': td_elements[3].text
    }

    data_list_child3.append(airspace_data)

for tr in tr_elements2[1:]:
    td_elements = tr.find_elements(By.TAG_NAME, 'td')
    
    airspace_data = {
        'type': '비행 위험 구역',
        'name': td_elements[0].text,
        'pos': td_elements[1].text,
        'height': td_elements[3].text
    }

    data_list_child3.append(airspace_data)

# 드라이버 종료
driver.quit()
driver = webdriver.Chrome() 
driver.get('https://www.airportal.go.kr/airplane/airspace04.do')

'''군작전공역'''
right_div = select_parent_tag()
table_container_7 = right_div.find_element(By.CSS_SELECTOR, 'table.table_list.space.milit_mb')
tbody3 = table_container_7.find_element(By.TAG_NAME, 'tbody')

tr_elements = tbody3.find_elements(By.TAG_NAME, 'tr')
for tr in tr_elements[1:]:
    td_elements = tr.find_elements(By.TAG_NAME, 'td')
    airspace_data = {
        'type': '군작전 공역',
        'name': td_elements[0].text,
        'pos': td_elements[1].text,
        'height': td_elements[2].text
    }
    data_list_child4.append(airspace_data)

# 드라이버 종료
driver.quit()

# 데이터 통합
data_list.extend(data_list_child1)
data_list.extend(data_list_child2)
data_list.extend(data_list_child3)
data_list.extend(data_list_child4)

# 데이터 확인
if not data_list:
    print('데이터 수집되지 않음')
if data_list:
    print('데이터 개수', len(data_list))
    print('데이터 크롤링 완료')

# 데이터프레임 생성 및 저장
df = pd.DataFrame(data_list, columns=['type', 'name', 'pos', 'height'])

# content 폴더가 없으면 생성
content_dir = os.path.join(os.getcwd(), 'content')
if not os.path.exists(content_dir):
    os.makedirs(content_dir)

# 파일 경로
csv_path = os.path.join(content_dir, 'airspace_data.csv')

# CSV 파일로 저장
df.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"[7] CSV 저장: {csv_path}")
