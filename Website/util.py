
"""
A Python module for interacting with OpenAI's GPT models and managing settings.

This module includes classes for managing settings and interacting with OpenAI's GPT models.

Classes:
- `Settings`: A class for managing settings using Pydantic's BaseSettings.
- `GPT_Wrapper`: A class for interfacing with OpenAI's GPT models.
"""
from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import firebase_admin


# Settings --------------------------------------------------------------------------------------------------------------------------------------
class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(validation_alias="OPENAI_API_KEY")
    DATA_PATH: str = Field(validation_alias="DATA_PATH")


# Vars & Instances ------------------------------------------------------------------------------------------------------------------------------
"""
NOTE:

This code below is pivotal, especially in scenarios like `streamlit run`, where the Pydantic 
class BaseSettings might encounter difficulties loading environment variables.

The specific process within the code ensures the loading of these variables from the `.env` file.
This code segment employs the BaseSettings class from Pydantic to define settings, like the OPENAI_API_KEY.

The snippet also incorporates the loading of environment variables from the `.env` file, critical for 
scenarios where Pydantic may struggle with this process, ensuring smooth functionality, particularly in 
applications like streamlit run.
"""
_ = load_dotenv(find_dotenv())
if not _:
    _ = load_dotenv(".env")

local_settings = Settings()


# Google Calendar API ------------------------------------------------------------------------------------------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = Credentials.from_authorized_user_file(local_settings.DATA_PATH+'token.json', SCOPES)
service = build('calendar', 'v3', credentials=creds)


# Firebase API ------------------------------------------------------------------------------------------------------------------------------------

cred = firebase_admin.credentials.Certificate(local_settings.DATA_PATH+"doc-it-right-c4b0c-a8097b4fd708.json")

try:
    firebase_admin.get_app()

except ValueError:
    # Initialize the app if it hasn't been initialized yet
    firebase_admin.initialize_app(cred)


