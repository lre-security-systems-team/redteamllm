from src.llm.llm_wrapper import LLM, register


@register({
    "type": "function",
    "function": {
        "name": "say_hello",
        "description": "say hello",
            "required": [
                "command",
            ],
            "additionalProperties": False
        },
        "strict": True
    }
)
def say_hello():
    return "hello"

@register({
    "type": "function",
    "function": {
        "name": "say_by",
        "description": "say by",
            "required": [
                "command",
            ],
            "additionalProperties": False
        },
        "strict": True
    }
)
def say_by():
    return "by"

a = LLM(api_key="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",model_name="gpt-4o")

print(a.send_process_prompt("great me than say goodby"))
print("tool call count: ",a.tool_call_count)
print("token input count: ",a.total_input_tokens)
print("token completion count: ",a.total_completion_tokens)
print("token total  count: ",a.total_tokens)



