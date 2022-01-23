import sys
import os
import time
import json

# https://selenium-python.readthedocs.io/getting-started.html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# https://lxml.de/tutorial.html
from lxml import etree

EXEPATH = sys.argv[0]
DIR_PATH = os.path.dirname(os.path.abspath(EXEPATH))
DOWNLOAD_DIR_TRK = DIR_PATH+"\\data\\trk\\"
JSON_DIR = DIR_PATH+"\\data\\json\\"

"""
Use chromedriver version according to local current chrome version
Version here : 97.0.4692.71
https://chromedriver.chromium.org/home
"""
CHROMEDRIVER_DIR=DIR_PATH+"\\selenium\\chromedriver.exe"

XPATH_TO_FLIGHT_DATE = "/html/body/div[1]/div[2]/div/div/div[1]/div/div[3]/section/ul[1]/li[1]/a"
XPATH_TO_FLIGHT_DISTANCE = "/html/body/div[1]/div[2]/div/div/div[1]/div/div[3]/section/ul[1]/li[6]/b"
XPATH_TO_FLIGHT_DURATION = "/html/body/div[1]/div[2]/div/div/div[1]/div/div[3]/section/ul[1]/li[8]"
XPATH_TO_FLIGHT_TRK = "/html/body/div[1]/div[2]/div/div/div[1]/div/div[3]/section/ul[2]/li[4]/a"
XPATH_TO_FLIGHT_TYPE="/html/body/div[1]/div[2]/div/div/div[1]/div/div[3]/section/ul[1]/li[2]/a"

ONLINE_TRK_TO_GPX ="https://www.gpsvisualizer.com/convert_input?convert_format=gpx&units=metric"


def create_driver():
    """
    # Locate the chromedriver executable and create driver
    # get the path from the .py file
    # get the path of "datasets" directory
    
    returns a headless chromedriver
    """

    # Driver preferences
    preferences = {
        "download.default_directory": DOWNLOAD_DIR_TRK,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True 
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", preferences)

    # Headless driver
    chrome_options.add_argument("--headless")  

    # Create webdriver
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_DIR, options=chrome_options)
    
    return driver
    

def get_primary_flight_info(driver):
    """
    gets : 05/09/2021 91.25 km durée (du parcours) : 4h31mn
    returns str types: 
        05/09/2021
        91.25
        4h31mn
    
    """
    try:
        date = driver.find_element(By.XPATH, XPATH_TO_FLIGHT_DATE).text
        distance = driver.find_element(By.XPATH, XPATH_TO_FLIGHT_DISTANCE).text
        distance = distance.split(' ')[0]
        duration= driver.find_element(By.XPATH, XPATH_TO_FLIGHT_DURATION).text
        duration = duration.split(': ')[1]
        type = driver.find_element(By.XPATH, XPATH_TO_FLIGHT_TYPE).text
        return (
            date,
            distance,
            duration,
            type
        )
    except Exception as e :
        print(e + 'ERROR: cannot get primary flight info')
    

def download_trk_file(driver):
    """
    Returns .trk file.
    Saves it in DOWNLOAD_DIR_TRK
    """
    
    igc_trk = driver.find_element(By.XPATH, XPATH_TO_FLIGHT_TRK)
    igc_trk.click()  
    time.sleep(5)
    

def convert_trk_into_gpx(driver):
    """
    Using selenium it takes .trk file previously downloaded and convert it into .gpx
    """
    
    for file_name in os.listdir(DOWNLOAD_DIR_TRK):
        file_path = DOWNLOAD_DIR_TRK+file_name    
    driver.get(ONLINE_TRK_TO_GPX)
    # Upload gpx file
    try :        
        driver.find_element(By.ID, "input:uploaded_file_1").send_keys(file_path)               
        time.sleep(5)
        driver.find_element(By.NAME, "submitted").send_keys(Keys.ENTER)
        time.sleep(15)
        driver.find_element(By.XPATH, "/html/body/table/tbody/tr/td[2]/p[3]/a").send_keys(Keys.ENTER)
        time.sleep(3)
    except Exception as e :
        print(e + 'ERROR: cannot convert trk into gpx')
    
    
