import streamlit as st
from groq import Groq
from linkedin_api import Linkedin  # Install linkedin-api-python if needed

# Streamlit UI
st.title("LinkedIn Profile Analyzer")

# Input fields
api_key = st.secrets["GROQ_API_KEY"]
li_at_cookie = st.secrets["LI_AT_COOKIE"]
linkedin = Linkedin(cookie=li_at_cookie)
profile_url = st.text_input("Enter the LinkedIn Profile URL")

# Initialize session state for caching responses
if "cached_responses" not in st.session_state:
    st.session_state.cached_responses = {}

def authenticate_linkedin(cookie):
    """Authenticate with LinkedIn and return a session object."""
    return Linkedin(cookie=cookie)    

def get_profile_data(linkedin, profile_url):
    """Retrieve profile data from LinkedIn."""
    try:
        profile_id = profile_url.split("/")[-2]  # Extract profile ID from URL
        return linkedin.get_profile(profile_id)
    except Exception as e:
        st.error(f"Failed to retrieve LinkedIn profile: {e}")
        return None

def generate_responses(client, profile_data):
    """Generate analysis responses and store them in session state."""
    full_profile_text = f"""
    Analyze the following LinkedIn profile:
    Name: {profile_data.get('firstName', '')} {profile_data.get('lastName', '')}
    Headline: {profile_data.get('headline', '')}
    Summary: {profile_data.get('summary', '')}
    Experience: {profile_data.get('experience', '')}
    Education: {profile_data.get('education', '')}
    Skills: {profile_data.get('skills', '')}
    """

    prompts = {
        "General Analysis": "You are a LinkedIn profile analyzer. Provide a holistic and insightful analysis of the user's profile, covering key strengths, experiences, and skills. Keep the response structured and professional, highlighting the most relevant aspects succinctly.",
        "Experience": "You are a LinkedIn profile analyzer looking for people specifically regarding their experiences. Keep your analysis brief and concise but detailed. Maintain objectivity and format it in such a way that each experience is given a brief but detailed description (including numbers, action words, etc) of things this person has done.",
        "Research": "You are a profile analyzer in evaluating research backgrounds. Analyze the profile with a focus on academic and industry research experience. Highlight key publications, research projects, and contributions to the field. Format the response to emphasize major achievements and areas of expertise.",
        "Leadership & Entrepreneurship": "You are a profile analyzer that evaluates leadership and entrepreneurial qualities. Analyze the profile based on leadership roles, initiatives taken, and entrepreneurial endeavors. Emphasize strategic decision-making, team management, and impact created. Format the response with clear sections on leadership experiences and entrepreneurial ventures."
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
    linkedin = authenticate_linkedin(li_at_cookie)
    
    if linkedin:
        profile_data = get_profile_data(linkedin, profile_url)
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
