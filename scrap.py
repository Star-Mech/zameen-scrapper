from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

from utils import get_text_javascript

import time
import random
import json



class City:
    def __init__(self, url) -> None:
        self.url = url
    
    def _get_total_pages(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text)

        total_pages = int(soup.select_one('ul[aria-label="Pagination"] > li:nth-last-child(2) > a').text)

        return total_pages

    def get_all_project_links(self):
        
        city_project_urls = []
        total_pages = self._get_total_pages()

        for page in range(1, total_pages+1):
            time.sleep(random.randint(1, 5))
            try:
                response = requests.get(f'https://www.zameen.com/new-projects/islamabad-3-1/?page={page}')
                    
                soup = BeautifulSoup(response.text)
                proj_tags = soup.select("main > div > div > div > div > div > a")
                urls = [ele.get('href') for ele in proj_tags]
                city_project_urls.extend(urls)
            
            except requests.exceptions.ReadTimeout:
                time.sleep(10)
                continue
            
        return city_project_urls
    
    def scrap(self, driver):
        city_project_urls = self.get_all_project_links()

        proj_base_url = 'https://www.zameen.com'

        for proj_url in city_project_urls:
            page_url = proj_base_url + proj_url



            page = Page(page_url)

            try:
                project_data = page.scrap(driver)

                with open(f"data/{project_data['project_name']}", 'w') as json_file:
                    json.dump(project_data, json_file)
            
            except: # Any unhandled exception
                print(f"Exception on page: {page_url}")
                continue
            

class Page:
    def __init__(self, url) -> None:
        self.url = url

    def scrap(self, driver: WebDriver):
        driver.get(self.url)


        # Wait for the page to be fully loaded
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )


        project_name_selector = 'main > div > div > div:nth-child(1) > div > div:nth-child(2) > h1'
        project_location_selector = 'main > div> div > div:nth-child(1) > div > div:nth-child(2) > div > div > div'

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, project_name_selector))
            )

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, project_location_selector))
            )

        project_name = get_text_javascript(driver, driver.find_element(By.CSS_SELECTOR, project_name_selector))
        project_location = get_text_javascript(driver, driver.find_element(By.CSS_SELECTOR, project_location_selector))

        project_data = self._get_data(driver)
        
        # Create new dict with some info and then update it with the project_data dict
        # This way, the added information will appear at top of the dict
        data_dict = {'project_name': project_name, 'project_location': project_location}
        data_dict.update(project_data)



        return data_dict

    
    def _get_overview(self, driver):
        overview_elements = driver.find_elements(By.CSS_SELECTOR, 'main > div > div:nth-child(2) > div > div:nth-child(1) > div > div[class^="new-projects-overview"] [class^="new-projects-overview_value"]')

        offerings = overview_elements[0].text
        offerings = list(map(lambda x: x.strip(), offerings.split(' ')))


        developer = overview_elements[1].text

    def _get_data(self, driver):
    
        this_project_data = {}

        overview_elements = driver.find_elements(By.CSS_SELECTOR, 'main > div > div:nth-child(2) > div > div:nth-child(1) > div > div[class^="new-projects-overview"] [class^="new-projects-overview_value"]')

        offerings = overview_elements[0].text
        offerings = list(map(lambda x: x.strip(), offerings.split(' ')))


        developer = overview_elements[1].text

        this_project_data['offerings'] = offerings
        this_project_data['developer'] = developer

        info_parent_element = driver.find_element(By.CSS_SELECTOR, 'main > div > div:nth-child(2) > div > div:nth-child(2) > div > div')
        info_elements = info_parent_element.find_elements(By.CSS_SELECTOR, ':scope > div')

        tile_data = []
        for info_ele in info_elements:
            info_ele_data = {}
            # Get type name
            
            # Open the element and trigger it's loading
            info_ele.click()

            
            time.sleep(random.random()) # Some sleep to ensure loading 

            type_name = get_text_javascript(driver, info_ele.find_element(By.CSS_SELECTOR, 'div.rc-collapse-header [class*="property-type-collpase_headerTitle"]'))
            
            # Get price range
            price_range = get_text_javascript(driver, info_ele.find_element(By.CSS_SELECTOR, 'div.rc-collapse-header [class*="property-type-collpase_price"]'))
            
            if type_name.casefold() == 'shops':
                continue
            #Get the info cards within this type

            info_ele_data['type'] = type_name
            info_ele_data['price_range'] = price_range

            info_cards = info_ele.find_elements(By.CSS_SELECTOR, 'div.rc-collapse-content-box div[class*="card_card"]')
                    
            
            # Get info from each card
            cards_data_list = []
            for card in info_cards:
                card_data = {}


                # match type_name.casefold():
                #     case 'flats':
                #         (card_type_ele, card_price_ele) = card.find_elements(By.CSS_SELECTOR, 'div[class*="property-type-collpase_cardHeader"] > div > div')
            
                #     case _:
                #         (card_type_ele, card_price_ele) = card.find_elements(By.CSS_SELECTOR, 'div[class*="property-type-collpase_cardHeader"] > div > div')

                (card_type_ele, card_price_ele) = card.find_elements(By.CSS_SELECTOR, 'div[class*="property-type-collpase_cardHeader"] > div > div')
                card_type, card_price = get_text_javascript(driver, card_type_ele), get_text_javascript(driver, card_price_ele)

                card_data['type'] = card_type
                card_data['price'] = card_price

                # Info blocks within a card
                info_blocks = card.find_elements(By.CSS_SELECTOR, 'div[class*="property-type-collpase_infoBlock"]')
                
                # A single key would not be repeated within a block
                for block in info_blocks:
                    #property name
                    property_name = get_text_javascript(driver, block.find_element(By.CSS_SELECTOR, ':scope > div:nth-child(2) div[class*="property-type-collpase_key"]'))
                    #property value
                    property_val = get_text_javascript(driver, block.find_element(By.CSS_SELECTOR, ':scope > div:nth-child(2) div[class*="property-type-collpase_value"]'))

                    card_data[property_name] = property_val

                cards_data_list.append(card_data)
            
            info_ele_data['cards'] = cards_data_list

            tile_data.append(info_ele_data)

        this_project_data['tiles'] = tile_data

        return this_project_data




    if __name__ == "__main__":

        isb_url ='https://www.zameen.com/new-projects/islamabad-3-1/'

        city = City(isb_url)

        driver = webdriver.Chrome()
        city.scrap()