def scrap_flight(cfd_link):
    """
    Generates a .trk file followed by a temporary .gpx file.
    Function returns date, distance, duration of flight as string
    """
    
    driver = create_driver()
    try:        
        # Go to link provided as arg_1, driver automatically waits until page is fully loaded
        driver.get(cfd_link)
        # Gives primary infos : 05/09/2021 91.25 4h31mn
        date, distance, duration, type= get_primary_flight_info(driver)  
        print(date, distance, duration, type)     
        # Download .trk file
        download_trk_file(driver)        
        # Convert trk to gpx
        convert_trk_into_gpx(driver)        
    except Exception as e:
        print(e + 'ERROR: cannot scrap flight datas')
    driver.close()    
    return (
        date,
        distance, 
        duration,
        type
    )
    
    
def find_gpx_file():
    for file in os.listdir(DOWNLOAD_DIR_TRK):
        if file.endswith(".gpx"):
            return file
        
    
def convert_gpx_to_json(flight_date):
    """
    Create a liste of coordinnates from the .gpx file 
    and write an MVC array into a Json file
    """
    
    # date toute attachée de référence à la date du vol et au fichier gpx ?
    date = flight_date.replace('/', '-')    
    # find filename :    
    filename = find_gpx_file()         
    # Fichier exporté en format GPX
    file = open(DOWNLOAD_DIR_TRK+filename, 'r')
    # Chargement en mémoire du contenu du fichier
    root = etree.parse(file)
    # Format normalisé des fichiers GPX
    ns = "http://www.topografix.com/GPX/1/1"
    # Chemin de l'arborescence des données pour extraire le trkpt
    liste_points = root.xpath("/ns:gpx/ns:trk/ns:trkseg/ns:trkpt", namespaces={"ns": ns})
    # Liste des latitudes en degrés
    latitude = []
    # Liste des longitudes en degrés
    longitude = []    
    # Lecture des données
    for point in liste_points:
        latitude.append(float(point.get("lat")))
        longitude.append(float(point.get("lon")))
    # Création d'une liste de tuples (lat, lon):
    coordinates = [(latitude[i], longitude[i]) for i in range(0, len(latitude))]
    # print(coordinates)
    # [ ..., 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667), 
    #  (45.4681333, 1.8510667)]
    
    # React google map Polyline path needs to be an MVC array : [{lat: 37.772, lng: -122.214}, {lat: 21.291, lng: -157.821}]
    MVCarray = [{"lat":x[0],"lng":x[1]} for x in coordinates]
    
    # Enregistrer la liste au format json (le fichier pourra être ensuite stocké dans models.py sous JSONField ?)
    with open(JSON_DIR+'{}.json'.format(date), 'w') as f:
        json.dump(MVCarray, f)
    
    # Faire le ménage
    delete_downloaded_files()
        
def delete_downloaded_files():
    """
    Deletes unwanted .trk and .gpx files.
    """    
    for file in os.listdir(DOWNLOAD_DIR_TRK):        
        os.remove(DOWNLOAD_DIR_TRK+file)
    print('Files have been deleted')
        

def scrap_and_convert_to_JSON_MVCarray():
    """
    Needs a valid URL.
    Main fonction.
    1 -> Scrap .trk file
    2 -> Convert .trk into .gpx
    3 -> Create a .json with MVCarray standard type
    """
    url = input("CFD link : ")
    date, distance, duration, type = scrap_flight(url)
    convert_gpx_to_json(date)    
    

if __name__ == "__main__":    
    
    scrap_and_convert_to_JSON_MVCarray()

#  CFD link for test puprose : https://parapente.ffvl.fr/cfd/liste/vol/20309211?sort_clear=1