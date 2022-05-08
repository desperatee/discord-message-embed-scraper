import asyncio
import os
import re
import string
import random
from datetime import datetime

from colorama import Fore
from playwright.async_api import async_playwright, ElementHandle, Page

from utils.launch_browser import launch
from utils.logger import Log
from utils.root import get_project_root
from utils.terminal import color_wrap


class Count:
    def __init__(self):
        self.image_num: int = 0
        self.page_num: int = 0

    def incr_image_num(self):
        self.image_num += 1

    def incr_page_num(self):
        self.page_num += 1


log: Log = Log('[DOWNLOADER]')
count: Count = Count()

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


async def download_single_page(page: Page, search_term: str, folder_name: str) -> bool:
    output_path = f'{get_project_root()}/images/{folder_name}'

    # get all images
    # [class^="searchResult-"] [id^="message-accessories"]
    # [id^="search-result-"]
    # [id^="message-accessories-"]
    elements: list[ElementHandle] = await page.query_selector_all('[id^="search-result-"] [id^="message-accessories-"]')
    if not elements:
        log.debug(color_wrap(f'No results found for |{color_wrap(search_term)}| on Page {count.page_num}.',
                             fore_color=Fore.RED))
        return False

    log.debug(color_wrap(f'Found {len(elements)} results on Page {count.page_num}.', fore_color=Fore.LIGHTGREEN_EX))
    # make dir if it's not present
    os.makedirs(output_path, exist_ok=True)

    # download all elements
    for element in elements:
        count.incr_image_num()
        await element.screenshot(type='jpeg', path=output_path + f'/{count.image_num}-{id_generator()}.jpeg', quality=100)
    log.debug(color_wrap(f'Downloaded {len(elements)} images.'))
    return True


async def download_all_search_results(guild_link: str = 'YOUR DISCORD CHANNEL LINK HERE',
                                      search_term: str = 'YOUR SEARCH TERM'):
    # removing special characters from search term
    folder_name: str = re.sub('[^A-Za-z0-9]+', '_', search_term)

    # adds date so you can search the same term multiple times ez.
    _time = f'{datetime.now()}'.split('.')[0]
    folder_name += '____' + re.sub('[^A-Za-z0-9]+', '_', _time)

    async with async_playwright() as pw:
        browser, context, page = await launch(pw, log, headless=True)
        await page.goto(guild_link)
        log.debug(f'Searching |{color_wrap(search_term)}|')
        await page.type('[aria-label="Search"]', search_term)
        await page.press('[aria-label="Search"]', 'Enter')
        count.incr_page_num()  # on page num 1

        while True:
            await page.wait_for_selector('[id^="search-result-"]')
            if not await download_single_page(page, search_term, folder_name):
                # no search results found
                break

            count.incr_page_num()  # incr next page

            # go to next page
            next_btn = await page.query_selector('[rel="next"]')
            if await next_btn.is_disabled():
                break
            await next_btn.click()
            await page.wait_for_load_state('networkidle')

        log.info(f'Downloaded {count.image_num} images total.')


if __name__ == "__main__":
    asyncio.run(download_all_search_results())