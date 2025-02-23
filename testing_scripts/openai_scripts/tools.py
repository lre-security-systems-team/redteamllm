from openai import OpenAI, pydantic_function_tool

from termcolor import colored
import json
from pydantic import BaseModel, Field
from subproc import exec_cmd



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
    print(colored(f"Tool calls: \n {tool_calls}",'green'))


    if not tool_calls:
        message = input("User:\n")
        messages.append({"role":"user","content":message})
        continue


    for tool_call in tool_calls:
        args =json.loads(tool_call.function.arguments) 
        results = exec_cmd(**args)
        messages.append({"role":"tool","tool_call_id":tool_call.id,"content":results})

        

        print(colored(f"CMD executed'{tool_call.function.arguments}'\nResult:\n{results}",'red'))



    
