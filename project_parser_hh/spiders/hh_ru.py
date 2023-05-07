import scrapy
from scrapy.http import HtmlResponse
import sys
import re

sys.path.append('C:\\Users\\Админ\\Desktop\\parsing\\parsing-scraping')
from project_parser_hh.items import ProjectParserHhItem, clean_salary

class HhRuSpider(scrapy.Spider):

    name = 'hh_ru'
    allowed_domains = ['hh.ru']
    start_urls = [
        'https://spb.hh.ru/search/vacancy?area=76&search_field=name&search_field=company_name&search_field=description&text=python&no_magic=true&L_save_area=true&items_on_page=20',
    ]

    def parse(self, response: HtmlResponse):
        next_page = response.xpath("//a[@data-qa='pager-next']/@href").get()

        if next_page:
            yield response.follow(next_page, callback=self.parse)

        urls_vacancies = response.xpath("//div[@class='serp-item']//a[@class='serp-item__title']/@href").getall()
        #urls_vacancies = response.xpath("//div[@class='serp-item']//a[@data-qa='vacancy-serp__vacancy-title']/@href").getall()
        for url_vacancy in urls_vacancies:
            yield response.follow(url_vacancy, callback=self.vacancy_parse)

    def vacancy_parse(self, response: HtmlResponse):
        vacancy_name = response.css("h1::text").get()
        vacancy_salary = response.xpath("//div[@data-qa='vacancy-salary']//text()").getall()
        vacancy_url = response.url

        salary_min, salary_max = clean_salary(vacancy_salary)

        item = ProjectParserHhItem()
        item['name'] = vacancy_name
        item['salary_min'] = salary_min #int(salary_min) if salary_min.isdigit() else salary_min
        item['salary_max'] = salary_max #int(salary_max) if salary_max.isdigit() else salary_max
        item['url'] = vacancy_url

        yield item