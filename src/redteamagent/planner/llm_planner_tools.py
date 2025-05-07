from .llm_planner import LLMPlanner,register
from ..execution_tree import ExecutionNode
from termcolor import colored



@register({
    "type":"function",
    "function":{
    "name":"decompose_task",
    "description": "return the decomposition of a task into multiple subtasks, or the task it self if no decomposition (passing null)",
    "parameters":{
        "type":"object",
        "properties":{
            "task_list" :{
                "type" : ["array","null"],
                "items":{
                    "type":"string"
                },
                "description" :"A list of subtasks (1 to 5 max), or null if no need for decomposition"
            }
        }
    }
    }
},LLMPlanner)
def decompose_task(task_list:list[str]) -> str:
    if task_list == None:
        # marking result of task decomposition
        LLMPlanner.llm_plan_result= None
        print(colored("No decomposition","red"))
        return "success"
    first = ExecutionNode(task_list[0])
    prev = first
    for e in range(1,len(task_list)):
        act = ExecutionNode(task_list[e])
        prev.next_node = act
        prev = act
    LLMPlanner.llm_plan_result = first 
    print(colored("DECOMPOSITION:","red"))
    for e in task_list:
        print(colored(f" - {e}","red"))

    return "success"