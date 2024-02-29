# Doc-IT-Right - Capstone Project 👨‍⚕️
#### Fall Semester 2023/2024

##
### Table of contents

1. [Project Description](#proj_desc)
  1.1 [Main Technologies Used](#main_tech)
  1.2 [Main Challenges Faced](#main_chal)
2. [Repository Description](#rep_desc)
3. [How to Use](#proj_use)
   3.1. [How to Interact with our Chatbot](#chat_int)
4. [Credits](#credits)
5. [License](#license)
6. [References](#ref)
##

<a name="proj_desc"></a>
## Project Description

Our project comes in the sense of a university course - Capstone Project - on our final year of a Bachelor's Degree in Data Science at Nova IMS.

Our fictional company, Doc-IT-Right,  is part of the consultancy sector. However, it falls under the health sector, as it intends to provide a solution for the scheduling and management of appointments in different medical specialties of a medical clinic. 

Our project aims to develop an interface that allows the management of a medical office, including a website with information about the company (https://docitrightcp.wixsite.com/doc-it-right) and also a chatbot that will directly interact with the patient, clarifying all of its doubts. In addition, a predictive model was also developed to predict which appointments were more likely to be missed by patients, having a final accuracy of 80% (as well as the same value for the weighted f1-score); therefore, empowering clinics to better manage their schedules (possibly contacting the patient as a reminder of the appointment or confirming if it is still coming).

Our mission is to guarantee that clinics can deliver the best service to their patients, in the most effective way possible. This software will open up the possibility of increasing the quality of medical service with less or equal resources. By effectively organizing data, doctors and other collaborators can dedicate their time to other more complex and important actions, that will benefit patients in a great way, instead of spending time with routine, basic and repetitive actions that can be performed by this software.

This way, and in a country where there is such a great qualified labour but not so much quantity of it, we aim to get the best out of the available workforce, challenging them into new, more rewarding tasks, and manage them into success and contentment of patients that can, in this way, have better medical care and see their doubts quickly resolved.

<a name="main_tech"></a>
### - What main technologies were used in the development of this project?
For this project, the main goal was to create an AI-powered Question Answer System which would engage with fictional customers - in our case patients of medical clinics. This would be the primary communication channel of our business - being able to offer services to customers (easily managing appointments, answering patient's medical specialities, as well as their medication doubts; giving the predictions of which appointments are more likely to be missed to clinics) through a conversational app. 

With this project, we were able to explore more in-depth how to make use of LLM models, from OpenAI, in different problems (with Python being the chosen programming language) - through the development of a chatbot that is able to perform appointment scheduling actions, solve patient doubts and predict which appointments are more likely to be missed. Furthermore, the team learned how to create an application using Streamlit and a website on WIX.

<a name="main_chal"></a>
### - What were the main challenges faced? 
The main challenges faced during the development of this project were related with:
- Team's limited budget in OpenAi - using and interacting with the chat. Hence, there was a need to become more cautious and restrict some of the parts of the development stage;
- The chatbot required very specific instructions to ensure the correct outputs were obtained, which was an extremely time-consuming process (sort of trial and error);
- There was not enough time to predict, and consequently, code all the possible human-generated inputs. However, that is something that can be improved with time and user's help/reviews.

<a name="rep_desc"></a>
##
## Repository Description
This repository contains all the files created during the development of our project. In the following paragraphs will be a short description of how the repository is organized and what each file contains:
- [Prompts folder](Prompts): contains all the links that lead to the chats where the prompts were fed into the LLM (in our case, ChatGPT) to obtain - company definition (company name, problem, value proposition, core values, mission, vision, tag line, personas), marketing (discussion of pros and cons of reviews from competitor companies, blog posts creation, pitch script, 5-post social media campaign, Instagram post captions), timetable scheduling and patient data generator prompts.
- [No Show Prediction](No_show_prediction): this is a folder that contains two Jupyter notebooks, one containing the development of a predictive model for no-show appointments and another where the data needed for this task are properly treated.
- [Website](Website): this folder contains all the needed files for the chatbot application, on Streamlit, to work properly.
- [Prompt Template](Website/info_files/prompt_list.py):  this file contains the template prompts fed into the model (it is stored inside of info_files in the Website folder). 
- [Requirements](requirements.txt): file that specifies the dependencies and the versions that need to be installed in the environment for the project to be run.
- [Use Cases](use_cases.pdf): this file contains practical examples of scenarios in which our chatbot application can be helpful to clients of our company - appointment scheduling, appointment rescheduling, appointment cancellations, clarifying medical doubts, and predictive model.
- [Five Questions](five_questions.md): this file contains practical examples of questions that can be asked to our chatbot, in which it requires it to go retrieve the information to our text data (pdf file with the medicine information leaflets).
- [Data Description](data_description.txt): this text file contains the description and the metadata of all the used data in our project.
- [Git Ignore](.gitignore): this file specifies patterns of files and directories that should be excluded from the version control of our repository.
- [README](README.md): file that contains the basic instructions of how to run the project, the motivations behind it and its features.
- [LICENSE](LICENSE.md): this is a file that contains the chosen license for this project.

##
<a name="proj_use"></a>
## How To Use the Project. How to Install and Run the Project
Our project was divided into two main parts: informative website on WIX (https://docitrightcp.wixsite.com/doc-it-right) and the Streamlit app. Hence, the following steps need to be taken to ensure that the chatbot interface can be correctly accessed:
- Retrieve code from this GitHub Repository (`Fork` and then `Git Clone`)
- Download the folder (data.zip), sent by email, with the credentials (credentials to be able to use the Google Calendar platform) and tokens (contains authorization tokens used to authenticate and authorize access when declaring the specified scope). Please unzip this folder before moving on to the next step.
- Download the .env file (should be stored inside of the Capstone folder only), sent by email (which also contains our `API-key` - it is advisable to change to your own OpenAI API-key; the `DATA_PATH` should also be substituted to the local path of the data folder you just downloaded from the email. Please note that the end of the path should be `//`).
- Afterwards, inside the `No-show prediction` folder - in this GitHub repository, there is a need to change in both notebooks the path for your local path to the data (Please note that the end of the path should be `//`).
- There's also a need to run the requirements.txt file so that the environment is in the same conditions as the development environment was.

Finally, to run the Streamlit app: go inside the terminal, and open the [`Website`](Website) folder  (which is inside the capstone folder/repository). When that is done, run the following command `streamlit run main.py`.

<a name="chat_int"></a>
### How to interact with our chatbot
Our chatbot is capable of handling different formats of inputs. However, in order to obtain the most correct result the following structure of inputs shall be followed (the format presented will be "question that the chatbot will ask" | "your answer format"):
- Date | YYYY-MM-DD (e.g.: 2024-01-07)
- Time | HH:MM:SS (e.g.: 10:30:00)
- Email | Needs to be in email format, but other than that it does not have restrictions (e.g.: doc.it.right.cp@gmail.com)
- Doctor | The name needs to be correctly written - the names of the available doctors can be seen in the schedule tab of our chatbot application (e.g.: Dr. José Dias).
- Parking Spot | `Yes` or `No` answers only
- Special Requests | Either `No` or state any special request that you desire (e.g.: "I want a wheelchair")
- Payment in Advance | Integer Number between 0 and 100

The results of the predictive model for each appointment can be verified in the event scheduled in the clinic's calendar. Furthermore, they are also stored at Doc-IT-Right's database (along with the patient's personal information and the remaining appointment data).

Afterwards, you can have fun interacting with our Dr. Chatbot 🥳.

<a name="credits"></a>
## 
#### Project Developed by:
- Bruna Faria | [LinkedIn](https://www.linkedin.com/in/brunafdfaria/)
- Catarina Oliveira | [LinkedIn](https://www.linkedin.com/in/cjoliveira96/)
- Inês Vieira | [LinkedIn](https://www.linkedin.com/in/inesarvieira/)
- Joana Rosa | [LinkedIn](https://www.linkedin.com/in/joanarrosa/) 
- Rita Centeno | [LinkedIn](https://www.linkedin.com/in/rita-centeno/)
##
##

<a name="license"></a>
## License
This project is licensed under the [GNU AGPLv3] - see the [LICENSE.md](LICENSE.md) file for details.
##

<a name="ref"></a>
## References
Here are some of the most important contents our team checked during the development of the project:
- OpenAI. (2023). ChatGPT (Jan 7 version) [Large language model](https://chat.openai.com/chat)
- [Streamlit App Design - 1](https://github.com/Ashwani132003/pondering)
- [Streamlit App Design - 2](https://github.com/hamagistral/de-zoomcamp-ui/blob/master/streamlit/01_%F0%9F%91%A8%E2%80%8D%F0%9F%94%A7_DE_Zoomcamp_2023.py)
- [Streamlit Components](https://streamlit.io/components?category=widgets)
- [Additional Streamlit Components](https://docs.streamlit.io/library/api-reference/widgets/st.multiselect)
- [How to deploy the application](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [Schedule Chatbot Option](https://www.pragnakalp.com/how-to-use-openai-function-calling-to-create-appointment-booking-chatbot/)
- [Chatbot Langchain Memory](https://stackoverflow.com/questions/76240871/how-do-i-add-memory-to-retrievalqa-from-chain-type-or-how-do-i-add-a-custom-pr)
