import asyncio
import cloudscraper
import json
import time
from loguru import logger
import requests
from colorama import Fore, Style, init

init(autoreset=True)

print(f"""
{Fore.CYAN + Style.BRIGHT}

 ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄   ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ 
█       █       █   ▄  █ █  █ █  █       █       █       █
█  ▄▄▄▄▄█       █  █ █ █ █  █▄█  █    ▄  █▄     ▄█   ▄   █
█ █▄▄▄▄▄█     ▄▄█   █▄▄█▄█       █   █▄█ █ █   █ █  █ █  █
█▄▄▄▄▄  █    █  █    ▄▄  █▄     ▄█    ▄▄▄█ █   █ █  █▄█  █
 ▄▄▄▄▄█ █    █▄▄█   █  █ █ █   █ █   █     █   █ █       █
█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄█  █▄█ █▄▄▄█ █▄▄▄█     █▄▄▄█ █▄▄▄▄▄▄▄█
                 NODEPAY SCRIPT
{Style.RESET_ALL}
{Fore.YELLOW}╔═════════════════════════════════════════════════════════════════╗
║  {Fore.GREEN}• YouTube Channel :  https://www.youtube.com/@SCRYPTO-Channel  {Fore.YELLOW}║
║  {Fore.GREEN}• Telegram Channel : https://t.me/SCRYPTO_Newss                {Fore.YELLOW}║
║  {Fore.GREEN}• Join us now for more scripts !!                              {Fore.YELLOW}║
╚═════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)

def truncate_token(token):
    return f"{token[:5]}--{token[-5:]}"

logger.remove()
logger.add(lambda msg: print(msg, end=''), format="{message}", level="INFO")

PING_INTERVAL = 15
RETRIES = 10

DOMAIN_API = {
    "SESSION": "http://api.nodepay.ai/api/auth/session",
    "PING": [
        "https://nw.nodepay.org/api/network/ping"
    ]
}

CONNECTION_STATES = {
    "CONNECTED": 1,
    "DISCONNECTED": 2,
    "NONE_CONNECTION": 3
}

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

class AccountData:
    def __init__(self, token, index):
        self.token = token
        self.index = index
        self.status_connect = CONNECTION_STATES["NONE_CONNECTION"]
        self.account_info = {}
        self.retries = 0
        self.last_ping_status = 'Waiting...'
        self.browser_ids = [
            {
                'ping_count': 0,
                'successful_pings': 0,
                'score': 0,
                'start_time': time.time(),
                'last_ping_time': None
            }
        ]

    def reset(self):
        self.status_connect = CONNECTION_STATES["NONE_CONNECTION"]
        self.account_info = {}
        self.retries = 3

async def retrieve_tokens():
    try:
        with open('user.txt', 'r') as file:
            tokens = file.read().splitlines()
        return tokens
    except Exception as e:
        logger.error(f"Failed to load tokens: {e}")
        raise SystemExit("Exiting due to failure in loading tokens")

async def execute_request(url, data, account):
    headers = {
        "Authorization": f"Bearer {account.token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://app.nodepay.ai/",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "chrome-extension://lgmpfmgeabnnlemejacfljbmonaomfmm",
        "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cors-site"
    }

    try:
        response = scraper.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"{Fore.RED}Error during API call for token {truncate_token(account.token)}: {e}{Style.RESET_ALL}")
        raise ValueError(f"Failed API call to {url}")

    return response.json()

async def start_ping(account):
    try:
        logger.info(f"{Fore.CYAN}[{time.strftime('%H:%M:%S')}][{account.index}]{Style.RESET_ALL} Starting ping for token {Fore.CYAN}{truncate_token(account.token)}{Style.RESET_ALL}")
        while True:
            try:
                await asyncio.sleep(PING_INTERVAL)
                await perform_ping(account)
            except Exception as e:
                logger.error(f"{Fore.RED}Ping failed for token {truncate_token(account.token)}: {e}{Style.RESET_ALL}")
    except asyncio.CancelledError:
        logger.info(f"Ping task for token {truncate_token(account.token)} was cancelled")
    except Exception as e:
        logger.error(f"Error in start_ping for token {truncate_token(account.token)}: {e}")

async def perform_ping(account):
    current_time = time.time()
    logger.info(f"{Fore.CYAN}[{time.strftime('%H:%M:%S')}][{account.index}]{Style.RESET_ALL} Attempting to send ping for token {Fore.CYAN}{truncate_token(account.token)}{Style.RESET_ALL}")

    if account.browser_ids[0]['last_ping_time'] and (current_time - account.browser_ids[0]['last_ping_time']) < PING_INTERVAL:
        logger.info(f"Woah there! Not enough time has elapsed.")
        return

    account.browser_ids[0]['last_ping_time'] = current_time

    for url in DOMAIN_API["PING"]:
        try:
            data = {
                "id": account.account_info.get("uid"),
                "browser_id": account.browser_ids[0],
                "timestamp": int(time.time())
            }
            response = await execute_request(url, data, account)
            ping_result, network_quality = "success" if response["code"] == 0 else "failed", response.get("data", {}).get("ip_score", "N/A")

            if ping_result == "success":
                logger.info(f"{Fore.CYAN}[{time.strftime('%H:%M:%S')}][{account.index}]{Style.RESET_ALL} Ping {Fore.GREEN}{ping_result}{Style.RESET_ALL} from {Fore.CYAN}{truncate_token(account.token)}{Style.RESET_ALL}, Network Quality: {Fore.GREEN}{network_quality}{Style.RESET_ALL}")
                account.browser_ids[0]['successful_pings'] += 1
                return
            else:
                logger.warning(f"{Fore.RED}Ping {ping_result}{Style.RESET_ALL} for token {truncate_token(account.token)}")

        except Exception as e:
            logger.error(f"{Fore.RED}Ping failed for token {truncate_token(account.token)}: {e}{Style.RESET_ALL}")

async def collect_profile_info(account):
    try:
        response = await execute_request(DOMAIN_API["SESSION"], {}, account)
        if response.get("code") == 0:
            account.account_info = response["data"]
            if account.account_info.get("uid"):
                await start_ping(account)
        else:
            logger.warning(f"Session failed for token {truncate_token(account.token)}")
    except Exception as e:
        logger.error(f"Failed to collect profile info for token {truncate_token(account.token)}: {e}")

async def process_account(token, index):
    """
    Process a single account: Initialize proxies and start asyncio event loop for this account.
    """
    account = AccountData(token, index)
    await collect_profile_info(account)

async def main():
    tokens = await retrieve_tokens()

    tasks = []
    for index, token in enumerate(tokens, start=1):
        tasks.append(process_account(token, index))

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("All tasks have been cancelled.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Program terminated by user.")
        tasks = asyncio.all_tasks()
        for task in tasks:
            task.cancel()
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        asyncio.get_event_loop().close()
