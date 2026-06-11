import subprocess
from typing import Optional
import json
from openai import OpenAI, pydantic_function_tool

import requests 
from bs4 import BeautifulSoup

def exec_cmd(command):
    res = subprocess.run(command,shell=True,capture_output=True)

    return f"stdout = {res.stdout.decode('utf-8')}\nstderr={res.stderr.decode('utf-8')}"


def search_web(query: str):
    """Perform a web search and return the first few results"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(f'https://www.google.com/search?q={query}', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract search result links
    search_results = []
    for g in soup.find_all('div', class_='r'):
        anchors = g.find_all('a')
        if anchors:
            link = anchors[0].get('href')
            search_results.append(link)
    
    return search_results  # Return the first 5 links


# with open("../../api_key") as f:
#     api_key = f.read().strip()
# client = OpenAI(api_key=api_key)

# developer_msg = {
#     "role": "developer",
#     "content": "You are an autonomous agent that will have complete access to a linux terminal with all the rights. You will be given a task and need to complete it. You need to be fully autonomous in your actions"
# }

# user_msg = {
#     "role" : "user",
#     "content": "hello"
# }
# messages = []
# messages.append(developer_msg)
# messages.append(user_msg)
# completion = client.chat.completions.create(
#     model="gpt-4o",
#     messages= messages,
# )






def call(*argv, **kwargs):
    def call_fn(function):
        return function(*argv,**kwargs)
    return call_fn

@call(5)
def print_n(n):
    return n +5


a = print_n
print(a)