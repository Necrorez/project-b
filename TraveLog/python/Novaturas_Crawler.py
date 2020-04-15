from bs4 import BeautifulSoup
from selenium import webdriver
from geopy.geocoders import Nominatim
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime, date
import requests
import json
import re

class TravelData(object):
    def __init__(self,destinationName,duration,linkToWebsite,rating,countries,IndivTravelData):
        self.destinationName = destinationName
        self.duration = duration
        self.linkToWebsite = linkToWebsite
        self.rating = rating
        self.countries = countries
        self.IndivTravelData = IndivTravelData

class LocationData(object):
    def __init__(self,lat,longt):
        self.lat = lat
        self.longt = longt

class IndivTravelData(object):
    def __init__(self,seats,checkIn,checkOut,savings,beforeSavings,price):
        self.seats = seats
        self.checkIn = checkIn
        self.checkOut = checkOut
        self.savings = savings
        self.beforeSavings = beforeSavings
        self.price = price



def GetPageNumber(url):
    driver = webdriver.Chrome("/usr/bin/chromedriver")
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    pageNumber = soup.findAll(class_='pagination-item link')
    Number = []
    for i in range(0,len(pageNumber)):
        try:
            temp = pageNumber[i].find('span').contents[0]
            int(temp)
            Number.append(temp)
        except:
            continue
    Number.sort()
    return Number[-1]

def GetIndvData(url):
    soup = BeautifulSoup(url, 'html.parser')
    content = soup.find_all(class_='list-row-wrapper direction list-roundtrip')
    cont = []
    for i in range(1,len(content)):
        try:
            Seat = content[i].find('span',class_='seats minimum-left').contents[0].contents[0]
        except:
            Seat = content[i].find('span',class_='seats').contents[0].contents[0]
        if(Seat == '0'):
            continue
        CheckIn = content[i].find('span',class_='checkin').contents[0]
        CheckOut = content[i].find('span',class_='checkout').contents[0]
        try:
            Savings = re.sub(',','.',content[i].find(class_='u-label no-break').find(class_='price').contents[0].split(' ')[0])
            BeforePrice = re.sub(',','.',content[i].find(class_='price line-through').contents[0].split(' ')[0])
        except:
            Savings = "NULL"
            BeforePrice = "NULL"
        try:
            Price = re.sub(',','.',content[i].find(class_='price').contents[0].split(' ')[0])
        except:
            continue
        toAdd = IndivTravelData(Seat,CheckIn,CheckOut,Savings,BeforePrice,Price)
        cont.append(toAdd)
    driver.quit()
    return cont

def getID(url):
    x2=re.split("/",url)
    try:
        urlText=x2[12]
        URLParsed = "https://www.novaturas.lt/lt/nova-api/route-map?hotel_code="+str(urlText)+"&season_id=0"
        Countries = GetCountryContainer(URLParsed)
        return Countries
    except:
        driver1= webdriver.Chrome('/usr/bin/chromedriver')
        driver1.get(url)
        timeout = 20
        driver1.refresh()
        try:
            element_present = EC.presence_of_element_located((By.ID, 'main'))
            WebDriverWait(driver1, timeout).until(element_present)
        except TimeoutException:
            print("Failed Restarting")
        URLLink = driver1.current_url
        driver1.close()
        x2=re.split("/",URLLink)
        urlText=x2[12]
        URLParsed = "https://www.novaturas.lt/lt/nova-api/route-map?hotel_code="+str(urlText)+"&season_id=0"
        Countries = GetCountryContainer(URLParsed)
        return Countries
    
        
    


def GetCountry(lat,longt):
    cord = str(lat)+", "+str(longt)
    try:
        location = Nominatim().reverse(cord, exactly_one=True,language='en')
    except:
        return 'Null'
    #address = location.raw['address']['country_code']
    country = location.raw['address']['country_code']
    toReturn = country.upper()
    return toReturn

def GetCountryContainer(url):
    link = requests.get(url)
    webText=json.loads(link.text)
    cont=[]
    for i in range(1,len(webText['markers'])):
        if(webText['markers'][i]['title']=="Tarpinis sustojimas"):
            continue
        Latitude = webText['markers'][i]['latitude']
        Longitude = webText['markers'][i]['longitude']
        toAdd = LocationData(Latitude,Longitude)
        cont.append(toAdd)
    Countries=[]
    seen= set(Countries) 
    for i in range(0,len(cont)):
        ct = GetCountry(cont[i].lat,cont[i].longt)
        if(ct != "LT"):
            if ct not in seen:
                seen.add(ct)
                Countries.append(ct)
    return Countries


number = GetPageNumber("https://www.novaturas.lt/pazintines-keliones")
contentList = []
for i in range(1,int(number)+1):
    driver= webdriver.Chrome('/usr/bin/chromedriver')
    url = "https://www.novaturas.lt/pazintines-keliones?page="+str(i)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    content = soup.find_all(class_='card roundtrip-card sizing-on-tablet sizing-on-desktop')
    for i in range(0,len(content)):
        try:
            Rating = content[i].find(class_='rating-value').contents[0]
        except:
            Rating = 'NULL'
        PlaceToGo = content[i].find(class_='title').find('span').contents[0]
        Link = content[i].find('a', href=True).get('href')
        Duration = content[i].find(class_='uppercase').contents[0].split(' ')[0]

        #Loading driver for individual pages
        driver1= webdriver.Chrome('/usr/bin/chromedriver')
        driver1.get(Link)
        timeout = 3
        try:
            element_present = EC.presence_of_element_located((By.ID, 'main'))
            WebDriverWait(driver1, timeout).until(element_present)
        except TimeoutException:
            print("Loading")
        
        Countries = getID(driver1.current_url)
        
        try:
            IndvData = GetIndvData(driver1.page_source)
            URLlink = driver1.current_url
        except:
            continue
        driver1.quit()
        
        #if there is no individual data there is no point in storing it
        if(len(IndvData)==0):
            continue
        if(Countries.__contains__("Null") or len(Countries)==0):
            continue
        toAdd = TravelData(PlaceToGo,Duration,URLlink,Rating,Countries,IndvData)
        contentList.append(toAdd)


contentInfo = [{"Destination Name": v.destinationName, "Duration": v.duration,
                 "Rating": v.rating, "Link" : v.linkToWebsite, "Countries": [d for d in v.countries],
                 "Individual data": [{"Check In": a.checkIn,"CheckOut":a.checkOut,"savings":a.savings,"beforeSavings":a.beforeSavings,"price":a.price}
                  for a in v.IndivTravelData]}
                for v in contentList
                ]

now = datetime.now()
stringName = "../data/data-"+ now.strftime("%d-%m-%Y-%H")+".json"

with open(stringName, 'w', encoding='utf-8') as f:
    json.dump({"Data": contentInfo}, f, ensure_ascii=False, indent=4)