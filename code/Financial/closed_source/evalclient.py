import json
import os
import requests
import itertools
import openai
from datetime import datetime
from openai import OpenAI
import anthropic
import qianfan
import sys
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
proxies ={'https': 'http://172.31.202.109:7892'}
# 加载 API 密钥和对话配置
with open(current_path+'/config.json') as f:
    config = json.load(f)
    openai_api_key = config['openai_api_key']
    claude_api_key = config['claude_api_key']
    #deepseek_api_key = config['deepseek_api_key']
    #deepseek_url = config['deepseek_url']

def evalclient(prompt,url, model):
    if model == "flageval-serving":
        try:
            raw_request = {
                    "engine": "",
                    "prompt": prompt,
                    "temperature": 1e-7,
                    "num_return_sequences": 1,
                    "max_new_tokens": 8192,
                    "top_p": 1,
                    "echo_prompt": False,
                    "top_k_per_token": 1,
                    "stop_sequences": [],
                }

            data_json = json.dumps(raw_request)
            response = requests.post(url, json=data_json).json()
            content = response["completions"][0]["text"]
            model_info = response["model_info"]

        except Exception as e:
            print(f"Error with flageval-serving API: {str(e)}")
            return None, ""
    elif "gpt-" in model or 'o1-' in model:
        try:
            openai_client = OpenAI(api_key=openai_api_key,base_url=proxies.get('https'),)
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                max_tokens=8192,
            )
            content = response.choices[0].message.content
        except Exception as e:
            print(f"Error with OpenAI API: {str(e)}")
            return None, model
    elif "claude-" in model:
        try:
            client = openai.Client(
            base_url="https://api.pandalla.ai/v1", api_key="sk-pVQGFS0muYPFc9IMbmu7CCLB5zDEQbaOskNBX7yNaSYXidNB")
            # Chat completion
            response = client.chat.completions.create(
                model="claude-3-5-haiku-20241022",
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_completion_tokens=8192,
            )
            
            content = response.choices[0].message.content

        except Exception as e:
            print(f"Error with Claude API: {str(e)}")
            return None, model
    elif "yi-large" in model:
        try:
            client = openai.Client(
            base_url="https://api.lingyiwanwu.com/v1", api_key="0879f16109824fd6bfe23a13addb0d7c")
            # Chat completion
            response = client.chat.completions.create(
                model="yi-large",
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_completion_tokens=8192,
            )
            
            content = response.choices[0].message.content
        except Exception as e:
            print(f"Error with yi-large API: {str(e)}")
            return None, model
    elif "ERNIE-" in model:
        try:
            os.environ["QIANFAN_ACCESS_KEY"] = "09f6d78c3a3c45f3bdf96980d3089174"
            os.environ["QIANFAN_SECRET_KEY"] = "cc9bdb92733447a69f12378caaf8b6cf"
            chat_comp = qianfan.ChatCompletion()
            response = chat_comp.do(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    disable_search=True,
                    temperature=0.9,
                    top_p=0.9,
                    max_tokens=8192,
                    request_timeout=300
                )['body']['result']
            content = response

        except Exception as e:
            print(f"Error with ERNIE API: {str(e)}")
            print(f"dialogue: {dialogue},topic: {topic}, ")
            return None, model
    elif "deepseek" in model:
        print("deepseek in model", "deepseek" in model)
        try:
            client = OpenAI(
                api_key="sk-46f0dfce51b34cfca4c26bc2a9e4a0f9",
                base_url="https://api.deepseek.com"
            )

            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )
            print("response", response)
            content: str = response.choices[0].message.content
        except Exception as e:
            print(f"Error with deepseek API: {str(e)}")
            return None, model
    elif "doubao-" in model or "Doubao-" in model:
        try:
            openai_client = OpenAI(api_key='2936fb06-eebb-414d-9445-75dbeb1d8596', base_url = "https://ark.cn-beijing.volces.com/api/v3")
            response = openai_client.chat.completions.create(
                model='ep-20241028182216-6zzbw', # doubao_pro_32k_0828_非联网版本-智源1028
                max_tokens= 300,
                 messages=[
                    {"role": "user", "content": prompt},
                ]
            )

            content = response.choices[0].message.content
        except Exception as e:
            print(f"Error with doubao API: {str(e)}")
            print(f"dialogue: {dialogue},topic: {topic}, ")
            return None, model
    else:
        return "not support model", model
    return content, model

if __name__ == "__main__":
    #evalclient('# 角色设定 #\n你是一位二十年资深辩论选手，以逻辑严密、观点鲜明和语言生动著称。你的角色是辩论的代表方（正方或反方），目标是利用理性论据和真实案例有力地支撑己方观点并反驳对方。\n\n# 行为准则 #\n- 目标明确：专注于辩论中的“说服”任务，以精炼而逻辑清晰的语言提出论点和反驳对方。你的最终目标是使对方和观众更倾向于支持你的立场。\n- 事实为依据：避免空泛例证，以事实为基础支持论点，确保内容符合道德伦理和法律。\n- 简洁明快：每次对话不超过 300 字。 避免不必要的场面话，尽量精炼和直接。\n- 紧扣主题：保持言辞直击辩题核心，避免过度铺垫。对话末尾再次强调与辩题相关的关键点，以增强说服效果。\n\n# 对话风格 #\n1. 精准表达：避免赘言，每次发言小于 300 字，直接指出对方观点的漏洞或局限，用精炼、逻辑严密的语言陈述己方立场。\n2. 生动幽默：合理运用幽默和生动的措辞，引发观众共鸣，使对话轻松而不失说服力。\n3. 回归辩题：在对话的最后总结核心论点，确保与辩题紧密关联，并引导观众关注问题的实质。\n\n# 示例 #\n主题：真爱是否为一种谎言？\n你是正方\n我是反方\n\n示例对话：\n那我说我正在谈恋爱正在拥有真爱，你怎么反驳我吧\n我怎么反驳？我想问你一下，你是哪一刻确定你拥有的这段爱是真爱?\n额，这个问题有点难回答，但我自己的感觉可以，只是我无法把我的感觉传递给你\n那我换一个问题，假设有一个人他声称拥有真爱，你是要告诉我们，反正真爱存在，她说什么我们信什么，还是你有一个办法帮我们判断她是不是真的拥有真爱\n', "http", "gpt-4o")
    #evalclient("使用VeighNa平台的CTA策略模板CtaTemplate，针对股指期货，开发一套简单的双均线策略SmaStrategy，并提供策略源代码和逻辑说明", "http", "gpt-4o")
    #evalclient("使用VeighNa平台的CTA策略模板CtaTemplate，针对股指期货，开发一套简单的双均线策略SmaStrategy，并提供策略源代码和逻辑说明", "http://120.92.208.64:7609/func", "flageval-serving")
    evalclient("我希望你作为一名使用VeighNa（vn.py）量化平台经验丰富的量化研究员，根据我描述的需求开发对应的程序代码。对于你开发的程序代码，都会提供对于程序逻辑的细节中文注释，代码中使用类型提示Type Hinting，同时代码内容需要符合PEP8代码标准要求。\n使用VeighNa平台的CTA策略模板CtaTemplate（位于vnpy_ctastrategy.template子模块下），开发一套简单的双均线策略，具体要求如下：\n\n 1. 使用简单移动平均线SMA判断多空信号\n2. 交易品种是期货，可以双向交易，允许做空", "http://120.92.208.64:7609/func", "flageval-serving")
