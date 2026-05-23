import importlib
import ast
import pandas as pd
import os, sys, json
import time
import math
import traceback
import numpy as np
from vnpy.trader.utility import load_json, save_json
from vnpy.trader.object import BarData
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.utility import ArrayManager


threshold=0.01

def prepare_am() -> ArrayManager:
    """准备测试用的ArrayManager对象"""
    df: pd.DataFrame = pd.read_csv("bar_data.csv")

    am: ArrayManager = ArrayManager(size=1000)

    for row in df.itertuples():
        bar: BarData = BarData(
            symbol=row.symbol,
            exchange=Exchange(row.exchange),
            datetime=row.datetime,
            interval=Interval.MINUTE,
            high_price=row.high,
            low_price=row.low,
            open_price=row.open,
            close_price=row.close,
            volume=row.volume,
            turnover=row.turnover,
            open_interest=row.open_interest,
            gateway_name="CSV",
        )
        am.update_bar(bar)

    return am

def prepare_answers():
    am: ArrayManager = prepare_am()
    answers={}
    result = am.wma(20, True)
    answers["16"] = result[-5:]
    result1, result2, result3 = am.macd(12, 26, 9, True)
    answers["17"] = [result1[-5:],result2[-5:],result3[-5:]]
    result = am.rsi(14, True)
    answers["18"] = result[-5:]
    result = am.cci(20, True)
    answers["19"] = result[-5:]
    result1, result2 = am.boll(20, 2, True)
    answers["20"] = [result1[-5:],result2[-5:]]
    answers["21"] = [1.094404,1.173817,1.014484,1.099357,1.126943]
    answers["22"] = [1.034339,0.967316,0.528202,0.621166,0.560852]
    #print(answers["16"])
    return answers




def function_definitions(python_file):
    with open(python_file, 'r') as file:
        content = file.read()
        tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return node.name


def get_code_from_file(cnt, num, model):
    #filename: str = "./indicator/llms_gpt4o/llm"+str(num)+".py"
    filename: str = "allmodels/"+model+"-llm_outputs/"+str(cnt)+"/llm"+str(num)+".py"
    with open(filename, "r", encoding="UTF-8") as lrf:
        code = lrf.read()
    return code, "gpt-4o"

def get_code_from_llm(task: str, model: str) -> str:
    try:
        print("get_code_from_llm")
        """从大模型处获取生成的任务代码"""
        content, model_info = evalclient(task, model)
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        response = client.chat.completions.create(
            model = model,
            messages=[
                {"role": "user", "content": task},
            ],
            stream=False,
        )
        start_str: str = "```python"
        end_str: str = "\n```\n"

        start_ix: int = content.index(start_str)
        end_ix: int = content.index(end_str)

        code: str = content[start_ix + len(start_str): end_ix - len(end_str)]
        return code, model_info
    except Exception as e:
        print("get code form llm failed", e)
        return "",""

def save_code_to_file(code: str, filename: str, num) -> bool:
    """保存代码到文件"""
    with open(filename, "w", encoding="UTF-8") as lwf:
        lwf.write(code)
    lwf.close()
    return True

def run_indic_backtesting(num, answers):
    try:
        am: ArrayManager = prepare_am()
        if 'llm_output' in sys.modules.keys():
            del sys.modules['llm_output']
        import llm_output as m
        ##importlib.reload(m)

        strategy_class: Type[CtaTemplate] = None
        result = 0
        for field_name in dir(m):
            field_value: object = getattr(m, field_name)
            if field_name.startswith("calculate"):
                strategy_class = field_value
                tmpresult = strategy_class(am)
                break
        #if num == 16:
        #    tmpresult = strategy_class(am, 20)
        #elif num == 17:
        #    tmpresult = strategy_class(am, 12, 26, 9)
        #elif num == 18:
        #    tmpresult = strategy_class(am, 14)
        #elif num == 19:
        #    tmpresult = strategy_class(am, 20)
        #elif num == 20:
        #    tmpresult = strategy_class(am, 20,2)
        #elif num == 21:
        #else:
        #    return {"success":False,"result":0, "exception":"unsupport num"}

        if num == 19:
            print("tmpresult",tmpresult[-5:], type(tmpresult))
        #tmpresult = tmpresult[1]
        #print("tmpresult",tmpresult)
        if num in [16,18,19,21,22]:
            for res,answer in zip (tmpresult[-5:], answers[str(num)]):
                print(type(res),res, answer,abs(res-answer), abs(res-answer)/answer, abs(res-answer)/answer > 0.1)
                if math.isnan(res):
                    res = 0
                if abs(res-answer)/answer > threshold:
                    result = 0
                    break
                else:
                    result = 1
        elif num in [17,20]:
            tmpresults=[]
            for value in tmpresult.values():
                tmpresults.append(value[-5:])
            for tmpresult, answers in zip(tmpresults,answers[str(num)]):
                for res, answer in zip(tmpresult, answers):
                    #print(res, answer,abs(res-answer), abs(res-answer)/answer, abs(res-answer)/answer > 0.1)
                    if abs(res-answer)/answer > threshold:
                        result = 0
                        break
                    else:
                        result = 1
                if result == 0:
                    break
        print(str(num),"result", result)

        return {"success":True,"result":result}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"success":False,"result":0, "exception":e}

def run_pipe(num, task, model, cnt, cta_results, answers):
    #code, model_info = get_code_from_llm(task, model)
    code, model_info = get_code_from_file(cnt, num, model)
    #print(f"大模型生成代码完成，代码长度{len(code)}")
    #print(code, model_info, num)
    filename: str = "./llm_output.py"
    save_code_to_file(code, filename, num)
    #print(f"代码文件保存成功{filename}")

    # 执行回测检验
    result = run_indic_backtesting(int(num), answers)
    print(result)
    if result["success"]:
        #print("CTA策略回测运行成功", num)
        #result_filename =model+ "indic_overall.json"
        result_filename =model+ "_overall.json"
        cta_results = load_json(result_filename)
        print("read json", cta_results.keys())

        if str(num) in cta_results.keys():
            print(num, len(cta_results[str(num)]))
            cta_results[str(num)].append(result["result"])
            print(num, len(cta_results[str(num)]))
        else:
            cta_results[str(num)] =[result["result"]]
        save_json(result_filename, cta_results)
        #cta_results.append({"num":num, "indicator": result["result"]})
        #cta_results.append({"num":num, "indicator": result, "model": model_info})
    else:
        print("CTA策略回测运行失败", num)
        print(result["exception"])

    return result["success"]

def run(model):
    answers = prepare_answers()
    quantpath = "QuantBench_v1.2"
    for cnt in range(10):
        cta_results,count=[],0
        #if cnt != 3:
        #    continue
        for file in os.listdir(quantpath):
            file_path = os.path.join(quantpath, file)
            if os.path.isfile(file_path) and "xlsx" not in file_path:
                count += 1
                num = file.split(".")[0]
                if int(num) >= 16 and int(num) <=22:
                    #if int(num) != 19:
                    #    continue
                    with open(file_path, 'r', encoding='utf - 8') as taskfile:
                        task = taskfile.read()
                    success = run_pipe(num,task, model, cnt, cta_results, answers)
                    #print("cta_results", cta_results)
                    #with open("indic_overall.json",'w') as rf:
                    #    json.dump({"accuracy":len(cta_results)/count,"indic_results":cta_results},rf,indent=4)
        #break

if __name__ == "__main__":
    run("gpt-4o-mini-2024-07-18")
