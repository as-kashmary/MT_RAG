from ollama import Client

class QueryClassifier:
    def __init__(self, query):
        self.llm=Client(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer 7efd7a1ff40e4dc5b8d19692d5f65af6.9WjyQeyPv2gcmkChoa-MQjxe' }
        )
        # deepseek-v3.1:671b-cloud
        # gpt-oss:20b-cloud
        # gpt-oss:120b-cloud
        # kimi-k2:1t-cloud
        # qwen3-coder:480b-cloud
        # glm-4.6:cloud
        # minimax-m2:cloud

        self.query=query

        prompt=f"""Classify the following query into one of these categories: Factual, Analytical, Opinion, or Contextual. You don't have to provide explanation.\nQuery: {self.query}\nCategory:"""
        messages = [
            {
                'role': 'user',
                'content': prompt,
            },
        ]
        response = ""
        for part in self.llm.chat('kimi-k2:1t-cloud', messages=messages, stream=True):
            # Get the latest content chunk
            chunk = part['message']['content']
            # print(chunk, end='', flush=True)  # Print as it streams
            response += chunk  # Accumulate
        
        # Strip at the end
        response = response.strip()
        # print(f"This is the response: {response}")
        self.response=response



    def classification(self):
        # print("clasiffying query")
        return str(self.response)