import ollama

r = ollama.chat(model='llama3.2:3b', messages=[{'role':'user', 'content':'한 줄로 자기소개'}])
print(r['message']['content'])