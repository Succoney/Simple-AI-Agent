import asyncio
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Optional
import json
from mcp_client import MCPClient
import sys
import re
import json

MANGER_PROMPT = """#### Purpose  
This AI assistant is designed to break down a complex query into multiple step-by-step actions, and solve it efficiently using available tools, including web search and markdown file generation.  
The assistant must avoid executing multiple searches within a single step and instead structure the steps logically to progressively refine and process the gathered information.  
Each step must be classified into one of the following categories: search, summary, document, or chat.  
Each step should only belong to one category. If a search query is too broad or complex, the assistant should break it down into smaller tasks, ensuring that each step contains at most one search operation.

#### Task Category Definitions
- search: Use a web search to retrieve real-time or factual information from the internet. Corresponds to calling web_search(query: str) -> str.  
- summary: Summarize or extract key information from previously gathered content or dialogue context.  
- document: Generate a structured markdown document using markdown_generate(content: str, doc_name: str, save_path: str = "../doc/") -> str.  
- chat: Ask or respond to a conversational or reasoning question directed at the language model.  

#### Available Tools  
1. **Web Search** – web_search(query: str) -> str  
2. **Markdown File Generation** – markdown_generate(content: str, doc_name: str, save_path: str = "../doc/") -> str  

#### Output Format  
Each step should be formatted as ##stepX:, followed by a clear action and the corresponding task category.  
Only one task category per step.  

---

#### Example  

**Input Query:**  
"Create a 7-day travel itinerary for a trip to Japan and save it as a markdown file."  

**Response:**  
##step1: **search** Find out the most popular tourist attractions across major cities in Japan using online resources. 
##step2: **summary** Organize and summarize the key attractions into a list categorized by region or city.  
##step3: **search** Look up the most efficient travel routes and transportation options between those destinations.  
##step4: **summary** Create a daily travel plan based on the attractions and routes, ensuring logical flow and time balance.
##step5: **document** Compile the itinerary into a well-structured markdown file with day-by-day plans and travel notes, then save it.

---

#### Notes  
- Each step must be atomic and strictly assigned to one of the four task categories.  
- Do not mix responsibilities or tool types in a single step.  
- Prefer smaller, clearer steps over complex, combined actions.
"""

JUDGE_PROMPT = """
#### Role  
You are an AI assistant designed to help users evaluate whether their tasks have been successfully completed by a language model. The user will provide a conversation in the form of `messages`, which includes multiple interactions between the user and the AI model.

#### Objective  
For **each user input** in the provided messages, determine whether the model's corresponding response **correctly and completely fulfills** the user's request.

#### Output Format  
For each user message, output a dictionary with the following structure:
- `"result"`: Either `"Yes"` or `"No"`.
- `"reason"`: (Only required when result is `"No"`) A brief explanation of why the model's response did not fully satisfy the user request.


#### Evaluation Criteria  
- Check whether the model understood the user's intent.  
- Check whether the response directly and adequately addresses the user’s query.  
- Consider factual accuracy, completeness, and relevance.  
- Ignore minor language issues unless they affect the result.  

#### Input  
A list of `messages`, each with a `role` ("user" or "assistant") and a `content` string. You must pair each user message with the next assistant message that follows.

"""

CLASSIFY_PROMPT = """
# Role:
You are an intelligent assistant designed to classify user tasks into one of the following categories:

1. Search – Tasks that require retrieving real-time or factual information from the internet.
2. Summary – Tasks that ask to summarize the content from previous messages or a given context.
3. Document – Tasks that involve producing a formatted Markdown document based on user input or content.
4. Chat – Tasks where the user is engaging in open-ended conversation, asking questions, or seeking advice from the model.

# Instructions:
When the user gives you a task (either a command or a question), classify it into one of the four categories above.  
Your output should be **only one word**, exactly one of the following:

- "search"
- "summary"
- "document"
- "chat"

# Examples:

## Example 1:
User input: "Check who won the Nobel Prize this year."
Output: "search"

## Example 2:
User input: "Please summarize the previous conversation."
Output: "summary"

## Example 3:
User input: "Generate a Markdown report from the meeting notes I provide."
Output: "document"

## Example 4:
User input: "What do you think about the future of artificial intelligence?"
Output: "chat"

# Notes:
- Choose strictly based on the main intent of the user query.
- Return only the one-word label. Do not add explanations or extra text.
"""

BROWSER_PROMPT = """
# Role:
You are an AI assistant specialized in decomposing complex web search tasks into a sequence of atomic search queries. Each search query must be suitable for exactly one call to the following function:
web_search(query: str) -> str

# Goal:
When given a complex or multi-step web search task by the user, your responsibility is to break it down into individual, simple search queries that can be independently executed using one `web_search()` call each.

# Rules:
1. Each search query must be:
   - Specific and unambiguous
   - Focused on a single intent
   - Include all necessary context (dates, location, keywords, etc.)
2. If the original query includes general terms like "next week" or "tomorrow", you must first convert them into explicit dates before generating the search queries.
3. If the task requires intermediate steps (like finding out the current date), include those steps as well.
4. Do NOT perform the search. Only output the list of one-step search queries.
5. The output must be a list of strings, each representing a search query.

# Output Format:
Return a Python list of search query strings, like this:
[
    "Search query 1",
    "Search query 2",
    ...
]

# Example Input:
"Find out the weather forecast in Suzhou for the next two weeks."

# Example Output (assuming today is April 6):
[
    "What is today's date?",
    "Suzhou weather forecast from April 6 to April 19"
]

# Reminder:
Do not combine multiple intents in one search query. Each item in the list must correspond to a single, atomic use of the web_search function.
"""


