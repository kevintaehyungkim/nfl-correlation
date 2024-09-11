from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import json


# util functions
def nested_dict():
    return defaultdict(nested_dict)


def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.119 Safari/537.36")
    
    chrome_driver_path = '/Users/taehyungkim/downloads/chromedriver-mac-arm64/chromedriver'
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver



TEAM_GAME_YARDS = nested_dict()


def fetch_boxscore_links(year):
    driver = setup_driver()
    game_urls = []
    
    try:
        # Navigate to the year-specific games page
        year_url = f"https://www.pro-football-reference.com/years/{year}/games.htm"
        print(f"Navigating to URL: {year_url}")
        driver.get(year_url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="div_games"]'))
        )
        
        # Find the table under header 'Week-by-Week Games' inside the div with id 'div_games'
        div_games = driver.find_element(By.XPATH, '//*[@id="div_games"]')
        rows = div_games.find_elements(By.XPATH, './/tr[not(contains(@class, "thead"))]')
        
        for row in rows:
            try:
                boxscore_link_element = row.find_element(By.XPATH, './/td[@data-stat="boxscore_word"]/a')
                if boxscore_link_element and boxscore_link_element.text.strip().lower() == 'boxscore':
                    relative_link = boxscore_link_element.get_attribute('href')
                    # full_link = base_url + relative_link
                    game_urls.append(relative_link)
            except Exception as e:
                print(f"Error finding boxscore link in row: {e}")
                continue  # Skip rows where 'Boxscore' link is not found
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
    
    return game_urls


def extract_game_id(url):
    # Extract the game ID from the URL
    match = re.search(r'boxscores/(\d+)\w+', url)
    return match.group(1) if match else 'unknown_game_id'


def convert_to_number(value):
    value = value.strip()  # Remove any surrounding whitespace
    if value == '':
        return 0  # or you can return 0 or any other default value
    try:
        # Try converting to int
        return int(value)
    except ValueError:
        try:
            # If that fails, try converting to float
            return int(float(value))
        except ValueError:
            # If both conversions fail, return the value as is
            return value



def fetch_game_stats(game_url):
    driver = setup_driver()
    
    print(f"Fetching game stats from: {game_url}")
    
    try:
        # Navigate to the game URL
        driver.get(game_url)
        
        # Wait for the table to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'player_offense'))
        )
        
        # Allow additional time for dynamic content to load
        time.sleep(5)
        
        # Extract the table
        table = driver.find_element(By.ID, 'player_offense')
        
        # Extract game ID from URL
        game_id = extract_game_id(game_url)
            
        # Extract headers
        header_elements = driver.find_elements(By.XPATH, '//*[@id="player_offense"]/thead/tr[2]/th')
        headers = [header.get_attribute('data-stat') for header in header_elements]
        # print(f"Headers: {headers}")  # Debugging output

        # Extract rows
        rows = table.find_elements(By.XPATH, './/tbody/tr')
        for row in rows:
            cells = row.find_elements(By.XPATH, './/td')
            
            # Extract player name and team
            try:
                player_name = row.find_element(By.XPATH, './/th[@data-stat="player"]').text
                team_name = row.find_element(By.XPATH, './/td[@data-stat="team"]').text
            except Exception as e:
                print(f"Error extracting player or team data: {e}")
                continue
            
            print(f"Player: {player_name}, Team: {team_name}")  # Debugging output
            
            if team_name not in TEAM_GAME_YARDS:
                TEAM_GAME_YARDS[team_name] = {}
            if game_id not in TEAM_GAME_YARDS[team_name]:
                TEAM_GAME_YARDS[team_name][game_id] = {'pass': [], 'rush': [], 'rec': []}
            
            # Extract stats based on known positions
            stats = {header: convert_to_number(cell.text) for header, cell in zip(headers[2:], cells[1:])}

            print(stats)

            if not TEAM_GAME_YARDS[team_name][game_id]['pass']:
                TEAM_GAME_YARDS[team_name][game_id]['pass'] = nested_dict()

            if not TEAM_GAME_YARDS[team_name][game_id]['rec']:
                TEAM_GAME_YARDS[team_name][game_id]['rec'] = nested_dict()

            # if not TEAM_GAME_YARDS[team_name][game_id]['rush']:
            #     TEAM_GAME_YARDS[team_name][game_id]['rush'] = nested_dict()            

            if stats.get('pass_att') > 0:
                TEAM_GAME_YARDS[team_name][game_id]['pass'][player_name] = [stats.get('pass_yds', 0), stats.get('pass_cmp', 0)]
            
            else:
                # TEAM_GAME_YARDS[team_name][game_id]['rush'][player_name] = [stats.get('rush_yds', 0), stats.get('rush_att', 0)]
                TEAM_GAME_YARDS[team_name][game_id]['rec'][player_name] = [stats.get('rec_yds', 0), stats.get('rec', 0)]
                
            

    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()
    
    # print(TEAM_GAME_YARDS)
    # return team_game_yards


def save_to_json(data, year):
    json_filename = f"game_stats_{year}.json"
    with open(json_filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved to {json_filename}")


def main(year):
    boxscore_links = fetch_boxscore_links(year)

    for link in boxscore_links:
        fetch_game_stats(link)
    
    save_to_json(TEAM_GAME_YARDS, year)
    print('output saved to json')

if __name__ == "__main__":
    main(2023)

