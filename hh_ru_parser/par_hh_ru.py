from datetime import datetime
from bs4 import BeautifulSoup as bs
import requests
from pprint import pprint
import re
import json
from pymongo import MongoClient


"""получает статус код, url, заголовок"""
def get_status_code(vacancy):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/75.0.3770.142 Safari/537.36'
    }
    url = f'https://kazan.hh.ru/search/vacancy?no_magic=true&L_save_area=true&text={vacancy}&excluded_text=&area=88&salary=&' \
          f'currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=20'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True, headers, url
    return None


"""получает список вакансий на страницу"""
def get_vacansy(content):
    soup = bs(content.content, 'html.parser')
    block = soup.find_all('div', {'class': 'vacancy-serp-item-body__main-info'})
    dct_block = {}
    vacancies = []
    for i in range(len(block)):
        if block[i].findChildren('span', {'class': 'bloko-header-section-3'}):
            salary = re.findall('\d{1,6}',
                                block[i].findChildren('span', {'class': 'bloko-header-section-3'})
                                [0].text.replace('\u202f', ''))
            currency = re.findall('[а-я]{3}|[A-Z]{3}',
                                  block[i].findChildren('span', {'class': 'bloko-header-section-3'})
                                  [0].text.replace('\u202f', ''))
        else:
            salary = None
            currency = None
        vacancy_text = block[i].findChildren('a', {'class': 'serp-item__title'})[0].text
        vacancy_href = block[i].findChildren('a', {'class': 'serp-item__title'})[0].get('href')
        dct_block = {'name': vacancy_text,
                     'salary_min': salary[0] if salary else None,
                     'salary_max': salary[1] if salary and len(salary) > 1 else None,
                     'currency': currency[0] if currency else None,
                     'link': vacancy_href}

        vacancies.append(dct_block)
    return vacancies


"""получает следующую страницу"""
def get_next_page(content):
        soup = bs(content.content, 'html.parser')
        pages_block = soup.find('div', {'class': 'pager'})
        pages = pages_block.find_all('a', {'class': 'bloko-button'}, recursive=False)
        if pages:
            next_page = f"https://kazan.hh.ru{pages_block.findChildren('a', {'class': 'bloko-button'}, recursive=False)[0].get('href')}"
            return next_page
        return None

def get_count_pages():
    status = get_status_code(vacancy)
    if status:
        status_ok, headers, url = status
        response = requests.get(url, headers=headers)
        res = [url]
        while True:
            soup = bs(response.content, 'html.parser')
            pages_block = soup.find('div', {'class': 'pager'})
            pages = pages_block.find_all('a', {'class': 'bloko-button'}, recursive=False)
            if pages:
                next_page = f"https://kazan.hh.ru{pages_block.findChildren('a', {'class': 'bloko-button'}, recursive=False)[0].get('href')}"
                res.append(next_page)
                response = requests.get(next_page, headers=headers)
            else:
                break
        return res




"""получает все вакансии"""
def get_all_vacancies(vacancy, max_page):
    status = get_status_code(vacancy)
    if status:
        status_ok, headers, url = status
        response = requests.get(url, headers=headers)
        results = []
        for i in range(max_page):
            next_page = get_next_page(response)
            if next_page:
                results.append(get_vacansy(response))
                response = requests.get(next_page, headers=headers)
        all_vacancies = [obj for result in results for obj in result]
        parser_object = {'vacancies': all_vacancies, 'status_ok': status_ok}
        return parser_object
    return {'vacancies': None, 'status_ok': False}


"""записывает вакансии в json"""
def write_json():
    FILENAME = 'hhru.json'
    with open(FILENAME, 'w', encoding='utf-8') as file:
        json.dump(get_all_vacancies('python', 5), file, ensure_ascii=False, indent=4)


"""добавляет только новые вакансии, а также дату добавления вакансии в MongoDB при вызове функции"""
def adt_to_mongodb(new_vacancies):
    client = MongoClient('mongodb://localhost:27017/')
    db = client["mydatabase"]
    vacancies = db["vacancies"]
    for vacancy in new_vacancies:
        if vacancies.find_one({"link": vacancy["link"]}) is None:
            vacancy["date_added"] = datetime.now().strftime("%d.%m.%Y")
            vacancies.insert_one(vacancy)
    return vacancies


#vacancies = get_all_vacancies('python', 5)['vacancies']
#print(vacancies)
# write_json()
#mongodb = adt_to_mongodb(vacancies)
"""посмотреть все вакансии"""
#for vacansy in mongodb.find():
#    print(vacansy)

"""посмотреть конкретную"""
#print(mongodb.find_one({'link': vacancies[5]['link']}))


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/75.0.3770.142 Safari/537.36'
}
vacancy = 'python'
url = f'https://kazan.hh.ru/search/vacancy?no_magic=true&L_save_area=true&text={vacancy}&excluded_text=&area=88&salary=&' \
      f'currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=20'

pprint(get_count_pages())


