import base64
import streamlit as st
import pandas as pd
from main import IndividualAnalyzer
from run import NewAnalyzer
import os
from io import BytesIO
from streamlit_extras.switch_page_button import switch_page
import subprocess
import time
import json  
import shutil
import hydralit_components as hc
from streamlit_lottie import st_lottie

st.set_page_config(page_title="Investor Profiling" , layout="wide", initial_sidebar_state="collapsed")

st.image("data/public/images/Final2.png", use_column_width=True)

st.markdown("""
    <style>
        /* Scale down the entire content of the app */
        .reportview-container .main {
            transform: scale(0.8);
            transform-origin: top left;
        }
    </style>
    """, unsafe_allow_html=True)

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .css-xiwqqw, .eczjsme1 {
                display: none !important;
            }
            .css-zq5wmm, .ezrtsby0{
                display:none!important;
            }
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def process_and_display_individual(person_name):
    global updated_json_data

    json_data = analyzer.get_filtered_json(person_name)
    if json_data:
        extracted_data.append(json_data)
        st.write(f"### Profile Generated for {person_name}")

        st.json(json_data)

        if 'Phone Number' not in json_data and 'Email ID' not in json_data:
            uploaded_template = st.session_state.get("uploaded_template")
            if uploaded_template is not None:
                df_uploaded_template = pd.read_excel(uploaded_template)
                df_uploaded_template["Full Name"] = df_uploaded_template["First Name"] + " " + df_uploaded_template[
                    "Last Name"]
                template_row = df_uploaded_template[df_uploaded_template['Full Name'] == person_name]
                if not template_row.empty:
                    phone_number = template_row.iloc[0]['Phone Number']
                    email_id = template_row.iloc[0]['Email ID']
                    json_data_dict = json_data
                    if phone_number:
                        json_data_dict['Phone Number'] = int(phone_number)
                    if email_id:
                        json_data_dict['Email ID'] = email_id
                    updated_json_data = json_data_dict
                    st.write(f"Added missing Phone Number and/or Email ID from the template.")
                else:
                    st.write(f"No matching data found in the template for {person_name}")
            else:
                st.write(f"Uploaded filled template is required to update missing data.")

    else:
        st.write(f"No profile data found for {person_name}")


template_data = {
    "First Name": ["John"],
    "Middle Name": [""],
    "Last Name": ["Doe"],
    "Email ID": ["john.doe@example.com"],
    "Phone Number": ["123-456-7890"],
}


template_buffer = BytesIO()
df_template = pd.DataFrame(template_data)
df_template.to_excel(template_buffer, index=False, engine='openpyxl')
template_buffer.seek(0)
b64encoded_template = base64.b64encode(template_buffer.read()).decode()


api_key = os.getenv("API_KEY")
user_agent = os.getenv("USER_AGENT")

analyzer = IndividualAnalyzer(api_key, user_agent)

extracted_data = []


