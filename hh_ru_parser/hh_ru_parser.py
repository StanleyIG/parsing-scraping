import requests
from bs4 import BeautifulSoup as bs
import re
import json
from datetime import datetime
from pymongo import MongoClient


class HHruParser:
    def __init__(self, vacancy, max_page):
        self.vacancy = vacancy
        self.max_page = max_page
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.142 Safari/537.36'
        }
        self.url = f'https://kazan.hh.ru/search/vacancy?no_magic=true&L_save_area=true&text={self.vacancy}&excluded_text=&area=88&salary=&' \
              f'currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=20'

    """получает статус код, url, заголовок"""
    def get_status_code(self):
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:
            return True
        return False


    """получает список вакансий на страницу"""

    def get_vacansy(content):
        soup = bs(content.content, 'html.parser')
        block = soup.find_all('div', {'class': 'vacancy-serp-item-body__main-info'})
        vacancies = []
        # salary_min, salary_max = None, None
        for i in block:
            if i.findChildren('span', {'class': 'bloko-header-section-3'}):
                sal_raw = i.findChildren('span', {'class': 'bloko-header-section-3'})[0].text.replace('\u202f', '')
                salary = re.findall('\d{1,6}', sal_raw)
                if 'до' in sal_raw and 'от' not in sal_raw:
                    salary_min, salary_max = None, salary[0]
                elif 'от' in sal_raw and 'до' not in sal_raw:
                    salary_min, salary_max = salary[0], None
                elif 'от' in sal_raw and 'до' in sal_raw:
                    salary_min, salary_max = salary[0], salary[1]
                elif len(salary) > 1:
                    salary_min, salary_max = salary[0], salary[1]
                currency = re.findall('[а-я]{3}|[A-Z]{3}', sal_raw)[0]
            else:
                salary_min, salary_max = None, None
                currency = None

            vacancy_text = i.findChildren('a', {'class': 'serp-item__title'})[0].text
            vacancy_href = i.findChildren('a', {'class': 'serp-item__title'})[0].get('href')
            dct_block = {'name': vacancy_text,
                         'salary_min': int(salary_min) if salary_min is not None else salary_min,
                         'salary_max': int(salary_max) if salary_max is not None else salary_max,
                         'currency': currency,
                         'link': vacancy_href}

            vacancies.append(dct_block)
        return vacancies


    """получает следующую страницу"""
    def get_next_page(self, content):
        soup = bs(content.content, 'html.parser')
        pages_block = soup.find('div', {'class': 'pager'})
        pages = pages_block.findChildren('a', {'class': 'bloko-button'}, recursive=False)
        if pages:
            next_page = f"https://kazan.hh.ru/" \
                        f"{pages_block.findChildren('a', {'class': 'bloko-button'}, recursive=False)[0].get('href')}"
            return next_page
        return None

    """получает все вакансии"""
    def get_all_vacancies(self):
        status = self.get_status_code()
        if status:
            response = requests.get(self.url, headers=self.headers)
            results = []
            for i in range(self.max_page):
                next_page = self.get_next_page(response)
                if next_page:
                    results.append(self.get_vacansy(response))
                    response = requests.get(next_page, headers=self.headers)
            all_vacancies = [obj for result in results for obj in result]
            parser_object = {'vacancies': all_vacancies, 'status_ok': True}
            return parser_object
        return {'vacancies': None, 'status_ok': False}

    """записывает вакансии в json"""
    def write_json(self):
        FILENAME = 'hhru.json'
        with open(FILENAME, 'w', encoding='utf-8') as file:
            json.dump(self.get_all_vacancies(), file, ensure_ascii=False, indent=4)

    """добавляет только новые вакансии, а также дату добавления вакансии в MongoDB при вызове функции"""
    def add_to_mongodb(self):
        new_vacancies = self.get_all_vacancies()['vacancies']
        client = MongoClient('mongodb://localhost:27017/')
        db = client["mydatabase"]
        vacancies = db["vacancies"]
        for vacancy in new_vacancies:
            if vacancies.find_one({"link": vacancy["link"]}) is None:
                vacancy["date_added"] = datetime.now().strftime("%d.%m.%Y")
                vacancies.insert_one(vacancy)
        return vacancies


parser = HHruParser('python', 5)
vacancies = parser.get_all_vacancies()['vacancies']
mongodb = parser.add_to_mongodb()

"""посмотреть все вакансии"""
for vacansy in mongodb.find():
    print(vacansy)

"""посмотреть конкретную"""
# print(mongodb.find_one({'link': vacancies[5]['link']}))
