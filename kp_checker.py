# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime

from pymongo import MongoClient
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def expand_shadow_element(browser, element):
    shadow_root = browser.execute_script("return arguments[0].shadowRoot", element)
    return shadow_root


def get_data(login, password):
    browser = None

    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")

        browser = webdriver.Remote("http://chrome:4444/wd/hub", options=chrome_options)
        browser.set_page_load_timeout(30)
        browser.get("https://klient.gdansk.uw.gov.pl/")

        WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.TAG_NAME, "vaadin-text-field")))

        text_shadow_section = expand_shadow_element(browser, browser.find_element(By.TAG_NAME, "vaadin-text-field"))
        login_field = text_shadow_section.find_element(By.CSS_SELECTOR, "input")
        login_field.send_keys(login)

        password_shadow_section = expand_shadow_element(
            browser, browser.find_element(By.TAG_NAME, "vaadin-password-field")
        )
        password_field = password_shadow_section.find_element(By.CSS_SELECTOR, "input")
        password_field.send_keys(password)

        button_shadow_section = expand_shadow_element(browser, browser.find_elements(By.TAG_NAME, "vaadin-button")[-1])
        login_button = button_shadow_section.find_element(By.ID, "button")
        login_button.click()

        WebDriverWait(browser, 30).until(EC.url_changes(browser.current_url))

        combined_data = ""
        labels = browser.find_elements(By.TAG_NAME, "label")[1:]

        data_fields = browser.find_elements(By.TAG_NAME, "vaadin-text-field")
        for i in range(len(data_fields)):
            data_field = data_fields[i]
            field_shadow = expand_shadow_element(browser, data_field)
            input_field = field_shadow.find_element(By.CSS_SELECTOR, "input")
            field_value = input_field.get_attribute("value")
            data_name = labels[i].get_attribute("innerHTML") if i < len(labels) else "\t[?]: "
            combined_data += f"*{data_name}:* {field_value}\t"

        notes_field = browser.find_elements(By.TAG_NAME, "vaadin-text-area")[0]
        notes_shadow = expand_shadow_element(browser, notes_field)
        text_area_field = notes_shadow.find_element(By.CSS_SELECTOR, "textarea")
        combined_data += "*Notes:* " + text_area_field.get_attribute("value")

    except Exception as ex:
        send_error(ex)
        combined_data = ""

    finally:
        if browser:
            browser.quit()

    return combined_data


def get_file_path():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, "data.txt")


def get_current_data():
    print("Reading current data")
    data = {}

    file_name = get_file_path()
    if not os.path.exists(file_name):
        return data

    with open(file_name, "r+", encoding="utf-8") as file:
        file_data = file.read()
        lines = file_data.split("\n")
        for line in lines:
            if len(line) > 0:
                user_name, user_data = line.split("\t", 1)
                if user_name and user_data:
                    data[user_name] = user_data
    return data


def save_data(new_data):
    file_name = get_file_path()
    print(f"Saving new data to '{file_name}'...")
    with open(file_name, "w+", encoding="utf-8") as file:
        for user_name, user_data in new_data.items():
            line = f"{user_name}\t{user_data}\n"
            file.write(line)


def perform_check(collection, client):
    user_name = client["name"]

    print(f"Checking user {user_name}...")
    old_data = client["data"]
    new_data = get_data(client["login"], client["password"])

    if new_data == "":
        print("Couldn't get new data")
        return False

    if old_data == new_data:
        print(f"No new data:\n{new_data}")
        return False

    print(f"Old data: {user_name} -> {old_data}")
    print(f"New data: {user_name} -> {new_data}")

    query = {"name": user_name}
    update_data = {"$set": {"data": new_data}}
    collection.update_one(query, update_data)

    formatted_old_data = old_data.replace("\t", "\n")
    formatted_new_data = new_data.replace("\t", "\n")
    text = f"*Status changed for {user_name}:*\n\n*Old Status:*\n{formatted_old_data}\n\n*New Status:*\n{formatted_new_data}"
    telegram_id = client["telegram"]
    admin_id = os.environ["TELEGRAM_ADMIN_ID"]
    send_message(text, telegram_id)
    if str(telegram_id) != str(admin_id):
        send_message(text, admin_id)

    return True


def send_error(exception):
    admin_id = os.environ["TELEGRAM_ADMIN_ID"]
    exception_message = f"Exception [{type(exception).__name__}]: {exception}, Args: {exception.args!r}"
    print(exception_message)
    send_message(exception_message, admin_id)
    print("Sleeping for 30s...")
    time.sleep(30)


def send_message(message, telegram_id):
    token = os.environ["TELEGRAM_API_TOKEN"]
    send_text = (
        f"https://api.telegram.org/bot{token}/sendMessage?chat_id={telegram_id}&parse_mode=Markdown&text={message}"
    )
    requests.get(send_text)
    time.sleep(5)


def get_database():
    username = os.environ["MONGO_INITDB_ROOT_USERNAME"]
    password = os.environ["MONGO_INITDB_ROOT_PASSWORD"]
    connection_string = f"mongodb://{username}:{password}@mongo:27017/"
    mongo_client = MongoClient(connection_string)
    return mongo_client["kp_checker"]


if __name__ == "__main__":
    print(f"Executing at {datetime.now()}...")
    db = get_database()
    collection = db["clients"]
    clients = collection.find()
    for client in clients:
        perform_check(collection, client)
        time.sleep(5)
    print("Check completed")
