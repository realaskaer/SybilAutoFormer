import random
import traceback

import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from termcolor import cprint

from settings import SLEEP_FOR_ACCOUNT, ADS_ACCOUNT_CODE, SLEEP_AFTER_SUBMITTING, SHUFFLE_WALLETS, WALLETS_TO_WORK

WALLET_ADDRESS_SELLECTOR = '#mG61Hd > div.RH5hzf.RLS9Fe > div > div.o3Dpx > div:nth-child(1) > div > div > div.AgroKb > div > div.RpC4Ne.oJeWuf > div.Pc9Gce.Wic03c > textarea'
PROOF_SELLECTOR = '#mG61Hd > div.RH5hzf.RLS9Fe > div > div.o3Dpx > div:nth-child(2) > div > div > div.AgroKb > div > div.RpC4Ne.oJeWuf > div.Pc9Gce.Wic03c > textarea'
ATTEST_PROOF_SELLECTOR = '#mG61Hd > div.RH5hzf.RLS9Fe > div > div.o3Dpx > div:nth-child(3) > div > div > div.AgroKb > div > div.aCsJod.oJeWuf > div > div.Xb9hP > input'
CONTACT_SELLECTOR = '#mG61Hd > div.RH5hzf.RLS9Fe > div > div.o3Dpx > div:nth-child(4) > div > div > div.AgroKb > div > div.aCsJod.oJeWuf > div > div.Xb9hP > input'
SEND_SELLECTOR = '#mG61Hd > div.RH5hzf.RLS9Fe > div > div.ThHDze > div.DE3NNc.CekdCb > div.lRwqcd > div'

TITLE = """
 ______     __  __     ______     __     __         ______     __  __     ______   ______     ______   ______     ______     __    __     ______     ______    
/\  ___\   /\ \_\ \   /\  == \   /\ \   /\ \       /\  __ \   /\ \/\ \   /\__  _\ /\  __ \   /\  ___\ /\  __ \   /\  == \   /\ "-./  \   /\  ___\   /\  == \   
\ \___  \  \ \____ \  \ \  __<   \ \ \  \ \ \____  \ \  __ \  \ \ \_\ \  \/_/\ \/ \ \ \/\ \  \ \  __\ \ \ \/\ \  \ \  __<   \ \ \-./\ \  \ \  __\   \ \  __<   
 \/\_____\  \/\_____\  \ \_____\  \ \_\  \ \_____\  \ \_\ \_\  \ \_____\    \ \_\  \ \_____\  \ \_\    \ \_____\  \ \_\ \_\  \ \_\ \ \_\  \ \_____\  \ \_\ \_\ 
  \/_____/   \/_____/   \/_____/   \/_/   \/_____/   \/_/\/_/   \/_____/     \/_/   \/_____/   \/_/     \/_____/   \/_/ /_/   \/_/  \/_/   \/_____/   \/_/ /_/ 
"""

def get_data_for_forms():
    forms_data = get_data_for_forms_util()

    if WALLETS_TO_WORK == 0:
        return forms_data

    elif isinstance(WALLETS_TO_WORK, int):
        return forms_data[WALLETS_TO_WORK]

    elif isinstance(WALLETS_TO_WORK, tuple):
        forms_data = [forms_data[i - 1] for i in WALLETS_TO_WORK]
        return forms_data

    elif isinstance(WALLETS_TO_WORK, list):
        range_count = range(WALLETS_TO_WORK[0], WALLETS_TO_WORK[1] + 1)
        forms_data = [forms_data[i - 1] for i in range_count]
        return forms_data
    else:
        accounts_data = []

    if SHUFFLE_WALLETS:
        random.shuffle(accounts_data)

    return accounts_data


def get_signature_and_address(private_key):
    from web3 import AsyncWeb3, AsyncHTTPProvider
    from eth_account.messages import encode_defunct

    rpc = 'https://rpc.ankr.com/eth'
    request_kwargs = {"verify_ssl": False}
    w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs=request_kwargs))
    address = AsyncWeb3.to_checksum_address(w3.eth.account.from_key(private_key).address)

    msg = 'RFI: I confirm that I own this wallet.'
    text_hex = "0x" + msg.encode('utf-8').hex()
    text_encoded = encode_defunct(hexstr=text_hex)
    signature = w3.eth.account.sign_message(
        text_encoded,
        private_key=private_key
    ).signature

    return w3.to_hex(signature), address


