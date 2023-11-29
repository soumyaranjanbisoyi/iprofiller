from main import IndividualAnalyzer
import os
import json
from dotenv import load_dotenv


load_dotenv()

api_key = "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"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class NewAnalyzer:
    ls = ["legal_disputes", "Close_connections", "Additional_Information", "awards_and_honorss", "philanthropy_activitiess", "early_lifee", "property_holdings", "Careers"]

    def __init__(self, api_key=api_key, user_agent=user_agent):
        self.individual_analyzer = IndividualAnalyzer(api_key, user_agent)

    def analyze_person(self, person_name):
        wiki_data = self.individual_analyzer.scrape_wikipedia_data(person_name)
        if not wiki_data:
            print(f"profile not found on wikipedia for {person_name}")
            wikipedia_data = {}
        else:
            wikipedia_data = self.individual_analyzer.wiki_json(wiki_data)
        if type(wikipedia_data) == list and len(wikipedia_data) > 0:
            wikipedia_data = wikipedia_data[0]
        forbes_data = self.individual_analyzer.scrape_forbes_data(person_name)
        # if not forbes_data.get('name'):
        #     return {"status": 404, "message": "Name not found in Forbes data"}  #Added this on 21st sept
        result = {}
        for key in self.ls:
            openai_data = self.individual_analyzer.scrap_gpt(person_name, key)
            result[key] = openai_data[key]
        combined_result = {**wikipedia_data, **forbes_data, **result}

        combined_result_formatted = {}
        for key, value in combined_result.items():
            if isinstance(value, str):
                # Replace \n with <br> tags for string values
                value = value.replace('\n', '<br>')
            combined_result_formatted[key] = value

        data_directory = os.path.join("data","json_data")
        person_name=person_name.replace(" ", "_")
        json_file_path = os.path.join(data_directory, f"{person_name}.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(combined_result_formatted, json_file, indent=4)

        return {"status": 200, "json_path": json_file_path}


    def check_json_file_exists(self, person_name):
        person_name = person_name.replace(" ", "_")
        json_data_directory = os.path.join("data","json_data")
        json_file_path = os.path.join(json_data_directory, f"{person_name}.json")
        if os.path.exists(json_file_path):
            return {"status": 200, "json_path": json_file_path}
        else:
            return {"status": 404, "json_path": None}


if __name__ == "__main__":
    api_key = api_key
    user_agent = user_agent

    analyzer = NewAnalyzer(api_key, user_agent)  # Create an instance of NewAnalyzer
    first_name = input("Enter first name:")
    last_name = input("Enter last name:")
    name = first_name + " " + last_name
    result = analyzer.analyze_person(name)  # Use the instance to call the analyze_person method
    if result["status"] == 200:
            data = result["json_path"]

            # Modify the json_path to use a different directory structure
            json_path_parts = data.split(os.path.sep)
            print(json_path_parts)
            modified_json_path = os.path.join(*json_path_parts)

            session_file_path = "session.json"  # Use a fixed session file name

            json_file_path = modified_json_path.replace('\\', '/')

            # Create a new session data list with the current data
            session_data = [{"name": name, "json_file_path": json_file_path}]

            # Update the session file with the modified session data, overwriting the previous file
            with open(session_file_path, 'w') as session_file:
                json.dump(session_data, session_file, indent=4)
    # if result["status"] == 200:
    #     data = result["json_path"]

    #     # Modify the json_path to use a different directory structure
    #     json_path_parts = data.split(os.path.sep)
    #     modified_json_path = os.path.join("pages", *json_path_parts)

    #     session_file_path = "data/session.json"
    #     session_data = []

    #     if os.path.exists(session_file_path):
    #         with open(session_file_path, 'r') as session_file:
    #             session_data = json.load(session_file)

    #     json_file_path = modified_json_path.replace('\\', '/')

    #     # Append the new data to the session data
    #     session_data.append({"name": name, "json_file_path": json_file_path})

    #     # Update the session file with the modified session data
    #     with open(session_file_path, 'w') as session_file:
    #         json.dump(session_data, session_file, indent=4)