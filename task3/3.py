import csv
import time
from typing import Dict, List

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    TimeoutException,
)
from selenium.webdriver.common.by import By as by
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait as w

BASE_URL = "http://quotes.toscrape.com"
LOGIN_URL = f"{BASE_URL}/login"
USERNAME = "admin"
PASSWORD = "admin"
OUTPUT_FILE = "output.csv"
CHROME_OPTIONS = ["--headless=new", "--window-size=1920,1080"]


def create_webdriver() -> webdriver.Chrome:
    """
    Создает экземпляр браузера Chrome.
    """

    opts = webdriver.ChromeOptions()
    for opt in CHROME_OPTIONS:
        opts.add_argument(opt)

    try:
        drv = webdriver.Chrome(options=opts)
        drv.implicitly_wait(2)
        return drv
    except WebDriverException as e:
        raise RuntimeError(f"Ошибка при инициализации WebDriver: {e}")


def login_to_website(
    drv: webdriver.Chrome,
    l_url: str = LOGIN_URL,
    usr: str = USERNAME,
    pwd: str = PASSWORD,
) -> None:
    """
    Выполняет авторизацию на сайте.

    Parameters
    ----------
    drv : webdriver.Chrome
        Экземпляр веб-драйвера.
    l_url : str
        URL страницы авторизации.
    usr : str
        Логин пользователя.
    pwd : str
        Пароль пользователя.
    """

    print("Переход на страницу авторизации...")
    drv.get(l_url)

    try:
        drv.find_element(by.ID, "username").send_keys(usr)
        drv.find_element(by.ID, "password").send_keys(pwd)
        drv.find_element(by.CSS_SELECTOR, "input[type='submit']").click()

        w(drv, 10).until(
            ec.presence_of_element_located((by.CSS_SELECTOR, "a[href='/logout']"))
        )
        print("Авторизация прошла успешно.")
    except (NoSuchElementException, TimeoutException) as e:
        raise RuntimeError(f"Ошибка авторизации: {e}")


def parse_quotes_from_page(drv: webdriver.Chrome) -> List[Dict[str, str]]:
    """
    Собирает данные цитат на текущей странице.

    Parameters
    ----------
    drv : webdriver.Chrome
        Экземпляр веб-драйвера.
    """

    res = []
    blocks = drv.find_elements(by.CLASS_NAME, "quote")

    for b in blocks:
        try:
            txt = b.find_element(by.CLASS_NAME, "text").text
            auth = b.find_element(by.CLASS_NAME, "author").text

            auth_a = b.find_element(by.XPATH, ".//span/a")
            a_link = auth_a.get_attribute("href") or ""

            t_elems = b.find_elements(by.CLASS_NAME, "tag")
            t_str = ";".join([t.text for t in t_elems])

            res.append(
                {"text": txt, "author": auth, "tags": t_str, "author_link": a_link}
            )
        except NoSuchElementException as e:
            print(f"Ошибка при парсинге отдельной цитаты: {e}")

    return res


def go_to_next_page(drv: webdriver.Chrome) -> bool:
    """
    Переходит на следующую страницу пагинации.

    Parameters
    ----------
    drv : webdriver.Chrome
        Экземпляр веб-драйвера.
    """

    try:
        n_btn = drv.find_element(by.CSS_SELECTOR, "li.next > a")
        n_btn.click()
        w(drv, 10).until(ec.staleness_of(n_btn))
        return True
    except NoSuchElementException, TimeoutException:
        return False


def collect_all_quotes(
    drv: webdriver.Chrome, b_url: str = BASE_URL
) -> List[Dict[str, str]]:
    """
    Итерируется по всем страницам и собирает данные.

    Parameters
    ----------
    drv : webdriver.Chrome
        Экземпляр веб-драйвера.
    b_url : str
        Базовый URL.
    """

    drv.get(b_url)
    all_dt = []
    p_num = 1

    while True:
        print(f"Парсинг страницы {p_num}...")
        all_dt.extend(parse_quotes_from_page(drv))

        if not go_to_next_page(drv):
            print("Пагинация завершена.")
            break
        p_num += 1

    return all_dt


def save_quotes_to_csv(dt: List[Dict[str, str]], fn: str = OUTPUT_FILE) -> None:
    """
    Сохраняет список словарей в CSV файл.

    Parameters
    ----------
    dt : List[Dict[str, str]]
        Данные для сохранения.
    fn : str
        Имя CSV-файла.
    """

    if not dt:
        print("Предупреждение: Нет данных для сохранения.")
        return

    try:
        with open(fn, mode="w", encoding="utf-8", newline="") as f:
            hdrs = ["text", "author", "tags", "author_link"]
            wr = csv.DictWriter(f, fieldnames=hdrs)
            wr.writeheader()
            wr.writerows(dt)
        print(f"Данные сохранены в '{fn}' (записей: {len(dt)}).")
    except IOError as e:
        print(f"Ошибка при записи файла '{fn}': {e}")


def analyze_http_vs_https(
    drv: webdriver.Chrome, dom: str = "quotes.toscrape.com"
) -> None:
    """
    Анализирует время загрузки HTTP и HTTPS версий.

    Parameters
    ----------
    drv : webdriver.Chrome
        Экземпляр веб-драйвера.
    dom : str
        Домен сайта.
    """

    print("\n--- HTTP vs HTTPS Анализ ---")
    for proto in ["http", "https"]:
        drv.delete_all_cookies()
        url = f"{proto}://{dom}/"
        print(f"Тестируем: {url}")

        s_time = time.time()
        try:
            drv.get(url)
        except Exception as e:
            print(f"  Не удалось загрузить {url}: {e}")
            continue

        l_time = time.time() - s_time
        f_url = drv.current_url
        redir = "Да" if url != f_url else "Нет"

        print(f"  Финальный URL: {f_url}")
        print(f"  Редирект:      {redir}")
        print(f"  Время загрузки:{l_time:.3f} сек\n")


def main() -> None:
    """
    Основной пайплайн 
    """

    print("Запуск парсера...")
    drv = None

    try:
        drv = create_webdriver()
        login_to_website(drv)
        q_dt = collect_all_quotes(drv)
        save_quotes_to_csv(q_dt)
        analyze_http_vs_https(drv)
    except RuntimeError as e:
        print(f"Критическая ошибка: {e}")
    finally:
        if drv:
            drv.quit()
        print("Работа парсера завершена. WebDriver закрыт.")


if __name__ == "__main__":
    main()
