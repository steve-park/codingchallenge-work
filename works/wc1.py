import requests
from urllib import parse
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import asyncio
import random
import itertools
import time
from datetime import datetime
from urllib.error import HTTPError


class NewsScrapper:
    def __init__(self, keyword, maxpages=50, debug_mode: bool = True):
        """네이버 뉴스 스크래퍼 생성자 - 초기 설정

        Args:
            keyword (str): 검색어
            maxpages (int, optional): 최대 기사 검색 페이지 수. Defaults to 20.
            debug_mode (bool, optional): 디버그 로그 출력 여부. Defaults to True.
        """
        self.baseurl = f'https://search.naver.com/search.naver?where=news&query={parse.quote(keyword)}'
        self.keyword = keyword
        self.current = 0
        self.maximum = maxpages if maxpages < 50 else 50
        self.debug_mode = debug_mode
        self.start = None
        self.end = None

        random.seed(777)

    async def __scrap_page(self, page, header):
        """개별 페이지 스크래핑 비동기 처리 함수

        Args:
            page (int): 대상 페이지 No
            header (dict): request header

        Raises:
            Exception: response code가 200 이 아닌 경우 발생

        Returns:
            dict: 해당 페이지의 기사 장보를 dictionary 형태로 반환 - 최대 10개
        """
        baseurl = f'{self.baseurl}&start={(page - 1) * 10 + 1}'

        await asyncio.sleep(random.randint(1, 10))

        response = requests.get(self.baseurl, headers=header)
        self.debug_mode and print(
            f'\t\t[scrap_page] {page} - {response.status_code} / {baseurl}')

        if not response.ok:
            raise HTTPError(baseurl, response.status_code)

        soup = BeautifulSoup(response.text, 'html.parser')
        page_result = []

        for item in soup.select('div.news_area'):
            article = {}
            article['title'] = item.select_one('a.news_tit')['title']
            article['summary'] = item.select_one(
                'a.api_txt_lines.dsc_txt_wrap').text
            article['press'] = item.select_one(
                'div.news_info > div.info_group > a.info.press').text
            article['link'] = item.select_one('a.news_tit')['href']

            page_result.append(article)

        return page_result

    async def __scrap_main(self, max_scrapper=20):
        """개별페이지 스크래핑 비동기 처리 함수 호출 및 결과 취합

        Args:
            max_scrapper (int, optional): async 처리 page scrapper 최대 수. Defaults to 10.

        Returns:
            list: news item dictionary의 list
        """
        header = {
            'User-Agent': UserAgent(verify_ssl=False).chrome
        }

        main_result = []

        while self.current < self.maximum:
            start = self.current
            end = self.maximum if self.current + \
                max_scrapper > self.maximum else self.current + max_scrapper

            self.debug_mode and print(
                f'\t[scrap_main] start: {start + 1} - end: {end}')
            scrappers = []

            for page in range(start + 1, end + 1):
                scrappers.append(asyncio.create_task(
                    self.__scrap_page(page, header)))

            self.current = end

            for page_result in await asyncio.gather(*scrappers):
                # main_result 에 누적하고 있으나, memory 사용률을 고려하여 database 등 결과를 직접 저장 필요
                main_result.extend(page_result)

            self.debug_mode and print(
                f'\t[scrap_main] comulative results: {len(main_result)}')

        return main_result

    def gather(self):
        """main_scrap 함수 호출자

        Returns:
            dictionary: 네이버 뉴스 스크래핑 dictionary의 list
        """
        start = time.perf_counter()
        self.start = datetime.now()

        news = asyncio.run(self.__scrap_main())

        self.debug_mode and print(
            f'\t[gather] elipsed time: {time.perf_counter() - start:0.2f} seconds')
        self.end = datetime.now()

        return news

    def info(self):
        """환경 설정 확인용 함수
        """
        info = {
            'baseurl': self.baseurl,
            'keyword': self.keyword,
            'current': self.current,
            'maximum': self.maximum,
            'start': self.start,
            'end': self.end
        }

        if self.debug_mode:
            print(f'[newsscrapper-info]')
            for key, value in info.items():
                print(f'\t{key} : {value}')

        return info


if __name__ == '__main__':
    scrapper = NewsScrapper('python', 3, True)
    scrapper.gather()
    scrapper.info()
