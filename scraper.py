#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Importing necessary modules

from selenium import webdriver
from time import sleep
import pandas as pd
import numpy as np
from datetime import datetime
from selenium.common.exceptions import StaleElementReferenceException


"""
I chose to use selenium as my scraper in order to autoatically navigate multiple pages in amazon. 
"""

### Creating class for scraping toys-for-fun website
class ToysForFun:
    def __init__(self):
        """
        Start the webdriver.
        """
        self.driver = webdriver.Chrome()
        
        # navigate to toys-for-fun "all results" lego page, where marke == lego
        self.driver.get('https://www.toys-for-fun.com/de/kategorien/bauen-konstruieren/lego/shopby/lego.html?limit=all')
    
    def quit(self):
        """
        Quit the webdriver and close the page
        """
        self.driver.close()
        self.driver.quit()
    
    def grab(self):
        """
        Grab pricing and product name information from the "all results" lego page
        """
        # find product names/titles 
        items = self.driver.find_elements_by_class_name('product-name')
        self.product_names = []
        for item in items:
            self.product_names.append(item.text)

        # find product prices
            # this also grabs discounted prices, we will clean this up later
        items = self.driver.find_elements_by_class_name('price-box')
        self.prices = []
        for item in items:
            #text = item.text
            self.prices.append(item.text)
        
    """
    Although not in the scope of the project, it may be useful to grab further information from each product.
    We can iterate through each product landing page to find information such as the availability, age range, gender, and so on.
    
    This information won't be included in the final analysis, but would make a great starting place for more detailed analysis.
    
    For example:
        - analysing the effect that the intended age range has on price
        - analysing whether certain products are consistently out of stock
            - this could help establish demand trends which would affect pricing and elasticity
            - will allow analysis on whether stock levels affect pricing strategy
    
    We additionally need to return the EAN for each product, to help us grab the product information from Amazon.
    """
    
    def product(self, product_names):
        """
        Iterate through each product landing page to return EAN, availability, and intended age range.
        """
        
        # part of the limiter
        i = 0
        
        # start iteration through the product landing pages
        self.product_links = []
        self.availability = []
        self.intended_age_range = []
        self.ean = []
        for item in product_names:
            try:
                result = self.driver.find_element_by_link_text(item)
                
                # find product landing page links
                # technically do not need to do this next line, but I find it's good to have a reference
                self.product_links.append(result.get_attribute("href"))
                
                # after a random wait, click on link
                sleep(np.random.random_sample())
                result.click()
            except Exception:
                self.product_links.append('')
                self.availability.append('')
        
            # find product availability
            try:
                product_availability = self.driver.find_element_by_class_name('extra-info')
                self.availability.append(product_availability.text)
            except Exception:
                self.availability.append('')
                self.intended_age_range.append("No information for this product")
                self.ean.append("No information for this product")
            
            try:
                # after a half second wait, click on "Zusatzinformation"
                sleep(0.5)
                self.driver.find_element_by_xpath('//*[@id="top"]/body/div[2]/div/div[2]/div/div[2]/div[4]/div[2]/ul/li[3]').click()
                
                # find product intended age range
                product_intended_age_range = self.driver.find_element_by_xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[5]')
                self.intended_age_range.append(product_intended_age_range.text)
            
                # find product EAN
                product_ean = self.driver.find_element_by_xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[8]')
                self.ean.append(product_ean.text)
            except Exception:
                try: 
                    self.driver.find_element_by_xpath('//*[@id="top"]/body/div[2]/div/div[2]/div/div[2]/div[4]/div[3]/ul/li[3]').click()
                
                    # find product intended age range
                    product_intended_age_range = self.driver.find_element_by_xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[5]')
                    self.intended_age_range.append(product_intended_age_range.text)
                
                    # find product EAN
                    product_ean = self.driver.find_element_by_xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[8]')
                    self.ean.append(product_ean.text)
                except Exception:
                    self.intended_age_range.append("No information for this product")
                    self.ean.append("No information for this product")

            # the below commented code is a limiter, in case there is no need to grab all products
            # uncomment as necessary
            """      
            i = i + 1
            if i > 100:
                break
            """      
            # after a random wait, navigate back to home page
            sleep(np.random.random_sample())
            self.driver.back()

