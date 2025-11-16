from ollama import Client

class ResponseGenerator:
    def __init__(self, query, context):
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
        self.context=context

        prompt=f"""
        Using the following context, provide a detailed and informative answer to the query. 
        If the context does not contain relevant information, respond with 'Insufficient information to answer the query.'\nContext: {self.context}\nQuery: {self.query}\nAnswer:"""
        print(prompt)
        
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



    def generation(self):
        # print("clasiffying query")
        return str(self.response)