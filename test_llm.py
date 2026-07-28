from llm import generate_answer

context = """
Employees receive 20 annual leaves every year.
"""

question = "How many annual leaves do employees receive?"

answer = generate_answer(question, context)

print(answer)