"""
Grabbing products from Amazon:
    
In the end I decided to use the EANs from toys-for-fun to automatically search in Amazon.
As Amazon support direct search via EAN, this is a safe method of grabbing the correct product. 
- I will nonetheless do a double check by comparing the Lego product numbers
- This will help eliminate any failures from the analysis

Instead of simulating clicks and text entry, I could have also provided an edited "search url"
- such as: https://www.amazon.de/s?k=5702016668247&ref=nb_sb_noss
- both methods work fine, but Amazon is more likely to detect the url method and block my IP

Instead of using the EAN to search for the product, I could have also crawled the entire Lego category page.
This would be a similar approach to the method taken for toys-for-fun.
However, Amazon is actively working against people trying to scrape.
- this makes the solution not only hard to implement
- but also means it is not particularly future-proof, as they are always changing the structure of the website

So with this in mind, I decided on the EAN search method. 
Although it sacricficies on performance slightly, it is a more future-proof approach. 
"""

### Creating class for scraping Amazon
class Amazon:
    def __init__(self):
        """
        Start the webdriver.
        """
        self.driver = webdriver.Chrome()
        
        # navigate to amazon lego page, where brand == lego
        self.driver.get('https://www.amazon.de/')
    
    def quit(self):
        """
        Quit the webdriver and close the page
        """
        self.driver.close()
        self.driver.quit()
    
    def grab(self, eans):
        """
        Grab pricing and product name information.
        This is achieved by searching for the ean of a product. 
        """

        self.title = []
        self.price = []
        self.strike_price = []
        # adding in a cooldown period every 15 products
        i = 0
        
        for ean in eans:
            # enter ean and click on search bar
            sleep(1)
            try:
                search = self.driver.find_element_by_id('twotabsearchtextbox')
                search.click()
                sleep(0.3)
            except StaleElementReferenceException:
                    self.driver.get('https://www.amazon.de/')
                    search = self.driver.find_element_by_id('twotabsearchtextbox')
                    search.click()
                    sleep(0.3)
            search.clear()
            sleep(1)
            search.send_keys(ean)
            sleep(1)
            self.driver.find_element_by_class_name('nav-input').click()
            sleep(0.5)
            # this reorders the products so the "sponsored" products come below the actual product 
            # therefore we can consistently search for the correct product and not a sponsored one
            try:
                self.driver.find_element_by_xpath('//*[@id="s-result-sort-select"]/option[2]').click()
            except Exception:
                self.title.append('')
                self.price.append('')
                self.strike_price.append('')
                pass
            sleep(1)
            try:
                self.driver.find_element_by_xpath('//*[@id="s-result-sort-select_1"]').click()
            except Exception:
                self.title.append('')
                self.price.append('')
                self.strike_price.append('')
                pass
            sleep(1)

            
            try:
                # find product title
                # exceptions match the different instances of how the data can be found on different pages
                product_title = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[1]/div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div/h2/a/span')
                self.title.append(product_title.text)
            except Exception:
                try:
                    alt_product_title = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a/span')
                    self.title.append(alt_product_title.text)
                except Exception:
                    try:
                        alt_product_title2 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[1]/div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div/h2/a/span')
                        self.title.append(alt_product_title2.text)
                    except Exception:
                        try:
                            alt_product_title3 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a/span')
                            self.title.append(alt_product_title3.text)
                        except Exception:
                            try:
                                alt_product_title4 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[1]/div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a/span')
                                self.title.append(alt_product_title4.text)
                            except Exception:
                                try:
                                    alt_product_title5 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/h2')
                                    self.title.append(alt_product_title5.text)
                                except Exception:
                                    try:
                                        alt_product_title6 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/h2/a/span')
                                        self.title.append(alt_product_title6.text)
                                    except Exception:
                                        try:
                                            alt_product_title7 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/h2/a/span')
                                            self.title.append(alt_product_title7.text)
                                        except Exception:
                                            self.title.append("")
                                            print(ean)

            try:
                # find product price
                # exceptions match the different instances of how the data can be found on different pages
                product_price = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[1]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[1]/span[2]/span[1]')
                self.price.append(product_price.text)
            except Exception:
                try:
                    alt_product_price = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[1]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[1]/span[2]/span[1]')
                    self.price.append(alt_product_price.text)
                except Exception:
                    try:
                        alt_product_price2 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[1]/span[2]/span[1]')
                        self.price.append(alt_product_price2.text)
                    except Exception:
                        try: 
                            alt_product_price3 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[1]/span[2]/span[1]')
                            self.price.append(alt_product_price3.text)
                        except Exception:
                            try:
                                alt_product_price4 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[2]/div/span/div/div/div[4]/div/div/a/span[1]/span[2]/span[1]')
                                self.price.append(alt_product_price4.text)
                            except Exception:
                                try:
                                    alt_product_price5 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[2]/div/span/div/div/div[4]/div/div/a/span[1]/span[2]/span[1]')
                                    self.price.append(alt_product_price5.text)
                                except Exception:
                                    self.price.append("not available")
                            
                
                    
            try:
                # find product strike price
                # exceptions match the different instances of how the data can be found on different pages
                product_strike_price = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[1]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[2]/span[2]')
                self.strike_price.append(product_strike_price.text)
            except Exception:
                try:
                    alt_product_strike_price = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[2]/div/span/div/div/div[4]/div/div/a/span[2]/span[2]')
                    self.strike_price.append(alt_product_strike_price.text)
                except Exception:
                    try:
                        alt_product_strike_price2 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[1]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[2]/span[2]')
                        self.strike_price.append(alt_product_strike_price2.text)
                    except Exception:
                        try:
                            alt_product_strike_price3 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[2]/span[2]')
                            self.strike_price.append(alt_product_strike_price3.text)
                        except Exception:
                            try:
                                alt_product_strike_price4 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[2]/span[2]')
                                self.strike_price.append(alt_product_strike_price4.text)
                            except Exception:
                                try:
                                    alt_product_strike_price5 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[2]/div/span/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/a/span[2]/span[2]')
                                    self.strike_price.append(alt_product_strike_price5.text)
                                except Exception:
                                    try:
                                        alt_product_strike_price6 = self.driver.find_element_by_xpath('//*[@id="search"]/div[1]/div[2]/div/span[3]/div[2]/div[2]/div/span/div/div/div[4]/div/div/a/span[2]/span[2]')
                                        self.strike_price.append(alt_product_strike_price6.text)
                                    except Exception:
                                        self.strike_price.append("")
                                    
            # adding in rate limiting with a 60s break every 10 articles
                # also an extra cooldown period every 50 articles   
            i = i + 1
            if i % 10 == 0:
                sleep(60)
            if i % 50 == 0:
                sleep(80)