class Agent:
    def __init__(self):
        load_dotenv("../config/config.env")
        self.base_url = os.getenv("base_url")
        self.api_key = os.getenv("api_key")
        self.model = os.getenv("model")
        self.client = OpenAI(base_url = self.base_url,api_key = self.api_key)
        self.messages = []
        self.mcp_client = MCPClient()
        self.step_num = 1

    async def planning(self, query : str, search_depth : int):
        messages = [{
            "role" : "system",
            "content" : MANGER_PROMPT.strip()
        },{
            "role" : "user",
            "content" : query
        },{
            "role" : "user",
            "content" : f"The number of steps after decomposition cannot exceed {2**(3-search_depth)}"
        }]

        response = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages,
                )

        print(response.choices[0].message.content)
        steps = response.choices[0].message.content.split("##")
        for index, step in enumerate(steps):
            print(step)
            if "step" not in step:
                continue

            step = step[7:]
            self.messages.append({
                "role" : "user",
                "content" : step,
            })
            done = await self.act(step)
            if done == False:
                await self.planning(step, 2 if search_depth == 2 else search_depth+1)
            else:
                # print(self.messages)
                self.step_num += 1
        
        with open("save.txt","w",encoding="utf-8") as f:
            for message in self.messages:
                f.write(str(message)+"\n")

    async def act(self, step : str) -> bool:
        if "**search**" in step.lower():
            await self.browser_act(step) 
        
        elif "**summary**" in step.lower():
            await self.summary_act(step)

        elif "**document**" in step.lower():
            await self.document_act(step)

        elif "**file**" in step.lower():
            await self.file_act(step)

        else:
            await self.chat_act(step)

        # response = await self.mcp_client.process_query(self.messages)

        # messages = [{
        #     "role" : "system",
        #     "content" : JUDGE_PROMPT
        # },{
        #     "role" : "user",
        #     "content" : str(response)
        # }]

        # judge = self.client.chat.completions.create(
        #             model = self.model,
        #             messages = messages,
        #         )

        # self.messages += response

        # if "yes" in judge.choices[0].message.content.lower():
        #     print(f"done!!!\n")
        #     return True
        # else:
        #     print(judge.choices[0].message.content.lower())
        #     print(f"fail!!!\n")
        #     return False

    async def browser_act(self, step : str, reflection : str = None) -> bool:

        messages = self.messages + [
            {
                "role" : "system",
                "content" : BROWSER_PROMPT.strip(),
            },
            {
                "role" : "user",
                "content" : step,
            }
        ]

        pattern = r'\[\s*.*?\s*\]'

        while True:
            try:
                response = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages
                )

                print(response.choices[0].message.content)

                match = re.search(pattern, response.choices[0].message.content, re.DOTALL)

                search_tasks = json.loads(match.group(0))

                break
            except Exception as e:
                print(str(e))
            

        print(search_tasks)

        for search in search_tasks:
            self.messages.append({
                "role" : "user",
                "content" : "User browser to search for " + search
            })
            response = await self.mcp_client.process_query(self.messages)

            self.messages+=response[1:]
            
            print("Search result:\n"+str(response[1:]))
        
        return True

    async def summary_act(self, step : str) -> bool:
        response = self.client.chat.completions.create(
            model = self.model,
            messages = self.messages
        )

        self.messages+=[{
            "role" : "assistant",
            "content" : response.choices[0].message.content
        }]

        print("Summary result:\n" + response.choices[0].message.content)

        return True

    async def document_act(self, step : str) -> bool:

        self.messages[-1]["content"] = "Generate a file and save it locally. " + self.messages[-1]["content"]

        response = await self.mcp_client.process_query(self.messages)

        self.messages+=response[1:]

        print("Document result:\n"+str(response[1:]))

        return True

    async def file_act(self, step : str) -> bool:
        messages = [
            {
                "role" : "system",
                "content" : BROWSER_PROMPT,
            },
            {
                "role" : "user",
                "content" : step,
            }
        ]

    async def chat_act(self, step : str) -> bool:
        response = self.client.chat.completions.create(
            model = self.model,
            messages = self.messages
        )

        self.messages+=[{
            "role" : "assistant",
            "content" : response.choices[0].message.content
        }]

        print("chat result:\n" + response.choices[0].message.content)

        return True
        


    async def loop_chat(self):
        print("""Hello! Welcome to use the Simple AI Agent😄😄😄.\nYou can test the Agent like using throuth terminal😎😎😎.\nYou can input the query in the next line and if you want to exit the Agent just input quit().""")

        while(True):
            self.messages = []
            self.step_num = 1
            query = input("Query: ").strip()

            if query == "":
                print("You don't input any query, please give me some query。🥺🥺🥺")
                continue

            if "quit()" in query.lower():
                break
            else:
                self.messages.append({
                    "role" : "user",
                    "content" : query
                })
                await self.planning(query, 0)
            
    async def clean_up(self):
        await self.mcp_client.cleanup()

async def main():
    agent = Agent()
    try:
        for i in range(1,len(sys.argv)):
            await agent.mcp_client.connect_to_mock_server(sys.argv[i])
        await agent.loop_chat()
    finally:
        await agent.clean_up()
        
if __name__ == "__main__":
    asyncio.run(main())