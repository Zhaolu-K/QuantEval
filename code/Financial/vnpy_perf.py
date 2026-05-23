import importlib
import ast
import pandas as pd
import os, sys, json
import time
import traceback
import numpy as np
import subprocess
import shutil
from random import randint
from vnpy.trader.utility import load_json, save_json
from vnpy.trader.object import BarData
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.utility import ArrayManager
from model_third.evalclient import evalclient


def performance(operation, data):
    # 初始化数据
    #data: list[int] = list(range(1000))      # 使用纯Python数据结构
    iterations = 100_000
    values: list[int] = [randint(0, 100) for _ in range(iterations)]

    # 循环多次进行测试
    start_time: int = time.perf_counter_ns()

    for value in values:
        #test_python(data, value)
        operation(data, value)
    end_time: int = time.perf_counter_ns()

    # 计算每次执行的平均时间
    avg_time: float = (end_time - start_time) / iterations
    # 打印结果
    print(f"总运行次数{iterations}，平均耗时{avg_time / 1e6:.6f}毫秒")
    print("avg_time",avg_time)
    return avg_time


def function_definitions(python_file):
    with open(python_file, 'r') as file:
        content = file.read()
        tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return node.name


def get_code_from_file(cnt,num, model):
    filename: str = "allmodels/"+model+"-llm_outputs/"+str(cnt)+"/llm"+str(num)+".py"
    with open(filename, "r", encoding="UTF-8") as lrf:
        code = lrf.read()
    return code, "gpt-4o"

def get_ccode_from_file(cnt, num, model):
    # 目标文件夹名称
    target_folder = "cython"+str(num)
    
    # 判断目标文件夹是否存在
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)
        print(f"{target_folder}文件夹已删除")
    source_folder = "allmodels/"+model+"-llm_outputs/"+str(cnt)+"/"+str(num)
    shutil.copytree(source_folder, target_folder)


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

def run_indic_backtesting(num, model):
    try:
        result = 0
        if num in [23,24,25]:
            data = np.arange(1000)
            if 'llm_output' in sys.modules.keys():
                del sys.modules['llm_output']
            import llm_output as m
            #importlib.reload(m)
            for field_name in dir(m):
                field_value: object = getattr(m, field_name)
                if field_name.startswith("test_"):
                    strategy_class = field_value
                    result = performance(strategy_class, data)
                    break
            print(str(num), result)
        elif num in [26,27,28]:
            if num == 26:
                data: list[int] = list(range(1000))
            else:
                data = np.array(range(1000), dtype=np.float64)
            folder = "cython"+str(num)
            os.chdir(folder)
            try:
                subprocess.run("chmod +x bash.sh", shell=True)
                subprocess.run(["./bash.sh"], shell=True)
                os.chdir("..")
            except:
                os.chdir("..")
            for file in os.listdir(folder):
                if file.endswith('.so'):
                    sofile = file.split(".")[0]
            loaded_module = importlib.import_module(folder+"."+sofile)
            if num == 26:
                result = performance(loaded_module.test_cython, data)
            elif num == 27:
                result = performance(loaded_module.test_numpy_cython, data)
            elif num == 28:
                result = performance(loaded_module.test_numpy_cython_static, data)
            else:
                result = -1
            #from cython26.test_module import test_cython
            #from cython27.test_numpy_cython import test_cython
            
            #result = performance(loaded_module.test_cython, data)
            print(str(num), result)
        #strategy_class: Type[CtaTemplate] = None

        #for field_name in dir(m):
        #    field_value: object = getattr(m, field_name)
        #    if field_name.startswith("test_numpy"):
        #        strategy_class = field_value
        #        print(strategy_class, field_name, m)
        #        result = performance(strategy_class)
        if result >0:
            #result_filename = model+"perf_overall.json"
            result_filename = model+"_overall.json"
            cta_results = load_json(result_filename)
            print("read json", cta_results.keys())

            if str(num) in cta_results.keys():
                cta_results[str(num)].append(result)
                print(num, len(cta_results[str(num)]))
            else:
                cta_results[str(num)] =[result]
            save_json(result_filename, cta_results)

        return {"success":True,"result":result}
    except Exception as e:
        return {"success":False,"result":0, "exception":e}

def run_pipe(num, task, model, cnt):
    if int(num) in [23,24,25]:
        #code, model_info = get_code_from_llm(task, model)
        code, model_info = get_code_from_file(cnt, num, model)
        #print(f"大模型生成代码完成，代码长度{len(code)}")
        #print(code, model_info, num)
        filename: str = "./llm_output.py"
        save_code_to_file(code, filename, num)
        #print(f"代码文件保存成功{filename}")
    elif int(num) in [26,27,28]:
        get_ccode_from_file(cnt,num, model)
    else:
        return
    # 执行回测检验
    result = run_indic_backtesting(int(num), model)
    print("run indic done",result)

    if result["success"]:
        #result_filename = model+"perf_overall.json"
        #cta_results = load_json(result_filename)
        #print("read json", cta_results.keys())

        #if str(num) in cta_results.keys():
        #    cta_results[str(num)].append(result["result"])
        #    print(num, len(cta_results[str(num)]))
        #else:
        #    cta_results[str(num)] =[result["result"]]
        #save_json(result_filename, cta_results)
        print("CTA策略回测运行成功", num)
        #print(result["result"])
        #cta_results.append({"num":num, "avg-time": result['result']})
        #cta_results.append({"num":num, "avg-time": result['result'], "model": model_info})
    else:
        print("CTA策略回测运行失败", num)
        print(result["exception"])

    return result["success"]

def run(model):
    Quantpath = "QuantBench_v1.2"
    for cnt in range(10):
        #if cnt != 0:
        #    continue
        cta_results,count=[],0
        for file in os.listdir(Quantpath):
            file_path = os.path.join(Quantpath, file)
            if os.path.isfile(file_path) and "xlsx" not in file_path:
                count += 1
                num = file.split(".")[0]
                if int(num) >= 23 and int(num) <=29:
                    print("cnt",cnt, "num",num)
                    #if int(num) != 26:
                    #    continue
                    #if(cnt in [0,1,2,3,4,5,6,7,8,9] and int(num)==27) or (cnt in [0,1,2,3,4,5,6,7,8,9] and int(num)==28) or(cnt in [9] and int(num) in [24]):  #llama3.1
                    #llama3.3#if (cnt in [0,1,2,3,4,6,7,8,9] and int(num) ==28) or (cnt in [0,1,9] and int(num) == 27) or (cnt in [6,7,8,9] and int(num)==24) or (cnt in [7,8,9] and int(num)==25):
                    #    continue
                    with open(file_path, 'r', encoding='utf - 8') as taskfile:
                        task = taskfile.read()
                        success = run_pipe(num,task, model, cnt)#, cta_results)
                #print(num)
                #if int(num) not in [23,24,25]:
                #if int(num) != 26:
                #    continue
        #break
if __name__ == "__main__":
    run("gpt-4o-2024-08-06")