# Collecting toys-for-fun prices

### Running toys-for-fun scraper       
bot = ToysForFun()
bot.grab()
bot.product(bot.product_names)
bot.quit()

### Creating a clean list of EANs
ean_list = []
for item in bot.ean:
    try:
        ean_list.append(item.split(sep=' ', maxsplit=1)[1])
    except Exception:
        ean_list.append('information for this product')

### Creating ToysForFun Dataframe
toysforfundf = pd.DataFrame(data=np.resize(np.array(ean_list), (len(ean_list),1)))
toysforfundf["price"] = bot.prices[:len(ean_list)]
toysforfundf["title"] = bot.product_names[:len(ean_list)]
toysforfundf["links"] = bot.product_links[:len(ean_list)]
toysforfundf["availability"] = bot.availability[:len(ean_list)]
toysforfundf["intended_age_range"] = bot.intended_age_range[:len(ean_list)]
    
### Create a csv file to be cached
### it may come in handy to have historical data which can be referred to at a later stage
toysforfundf.to_csv("toys-for-fun.csv")
toysforfundf.to_csv(("toys-for-fun-df-{}.csv").format(datetime.today().strftime('%Y-%m-%d')))


# Collecting Amazon prices

### Running Amazon scraper 
bot2 = Amazon()
bot2.grab(ean_list)
bot2.quit()
    
### Creating Amazon Dataframe
amazondf = pd.DataFrame(data=np.resize(np.array(ean_list), (len(ean_list),1)))
amazondf["price"] = bot2.price[:len(ean_list)]
amazondf["strike_price"] = bot2.strike_price[:len(ean_list)]
amazondf["title"] = bot2.title[:len(ean_list)]
    
### Create a csv file to be cached
### it may come in handy to have historical data which can be referred to at a later stage
amazondf.to_csv("amazondf.csv")
amazondf.to_csv(("amazon-df-{}.csv").format(datetime.today().strftime('%Y-%m-%d')))