def get_data_for_forms_util():
    with open('private_keys.txt') as file:
        private_keys = file.readlines()

    with open('proofs.txt') as file:
        proofs = file.readlines()

    with open('contacts.txt') as file:
        contacts = file.readlines()

    if len(private_keys) != len(proofs) != len(contacts):
        cprint(f"Ты уверен, что количество адресов, пруфов и контактов одинаковое?", 'red')
        raise RuntimeError('Проблемы в считывании данных')

    cprint(f"Получил данные для аккаунтов", 'light_green')

    full_data = []
    for i in range(len(private_keys)):
        full_data.append([
            private_keys[i],
            proofs[i],
            f"@{contacts[i]}",
        ])

    return full_data


def main():
    try:
        open_url = "http://local.adspower.net:50325/api/v1/browser/start?user_id=" + ADS_ACCOUNT_CODE

        resp = requests.get(open_url).json()
        time.sleep(1)

        if resp['code'] != 0:
            cprint(f"Не смог запустить браузер по причине {resp['msg']}", 'light_red')
            return

        forms_data = get_data_for_forms()
        chrome_driver = Service(resp["data"]["webdriver"])
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", resp["data"]["ws"]["selenium"])
        driver = webdriver.Chrome(service=chrome_driver, options=chrome_options)

        cprint(f"Успешно открыл браузер для отправки форм", 'light_green')

        driver.get('https://docs.google.com/forms/d/e/1FAIpQLSfdnxQvdt8QTjGODVCSnckk_f1dv_IFeaeUVXRfF__euyIZbw/viewform')

        for index, form_data in enumerate(forms_data, 1):
            cprint(f"[{index}/{len(forms_data)}] | Начинаю работу с аккаунтом #{index}")
            private_key, proof, contact = form_data
            attest_hash, wallet_address = get_signature_and_address(private_key)
            time.sleep(random.randint(*SLEEP_FOR_ACCOUNT))
            try:
                address_tab = driver.find_element(
                    By.CSS_SELECTOR,
                    WALLET_ADDRESS_SELLECTOR
                )
                address_tab.send_keys(wallet_address)

                time.sleep(0.1)

                proof_tab = driver.find_element(
                    By.CSS_SELECTOR,
                    PROOF_SELLECTOR
                )
                proof_tab.send_keys(proof)

                time.sleep(0.1)

                attest_proof_tab = driver.find_element(
                    By.CSS_SELECTOR,
                    ATTEST_PROOF_SELLECTOR
                )
                attest_proof_tab.send_keys(attest_hash)

                time.sleep(0.1)

                contact_tab = driver.find_element(
                    By.CSS_SELECTOR,
                    CONTACT_SELLECTOR
                )
                contact_tab.send_keys(contact)

                driver.find_element(
                    By.CSS_SELECTOR,
                    SEND_SELLECTOR
                ).click()

                time.sleep(2)
            except Exception as error:
                traceback.print_exc()
                cprint(f"[{index}/{len(forms_data)}] | Не смог что-то найти на форме{str(error)[:0]}", 'light_red')
                driver.refresh()
                time.sleep(2)
                break

            cprint(f"[{index}/{len(forms_data)}] | Успешно отправил форму для аккаунта #{index}", 'light_green')
            driver.refresh()

            sleep_time = random.randint(*SLEEP_AFTER_SUBMITTING)
            cprint(f"[{index}/{len(forms_data)}] | Сплю ({sleep_time} секунд) после отправки формы #{index}", 'light_yellow')
            time.sleep(sleep_time)

        time.sleep(1)

    except Exception as ex:
        cprint(f'{ex}', 'red')
        return


if __name__ == "__main__":
    cprint(TITLE, 'light_green')
    cprint(f'\n❤️ My channel for latest updates: https://t.me/askaer\n', 'light_cyan', attrs=["blink"])

    cprint(f"Начинаю работу с формами")
    main()
    cprint(f"Закончил работу с формами", 'light_green')

