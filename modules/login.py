import asyncio
from asyncio import sleep
from json import dump

from colorama import Fore
from playwright.async_api import async_playwright, Route, Response

from utils.launch_browser import launch
from utils.logger import Log
from utils.root import get_project_root
from utils.terminal import color_wrap


LOGGED_IN: bool = False


log: Log = Log('[D LOGIN]')


async def sniff_login(route: Route):
    await route.continue_()  # continue all requests as is

    if 'https://discord.com/api/v9/auth/login' not in route.request.url:
        return

    # parse login req
    resp: Response = await route.request.response()

    if resp.status != 200:  # login not successful, captcha or bad login, allow user to continue
        return

    # write acc info to file
    _json = await resp.json()
    with open(f'{get_project_root()}/program_data/acc_info.json', 'w') as file:
        dump(_json, file, indent=4)

    # set logged in state
    global LOGGED_IN
    LOGGED_IN = True


async def wait_for_login():
    while not LOGGED_IN:
        await sleep(0.1)


async def login():
    """
    Just login with email and password. QR code not supported.
        (QR stuff is WS, too much effort for something that will only happen once.)
    :return:
    """
    async with async_playwright() as pw:
        browser, context, page = await launch(pw, log, headless=False)
        await page.route('**/**', sniff_login)
        await page.goto('https://discord.com/login', wait_until='networkidle')

        # wait for user login
        await wait_for_login()

        # save browser state json
        browser_state: dict = await context.storage_state()
        with open(f'{get_project_root()}/program_data/browser_state.json', 'w') as file:
            dump(browser_state, file, indent=4)

        log.debug(color_wrap('Login detected! Closing browser in 3 seconds.', fore_color=Fore.LIGHTGREEN_EX))
        await sleep(3)

    log.debug(color_wrap('Closed Browser.'))


if __name__ == "__main__":
    asyncio.run(login())