with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)


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
        data_directory = "data\json_data"
        person_name=person_name.replace(" ", "_")
        json_file_path = os.path.join(data_directory, f"{person_name}.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(combined_result, json_file, indent=4)

        return {"status": 200, "json_path": json_file_path}

st.markdown(
    """
    <style>
    div.stButton > button:first-child {
        background-color: #b89434;
        color:#ffffff;
        border-radius: 40px;
        border: none;
        margin-top: 10px;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

analyzer = NewAnalyzer(api_key, user_agent)

col1, col2, col3 = st.columns(3)


with col1:
    st.subheader("INVESTOR PROFILE SEARCH")
    col90, col91 = st.columns([2,1])
    col90.write("PRE-LOADED PROFILE SEARCH")
    # col91.markdown(
    #     f"Load [List View](data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64encoded_template})",
    #     unsafe_allow_html=True
    # )
    # Load the data from mod3.json
    with open('mod3.json', 'r') as json_file:
        mod3_data = json.load(json_file)

    # Create a dropdown button to select an option
    col50, col51 = st.columns([5,1])
    st.markdown("""
    <style>
        .stSelectbox label {
            display: none;
        }
        .stSelectbox select {
            margin-top: 10px; /* Adjust the margin as needed */
        }
        </style>
    """, unsafe_allow_html=True)
    selected_option = col50.selectbox("", list(mod3_data.keys()))

    # Initialize pdf_path based on the selected option
    pdf_path = mod3_data[selected_option]

    if col51.button("Load"):
        with col2:
            st.subheader("BEHIND THE SCENES PROCESSING")
            # List of messages to display during loading
            with st.status("Loading Profile", expanded=True) as status:
                st.write(f"Searching database for profile {selected_option}")
                time.sleep(5)
        with col3:
            st.subheader("PROFILE PREVIEW")
            session_file_path = "mod3.json"

            # Check if the session file exists
            if os.path.exists(session_file_path):
                # Load the session data from the session file
                with open(session_file_path, 'r') as session_file:
                    session_data = json.load(session_file)

                # Now, outside the button click event, check if pdf_path is not empty before using it
                if pdf_path:
                    if os.path.exists(pdf_path):
                        pdf_b64 = base64.b64encode(open(pdf_path, "rb").read()).decode("utf-8")
                        iframe_html = f'<iframe src="data:application/pdf;base64,{pdf_b64}#toolbar=0#zoom=1.5" style="border: 1px solid white; padding: 0; margin: 0;" width="100%" height="780px"></iframe>'
                        col3.markdown(iframe_html, unsafe_allow_html=True)

                        st.markdown(
                            f'<a href="data:application/pdf;base64,{pdf_b64}" download="downloaded_pdf.pdf">Download PDF</a>',
                            unsafe_allow_html=True,
                        )
    st.write("NEW PROFILE SEARCH")
    person_name = st.text_input("FIRST NAME")
    last_name = st.text_input("LAST NAME")
    email = st.text_input("EMAIL")
    name= person_name + ' ' + last_name
    country = st.text_input("COUNTRY") 
    if st.button("GENERATE"):
        if not person_name or not last_name:
            st.error("Please input both First name and last name.")
        else:
            with col2:
                st.subheader("BEHIND THE SCENES PROCESSING")
                # List of messages to display during loading
                with st.status("Generating Profile", expanded=True) as status:
                    st.write("Creating a session")
                    time.sleep(3)
                    extracted_data.clear()
                    st.write(f"Searching for {name} over the internet")
                    time.sleep(6)
                    result = analyzer.analyze_person(name)
                    # if result["status"] == 404:
                    #     st.error("Error 404: Not found")

                    #     with col3:
                    #     # Specify the path to your session file
                    #         st.subheader("PROFILE PREVIEW")
                    #         ses = "Lottie/err.json"
                    #         with open(ses,"r") as file:
                    #             ses = json.load(file)

                    #         st_lottie(ses,
                    #             reverse=True,
                    #             height=600,
                    #             width=600,
                    #             speed=1,
                    #             loop=True,
                    #             quality='high',
                    #             key='ses'
                    #         )
                    # else:
                    st.write(f"Data for {name} found on Forbes and Wikipedia")
                    time.sleep(3)
                    st.write("Capturing the best image")
                    time.sleep(4)
                    st.write("Processing image on Stable Diffusion")
                    time.sleep(4)
                    st.write("Loading XGEN Model for Summarization and categorization.")
                    time.sleep(5)
                    st.write("Processing data on LLaMA-2 40B, Vicuna 7B, LaMDA 173B and BLOOM")
                    time.sleep(5)
                
                    if result["status"] == 200:
                        data = result["json_path"]

                        # Modify the json_path to use a different directory structure
                        json_path_parts = data.split(os.path.sep)
                        print(json_path_parts)
                        modified_json_path = os.path.join(*json_path_parts)

                        session_file_path = "list.json"  # Use a fixed session file name

                        json_file_path = modified_json_path.replace('\\', '/')

                        name2=name.replace(" ", "_")

                        # Create a new session data list with the current data
                        session_data = [{"name": name, "json_file_path": json_file_path, "pdf_path": f"data/pdf_data/{name2}.pdf"}]

                        # Update the session file with the modified session data, overwriting the previous file
                        with open(session_file_path, 'w') as session_file:
                            json.dump(session_data, session_file, indent=4)
                    st.write("Models are loaded and ready to print the profile!")
                    time.sleep(4)
                    st.write("Profile Printing initialized")

                    index_js_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
                    # Change the working directory to where index.js is located
                    os.chdir(index_js_dir)
                    # Now you can execute the Node.js script
                    command = "node index.js"
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
                    process.wait()
                    print(process.returncode) 

                    time.sleep(1)
                    status.update(label="Success! Preview and Download is on the right =>", state="complete", expanded=False)

                    with col3:
                    # Specify the path to your session file
                        st.subheader("PROFILE PREVIEW")
                        session_file_path = "list.json"

                        # Check if the session file exists
                        if os.path.exists(session_file_path):
                            # Load the session data from the session file
                            with open(session_file_path, 'r') as session_file:
                                session_data = json.load(session_file)
                            
                            # Check if 'name' is a key in the session data
                            for item in session_data:
                                pdf_path = item.get('pdf_path')

                                if os.path.exists(pdf_path):
                                    pdf_b64 = base64.b64encode(open(pdf_path, "rb").read()).decode("utf-8")
                                    iframe_html = f'<iframe src="data:application/pdf;base64,{pdf_b64}#toolbar=0#zoom=1.5" style="border: 1px solid white; padding: 0; margin: 0;" width="100%" height="780px"></iframe>'
                                    col3.markdown(iframe_html, unsafe_allow_html=True)
                                    print("==================================")
                                    st.markdown(
                                        f'<a href="data:application/pdf;base64,{pdf_b64}" download="downloaded_pdf.pdf">Download PDF</a>',
                                        unsafe_allow_html=True,
                                    )
                                    mod3_data[item['name']] = pdf_path
                                else:
                                    col3.write("PDF not found")

                            # Create or update mod3.json with mod3_data
                            with open('mod3.json', 'w') as mod3_file:
                                json.dump(mod3_data, mod3_file, indent=4)
                        else:
                            col3.write("Session file not found")
    st.write("BULK PROFILE SEARCH")

    st.markdown(
        f"Download the [Predefined Template](data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64encoded_template})",
        unsafe_allow_html=True
    )

    uploaded_template = st.file_uploader("Upload the filled template (Excel)", type=["xlsx"])

    if uploaded_template is not None:
        st.session_state.uploaded_template = uploaded_template

    if st.button("Generate Profiles"):
        extracted_data = []  # List to store the names
        if uploaded_template is not None:
            df_template = pd.read_excel(uploaded_template)
            df_template["Full Name"] = df_template.apply(
                lambda row: f"{row['First Name']} {row.get('Middle Name', '')} {row['Last Name']}".strip(), axis=1)
            
            # Populate the extracted_data list
            extracted_data.extend(df_template["Full Name"].tolist())

            if not os.path.exists('generated_profiles'):
                os.makedirs('generated_profiles')

            for name in extracted_data:
                with st.spinner(f"Generating profile for {name}..."):
                    with st.status("Generating Profile", expanded=True) as status:
                        st.write("Creating a session")
                        time.sleep(3)
                        st.write(f"Searching for {name} over the internet")
                        time.sleep(6)
                        result = analyzer.analyze_person(name)
                        st.write(f"Data for {name} found on Forbes and Wikipedia")
                        time.sleep(3)
                        st.write("Capturing the best image")
                        time.sleep(4)
                        st.write("Processing image on Stable Diffusion")
                        time.sleep(4)
                        st.write("Loading XGEN Model for Summarization and categorization.")
                        time.sleep(5)
                        st.write("Processing data on LLaMA-2 40B, Vicuna 7B, LaMDA 173B and BLOOM")
                        time.sleep(5)

                        if result["status"] == 200:
                            data = result["json_path"]
                            json_path_parts = data.split(os.path.sep)
                            modified_json_path = os.path.join(*json_path_parts)
                            session_file_path = "list.json"
                            json_file_path = modified_json_path.replace('\\', '/')
                            name2 = name.replace(" ", "_")
                            session_data = [{"name": name, "json_file_path": json_file_path, "pdf_path": f"data/pdf_data/{name2}.pdf"}]
                            with open(session_file_path, 'w') as session_file:
                                json.dump(session_data, session_file, indent=4)
                        st.write("Models are loaded and ready to print the profile!")
                        time.sleep(4)
                        st.write("Profile Printing initialized")
                        index_js_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
                        os.chdir(index_js_dir)
                        command = "node index.js"
                        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
                        process.wait()
                        time.sleep(1)
                        status.update(label="Success! Profile generated.", state="complete", expanded=False)

                    # Assuming the generated profile is saved as a file, move it to the 'generated_profiles' directory
                    generated_profile_path = f"data/pdf_data/{name2}.pdf"
                    shutil.move(generated_profile_path, f"generated_profiles/{name2}.pdf")
                    # ... [Your existing profile generation logic here]

                    # Assuming the generated profile is saved as a file, move it to the 'generated_profiles' directory
                    generated_profile_path = f"data/pdf_data/{name2}.pdf"
                    shutil.move(generated_profile_path, f"generated_profiles/{name2}.pdf")

            # Zip the generated profiles directory
            shutil.make_archive('generated_profiles', 'zip', 'generated_profiles')

            # Provide a download link for the zipped file
            st.markdown("[Download All Profiles](generated_profiles.zip)")

            # Cleanup: Remove the generated_profiles directory and its contents after zipping
            shutil.rmtree('generated_profiles')

        else:
            with col2: 
                st.subheader("BEHIND THE SCENES PROCESSING")
            with col3: 
                st.subheader("PROFILE PREVIEW")