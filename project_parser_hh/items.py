# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
from scrapy.loader.processors import MapCompose


def clean_salary(vacancy_salary):
    salary_min, salary_max = None, None
    _from = None
    for i in range(len(vacancy_salary)):
        if 'от' in vacancy_salary[i]:
              vacancy_salary[i] = vacancy_salary[i].replace(' ', '')
        elif 'до' in vacancy_salary[i] and not 'до вычета налогов' in vacancy_salary[i]:
              vacancy_salary[i] = vacancy_salary[i].replace(' ', '') 
        elif '\xa0' in vacancy_salary[i]:
              vacancy_salary[i] = vacancy_salary[i].replace('\xa0', '')
        elif 'до вычета налогов' in vacancy_salary[i]:
              _from = vacancy_salary[i]
    salary_raw = [s for s in vacancy_salary if s.isdigit()]
    salary_min, salary_max = None, None
    if 'до' in vacancy_salary and 'от' not in vacancy_salary:
          salary_min, salary_max = None, salary_raw[0]
    elif 'от' in vacancy_salary and 'до' and 'до вычета налогов' not in vacancy_salary:
          salary_min, salary_max = salary_raw[0], None
    elif 'от' in vacancy_salary and 'до' in vacancy_salary:
          salary_min, salary_max = salary_raw[0], salary_raw[1]
    elif len(salary_raw) > 1:
          salary_min, salary_max = salary_raw[0], salary_raw[1]
    elif 'от' in vacancy_salary and 'до вычета налогов' in vacancy_salary:
         salary_min, salary_max = salary_raw[0], _from
    
    return int(salary_min) if salary_min is not None and not 'до вычета налогов' else salary_min, \
           int(salary_max) if salary_max is not None and not 'до вычета налогов' else salary_max




class ProjectParserHhItem(Item):
    name = Field()
    salary_min = Field(input_processor=MapCompose(clean_salary))
    salary_max = Field(input_processor=MapCompose(clean_salary))
    url = Field()
    _id = Field()