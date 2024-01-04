
"""
ChatBot classes
"""

import random
from openai import OpenAI
from util import local_settings

# OpenAI API ------------------------------------------------------------------------------------------------------------------------------------
class GPT_Helper:
    def __init__(self, OPENAI_API_KEY: str, system_behavior: str="", functions: list=None, model="gpt-3.5-turbo"):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.messages = []
        self.model = model

        if system_behavior:
            self.messages.append({"role": "system", "content": system_behavior})

        if functions:
            self.functions = functions

    def langchain_process(self, prompt):
        docs = self.document_searcher.similarity_search(prompt)
        result = self.chain.run(input_documents=docs, question=prompt)
        return result
    

    # get completion from the model
    def get_completion(self, prompt, temperature=0, langchain=False):

        self.messages.append({"role": "user", "content": prompt})

        if not langchain:
            completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=temperature,
            tools=self.functions
        )
            if completion.choices[0].message.content:
                self.messages.append({"role": "assistant", "content": completion.choices[0].message.content})
                return completion.choices[0].message

        else:
           langchain_results = self.langchain_process(prompt)
           self.messages.append({"role": "assistant", "content": langchain_results})
           return langchain_results



# ChatBot ---------------------------------------------------------------------------------------------------------------------------------------

class ChatBot:
    """
    Generate a response by using LLMs.
    """

    def __init__(self, system_behavior: str, functions: list=None):
        self.__system_behavior = system_behavior
        self.__functions = functions

        self.engine = GPT_Helper(
            OPENAI_API_KEY=local_settings.OPENAI_API_KEY,
            system_behavior=system_behavior,
            functions=functions
        )

    def generate_response(self, message: str, langchain=False):
        return self.engine.get_completion(message, langchain=langchain)

    def __str__(self):
        shift = "   "
        class_name = str(type(self)).split('.')[-1].replace("'>", "")

        return f"🤖 {class_name}."

    def reset(self):
        self.engine = GPT_Helper(
            OPENAI_API_KEY=local_settings.OPENAI_API_KEY,
            system_behavior=self.__system_behavior,
            functions=self.__functions
    )

    @property
    def memory(self):
        return self.engine.messages

    @property
    def system_behavior(self):
        return self.__system_config

    @system_behavior.setter
    def system_behavior(self, system_config : str):
        self.__system_behavior = system_config




