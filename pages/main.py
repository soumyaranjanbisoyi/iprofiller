import time
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain
import requests
from bs4 import BeautifulSoup
import json
import re
import openai
import os
import logging
from dotenv import load_dotenv


load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


api_key = "sk-"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"




class IndividualAnalyzer:
    def __init__(self, api_key, user_agent):
        self.api_key = api_key
        self.user_agent = user_agent
        openai.api_key = api_key
        self.base_forbes_url = "https://www.forbes.com/profile/"

    def scrape_wikipedia_data(self, person_name):
        """
        Scrapes data from Wikipedia for a given person's name.

        Args:
            person_name (str): The name of the person.

        Returns:
            str: The scraped data from Wikipedia or None if not found.
        """

        session = requests.Session()
        session.headers["User-Agent"] = user_agent
        proper_case_name = person_name.title()
        page_title = proper_case_name.replace(' ', '_')

        url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&titles={page_title}&explaintext=1"

        max_retries = 3
        retry_delay = 5
        for retry in range(max_retries):
            response = session.get(url)

            if response.status_code == 200:
                data = response.json()
                pages = data["query"]["pages"]
                if "-1" in pages:
                    logger.info(f"Profile not found on Wikipedia for {person_name}")
                    # return "Profile not found on Wikipedia"
                    return None
                page_id = next(iter(pages))
                content = pages[page_id].get("extract")

                if content:
                    return content[:16385]

            elif response.status_code == 503:
                logger.info(f"503 Service Unavailable. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(
                    f"Failed to fetch data for {person_name} from Wikipedia. Status code: {response.status_code}")
                return None

        logger.error(f"Max retries reached. No Wikipedia data found for {person_name}")
        return None


    def wiki_json(self, wikipedia_data):
        output_schema = {
            "properties": {
                "address": {"type": "string"},
                "marital_status": {"type": "string"},
                "property_holding": {"type": "string"},
                "early_life": {"type": "string"},
                "Business_career": {"type": "string"},
                "Investment_details": {"type": "string"},
                "philanthropy_activities": {"type": "string"},
                "awards_and_honours": {"type": "string"},
                "Occupation": {"type":"string"}
                # "legal_disputes": {"type": "string"},
            }
        }
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k")
        chain = create_extraction_chain(output_schema, llm)
        result_json = chain.run(wikipedia_data)
        return result_json

    def scrape_forbes_data(self, person_name):
        """
        Scrapes data from Forbes for a given person's name.

        Args:
            person_name (str): The name of the person.

        Returns:
            dict: A dictionary containing scraped data from Forbes.
        """
        forbes_data = {}
        forbes_url = f"{self.base_forbes_url}{person_name.replace(' ', '-').lower()}/"
        response = requests.get(forbes_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            name_element = soup.find("h1", class_="listuser-header__name")
            name = name_element.text.strip() if name_element else "Name not found"
            net_worth_element = soup.find("div", class_="profile-info__item-value")
            net_worth = net_worth_element.text.strip() if net_worth_element else "Net worth not found"
            bio_element = soup.find("div", class_="listuser-content__bio")
            bio = bio_element.text.strip() if bio_element else "Bio not found"
            person_stats_element = soup.find("div", class_="listuser-content__block person-stats")

            if person_stats_element:
                person_stats_text = person_stats_element.get_text(separator='\n')
                person_stats_lines = person_stats_text.split('\n')
                person_stats_dict = {}
                key = None
                for line in person_stats_lines:
                    if line.strip() == "Personal Stats":
                        continue
                    if key is None:
                        key = line.strip()
                    else:
                        person_stats_dict[key] = line.strip()
                        key = None
            else:
                logger.info("Person Stats not found")
                person_stats_dict = {}

            ranking_element = soup.find("div", class_="listuser-content__block ranking")

            if ranking_element:
                ranking_text = ranking_element.get_text(separator='\n')

                ranking_lines = ranking_text.split('\n')

                ranking_info = {}
                ranking_info["Billionaires Rank (2023)"] = ranking_lines[1]
                # ranking_info["Forbes 400 Rank (2022)"] = ranking_lines[4]
            else:
                logger.info("Ranking information not found")
                ranking_info = {}
            image_element = soup.find("div", class_="listuser-image")

            if image_element:
                style_attr = image_element.get("style")
                image_url_match = re.search(r'url\(([^)]+)\)', style_attr)
                if image_url_match:
                    image_url = image_url_match.group(1)
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        image_dir = os.path.join("data","public","images")
                        image_filename = os.path.join(image_dir, f"{person_name.replace(' ', '_').lower()}.jpg")
                        with open(image_filename, "wb") as image_file:
                            image_file.write(image_response.content)
                            logger.info(f"Image saved as {image_filename}")
                        # Replace backslashes with forward slashes
                        image_full_path = image_filename.replace('\\', '/')

                        # Append the prefix to the image path
                        image_full_path_with_prefix = "http://localhost:3000/pages/" + image_full_path

                        # Create a session data list with the image_full_path_with_prefix
                        session_data = [{"image_full_path": image_full_path_with_prefix}]

                        # Write the session data to the session.json file
                        session_file_path = os.path.join("data", "session.json")
                        with open(session_file_path, 'w') as session_file:
                            json.dump(session_data, session_file, indent=4)

                    else:
                        logger.error(
                            f"Failed to download image from {image_url}. Status code: {image_response.status_code}")
                        image_full_path_with_prefix = None  # Set to None in case of failure
                else:
                    image_url = "Image URL not found"
            else:
                logger.info(f"Image not found for {name}")
                image_url = "Image URL not found"
                image_full_path_with_prefix = None  # Set to None if image_element is not found


            forbes_data = {
                "Name": name,
                "Net_Worth": net_worth,
                "Bio": bio,
                **person_stats_dict,
                **ranking_info,
                "image_path": image_full_path_with_prefix,
            }

        else:
            logger.error(
                f"Failed to fetch data from the Forbes page for {person_name}. Status code: {response.status_code}")
            return {"Message": "Profile not present in Forbes"}

        return forbes_data

    def scrap_gpt(self, person_name, key):
        prompt = {
            "legal_disputes": f"Extract information about any legal disputes involving {person_name}.",
            "philanthropy_activitiess": f"extract philanthopy activities done by {person_name}, make sure the sentence is completed properly and ends with proper puntuation",
            "awards_and_honorss": f"Extract awards and honors received by {person_name}, make sure to keep the info in bullet pointers",
            "Close_connections": f"Extract Name of 5 influential business people connected with {person_name}. Make sure it should contain only name of the person in bullet point, and while doing the formatting make sure to use <br> tags instead of python line breaks.",
            "Additional_Information": f"Extract any additional information about {person_name} that may be missing from previous sections but is important. Make sure to make a short summary about it and it should be crips with proper formatting.",
            "early_lifee": f"Extract details about {person_name} early life, make sure information should be completed properly and ends with proper puntuation",
            "property_holdings": f"Extract assets that {person_name} owns, make sure the sentence is completed properly and ends with proper puntuation",
            "Careers": f"Extract all information about {person_name} professional career. Make sure it should only contain information about the professional background like previous company, current company, etc.",

        }.get(key, f"Invalid key: {key}")

        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=1000,
            top_p=1.0,
            stop=None
        )
        response_text = response.choices[0].text.strip()

        result_json = {key: response_text}
        return result_json













