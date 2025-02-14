import streamlit as st
from groq import Groq
from linkedin_scraper import Person
from selenium import webdriver

# Streamlit UI
st.title("LinkedIn Profile Analyzer")

# Input fields
api_key = st.secrets["GROQ_API_KEY"]
li_at_cookie = st.secrets["LI_AT_COOKIE"]
profile_url = st.text_input("Enter the LinkedIn Profile URL")

# Initialize session state for caching responses
if "cached_responses" not in st.session_state:
    st.session_state.cached_responses = {}

def authenticate_linkedin(cookie):
    """Authenticate with LinkedIn using Selenium and return a WebDriver session."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.linkedin.com")
    driver.add_cookie({"name": "li_at", "value": cookie, "domain": ".linkedin.com"})

    return driver

def get_profile_data(driver, profile_url):
    """Retrieve profile data from LinkedIn."""
    try:
        person = Person(profile_url, driver=driver)
        return {
            "name": person.name,
            "headline": person.about,
            "summary": person.about,
            "experience": person.experiences,
            "education": person.education,
            "skills": person.skills
        }
    except Exception as e:
        st.error(f"Failed to retrieve LinkedIn profile: {e}")
        return None

def generate_responses(client, profile_data):
    """Generate analysis responses and store them in session state."""
    full_profile_text = f"""
    Analyze the following LinkedIn profile:
    Name: {profile_data.get('name', '')}
    Headline: {profile_data.get('headline', '')}
    Summary: {profile_data.get('summary', '')}
    Experience: {profile_data.get('experience', '')}
    Education: {profile_data.get('education', '')}
    Skills: {profile_data.get('skills', '')}
    """

    prompts = {
        "General Analysis": "Provide a structured, professional analysis of this LinkedIn profile.",
        "Experience": "Analyze the user's work experience, highlighting achievements and roles.",
        "Research": "Evaluate the research background, focusing on publications and contributions.",
        "Leadership & Entrepreneurship": "Analyze leadership roles and entrepreneurial efforts."
    }

    # Generate responses only if not cached
    if not st.session_state.cached_responses:
        for category, prompt in prompts.items():
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": prompt},
                          {"role": "user", "content": full_profile_text}],
                max_tokens=500,
                temperature=1.2,
            )
            st.session_state.cached_responses[category] = response.choices[0].message.content

def display_analysis():
    """Display cached analysis results."""
    analysis_type = st.radio("Choose analysis type", list(st.session_state.cached_responses.keys()))
    st.subheader(f"{analysis_type} Analysis")
    st.write(st.session_state.cached_responses.get(analysis_type, "No analysis available yet."))

# Main execution flow
if api_key and li_at_cookie and profile_url:
    driver = authenticate_linkedin(li_at_cookie)
    
    if driver:
        profile_data = get_profile_data(driver, profile_url)
        st.write(profile_data)
        
        if profile_data:
            # Initialize Groq client
            client = Groq(api_key=api_key)
            
            # Generate and cache responses
            generate_responses(client, profile_data)
            
            # Display analysis
            display_analysis()
else:
    st.warning("Please enter all required information.")
