import os
from json import load

from playwright.async_api import Playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async

from utils.logger import Log
from utils.root import get_project_root
from utils.terminal import color_wrap


os.makedirs(f'{get_project_root()}/program_data/', exist_ok=True)


async def launch(pw: Playwright, log: Log, headless: bool) -> tuple[Browser, BrowserContext, Page]:
    browser: Browser = await pw.chromium.launch(
        headless=headless,
        timeout=10_000  # long timeout
    )
    # load storage state if it's present
    storage_state: dict | None = None

    if 'browser_state.json' in os.listdir(f'{get_project_root()}/program_data/'):
        with open(f'{get_project_root()}/program_data/browser_state.json') as file:
            storage_state = load(file)

    context: BrowserContext = await browser.new_context(
        storage_state=storage_state
    )

    if context.pages:
        page: Page = context.pages[0]
    else:
        page: Page = await context.new_page()

    await stealth_async(page)  # just getting rid of that annoying popup
    log.debug(color_wrap('Launched browser.'))

    return browser, context, page
