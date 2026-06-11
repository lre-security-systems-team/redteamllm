from openai import OpenAI, pydantic_function_tool

from termcolor import colored
import json
from pydantic import BaseModel, Field
import requests 
from bs4 import BeautifulSoup
from subproc import exec_cmd

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
    
    return search_results[:5]  # Return the first 5 links

web_search_tool = {
    'type': 'function',
    'function': {
        'name': 'search_web',
        'description': 'Search the web and return search results',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The search query to execute, e.g \'python web scraping examples\''
                },
            },
            'required': [
                'query',
            ],
            'additionalProperties': False
        },
        'strict': True
    }
}



with open("../../api_key") as f:
    api_key = f.read().strip()
client = OpenAI(api_key=api_key)



exec = {
    "type": "function",
    "function": {
        "name": "exec_cmd",
        "description": "Execute a command on a linux terminal with all the rights",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The full command to be executed in the terminal, e.g 'echo toto', 'for e in 1 2 3; do echo $e; done', ..."
                },
            },
            "required": [
                "command",
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}

tools = [exec]
tools.append(web_search_tool)


messages = []

developer_msg = {
    "role": "developer",
    "content": "You are an autonomous agent that will have complete access to a linux terminal with all the rights. You will be given a task and need to complete it. You need to be fully autonomous in your actions"
}

user_msg = {
    "role" : "user",
    "content": input("enter your task:\n")
}
messages.append(developer_msg)
messages.append(user_msg)


while True:

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages= messages,
        tools=tools
    )


    tool_calls = completion.choices[0].message.tool_calls
    messages.append({"role":"assistant","content":completion.choices[0].message.content,"tool_calls":tool_calls})

    print(colored(f"Agent:\n{completion.choices[0].message.content}",'blue'))
    print(colored(f"TOTAL TOKEN {completion.usage.to_dict()}"))
    print(colored(f"Tool calls: \n {tool_calls}",'green'))


    if not tool_calls:
        message = input("User:\n")
        messages.append({"role":"user","content":message})
        continue


    for tool_call in tool_calls:
        args =json.loads(tool_call.function.arguments) 
        if tool_call.function.name == "exec_cmd":
            results = exec_cmd(**args)
        else:
            results = search_web(**args)
        messages.append({"role":"tool","tool_call_id":tool_call.id,"content":results})

        

        print(colored(f"CMD executed'{tool_call.function.arguments}'\nResult:\n{results}",'red'))



    


