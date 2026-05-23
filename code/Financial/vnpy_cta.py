import importlib
import ast
import pandas as pd
import os, sys, json
import time
import traceback
import requests
from openai import OpenAI
from datetime import datetime, date
from typing import Type
from model_third.evalclient import evalclient
from vnpy.trader.utility import load_json, save_json
from vnpy_ctastrategy.backtesting import BacktestingEngine, CtaTemplate


def function_definitions(python_file):
    with open(python_file, 'r') as file:
        content = file.read()
        tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return node.name


def get_code_from_file(cnt,num, model):
    #filename: str = "./cta/llms_test/llm"+str(num)+".py"
    filename: str = "allmodels/"+model+"-llm_outputs/"+str(cnt)+"/llm"+str(num)+".py"
    with open(filename, "r", encoding="UTF-8") as lrf:
        code = lrf.read()
    return code, model

def get_code_from_llm(task: str, model: str) -> str:
    try:
        print("get_code_from_llm")
        """从大模型处获取生成的任务代码"""
        content, model_info = evalclient(task, model)
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

def run_cta_backtesting() -> dict:
    """运行CTA策略回测"""
    try:
        # 从文件中加载策略类
        if 'llm_output' in sys.modules.keys():
            del sys.modules['llm_output']
        import llm_output as m
        #importlib.reload(m)

        strategy_class: Type[CtaTemplate] = None

        for field_name in dir(m):
            field_value: object = getattr(m, field_name)
            if field_name.endswith("Strategy"):
                strategy_class = field_value

        # 执行回测任务
        engine = BacktestingEngine()
        print("engin init done")

        engine.set_parameters(
            vt_symbol="IF99.CFFEX",
            interval="1m",
            start=datetime(2020, 1, 1),
            end=datetime(2023, 12, 30),
            rate=0.3/10000,
            slippage=0.2,
            size=300,
            pricetick=0.2,
            capital=1_000_000,
        )
        engine.add_strategy(strategy_class, {})

        engine.load_data()
        engine.run_backtesting()
        engine.calculate_result()
        d = engine.calculate_statistics()

        for k, v in list(d.items()):
            if "date" in k:
                if isinstance(v, str):
                    d[k] = v
                else:
                    d[k] = v.strftime('%Y-%m-%d')
            elif not isinstance(v, str):
                d[k] = float(v)

        return {
            "success": True,
            "statistics": d,
            "exception": ""
        }
    except Exception:
        return {
            "success": False,
            "statistics": {},
            "exception": traceback.format_exc()
        }


def run_pipe(num, task, model, cnt):#, cta_results):
    #code, model_info = get_code_from_llm(task, model)
    code, model_info = get_code_from_file(cnt, num, model)
    print(f"大模型生成代码完成，代码长度{len(code)}")
    filename: str = "./llm_output.py"
    save_code_to_file(code, filename, num)
    print(f"代码文件保存成功{filename}")


    # 执行回测检验
    result = run_cta_backtesting()

    if result["success"]:
        print("CTA策略回测运行成功", num)
        #print(result["statistics"])
        #cta_results.append({"num":num, "statistics": result["statistics"]})
        #cta_results.append({"num":num, "indicator": result, "model": model_info})
        #result_filename = model+"cta_overall.json"
        result_filename = model+"_overall.json"
        cta_results = load_json(result_filename)
        
        if str(num) in cta_results.keys():
            cta_results[str(num)].append(result["statistics"])
            print(num, len(cta_results[str(num)]))
        else:
            cta_results[str(num)] =[result["statistics"]]
        save_json(result_filename, cta_results)
    else:
        print("CTA策略回测运行失败", num)
        print(result["exception"])

    return result["success"]

def run(model):
    #with open('.vntrader/cta_overall.json', 'w') as file:
    #    file.truncate()
    for cnt in range(10):
        cta_results,count=[],0
        for file in os.listdir("QuantBench_v1.2"):
            file_path = os.path.join("QuantBench_v1.2", file)
            if os.path.isfile(file_path) and "xlsx" not in file_path:
                count += 1
                num = file.split(".")[0]
                if int(num) >= 16:
                    continue
                print("cnt",cnt, "num", num)
                with open(file_path, 'r', encoding='utf - 8') as taskfile:
                    task = taskfile.read()
                    success = run_pipe(num,task, model, cnt)#, cta_results)
            break
        #print("cta_results", cta_results)
        #with open(str(cnt)+"cta_overall.json",'w') as rf:
        #    json.dump({"accuracy":len(cta_results)/count,"cta_results":cta_results},rf,indent=4)
        break

if __name__ == "__main__":
    run("deepseek-chat")
