# 导入必要的标准库
import os
import logging
import asyncio
import time

# 从lightrag库中导入LightRAG类和QueryParam类
from lightrag import LightRAG, QueryParam
# 从lightrag.llm.zhipu模块中导入智普大模型的文本生成和嵌入函数
from lightrag.llm.zhipu import zhipu_complete, zhipu_embedding
# 从lightrag.utils模块中导入EmbeddingFunc类，用于定义嵌入函数
from lightrag.utils import EmbeddingFunc
# 从lightrag.kg.shared_storage模块中导入初始化管道状态的函数
from lightrag.kg.shared_storage import initialize_pipeline_status

# 设置工作目录
WORKING_DIR = "./mechanical_electrical"
# 设置文档路径
DOCUMENT_PATH = "./机电系统故障诊断与维修案例教程.txt"

# 配置日志记录，设置日志格式和日志级别为INFO
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

# 如果工作目录不存在，则创建该目录
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# 设置智普大模型的API密钥
os.environ["ZHIPUAI_API_KEY"] = "de713e4585d44fa2889a6d1d248ec968.zmYy00mOj2ZEXdRx"  # 请在此处填入你的API密钥

# 获取环境变量中的API密钥
api_key = os.environ.get("ZHIPUAI_API_KEY")
# 如果API密钥未设置，则抛出异常提示用户设置API密钥
if api_key is None:
    raise Exception("请设置ZHIPU_API_KEY环境变量")


# 定义一个异步函数，用于初始化LightRAG实例
async def initialize_rag():
    # 创建LightRAG实例
    rag = LightRAG(
        working_dir=WORKING_DIR,  # 设置工作目录
        llm_model_func=zhipu_complete,  # 设置使用的语言模型函数
        llm_model_name="glm-4-flashx",  # 设置使用的语言模型名称
        llm_model_max_async=4,  # 设置最大异步请求数
        llm_model_max_token_size=32768,  # 设置模型处理的最大token数量
        # 设置嵌入函数
        embedding_func=EmbeddingFunc(
            embedding_dim=2048,  # 设置嵌入向量的维度
            max_token_size=8192,  # 设置模型处理的最大token数量
            func=lambda texts: zhipu_embedding(texts),  # 使用智普的嵌入函数
        ),
    )

    # 初始化存储系统
    await rag.initialize_storages()
    # 初始化管道状态
    await initialize_pipeline_status()

    # 返回初始化好的LightRAG实例
    return rag


# 定义文档处理函数
def process_document(rag):
    """处理机电系统故障诊断文档"""
    try:
        # 检查文档是否存在
        if not os.path.exists(DOCUMENT_PATH):
            raise FileNotFoundError(f"文档文件不存在: {DOCUMENT_PATH}")

        # 读取本地文本文件
        with open(DOCUMENT_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # 将文档内容插入到LightRAG中
        rag.insert(content)
        logging.info(f"成功加载文档: {os.path.basename(DOCUMENT_PATH)}")
        logging.info(f"文档大小: {len(content) / 1024:.2f} KB")
        return True
    except Exception as e:
        logging.error(f"文档处理失败: {str(e)}")
        return False


# 定义查询函数
def execute_queries(rag, question, mode_name):
    """执行查询并返回结果"""
    try:
        start_time = time.time()

        # 根据模式名称设置查询参数
        param = QueryParam(mode=mode_name)

        # 执行查询
        result = rag.query(question, param=param)

        # 计算查询耗时
        elapsed = time.time() - start_time

        return {
            "mode": mode_name,
            "result": result,
            "time": elapsed
        }
    except Exception as e:
        logging.error(f"{mode_name}模式查询失败: {str(e)}")
        return {
            "mode": mode_name,
            "result": f"查询失败: {str(e)}",
            "time": 0
        }


# 定义主函数
def main():
    # 使用异步事件循环初始化LightRAG实例
    rag = asyncio.run(initialize_rag())
    logging.info("LightRAG系统初始化完成")

    # 处理文档
    if not process_document(rag):
        return

    # 机电系统相关的专业问题集
    question_sets = [
        {
            "category": "故障基础",
            "questions": [
                "机电设备故障的主要形式有哪些？",
                "故障诊断的基本流程是什么？"
            ]
        },
        {
            "category": "轴承诊断",
            "questions": [
                "如何诊断滚动轴承的失效？",
                "滑动轴承的安装要求是什么？"
            ]
        },
        {
            "category": "维修管理",
            "questions": [
                "设备维修计划管理包含哪些内容？",
                "维修技术准备工作有哪些？"
            ]
        },
        {
            "category": "传动系统",
            "questions": [
                "齿轮传动的失效形式及防止措施有哪些？",
                "轴类零件的主要失效形式是什么？"
            ]
        }
    ]

    # 查询模式列表
    modes = ["naive", "local", "global", "hybrid"]
    mode_names = {
        "naive": "朴素检索",
        "local": "局部检索",
        "global": "全局检索",
        "hybrid": "混合检索"
    }

    # 执行所有查询
    for set_idx, question_set in enumerate(question_sets, 1):
        print(f"\n{'=' * 50}")
        print(f"问题分类 {set_idx}: {question_set['category']}")
        print(f"{'=' * 50}")

        for q_idx, question in enumerate(question_set['questions'], 1):
            print(f"\n问题 {q_idx}: {question}")

            # 执行所有模式的查询
            results = []
            for mode in modes:
                result = execute_queries(rag, question, mode)
                results.append(result)

            # 打印所有结果
            for result in results:
                print(f"\n[{mode_names.get(result['mode'], result['mode'])}] 耗时: {result['time']:.2f}s")
                print(f"结果: {result['result']}")

            print(f"\n{'-' * 50}")


# 如果当前模块是主模块，则调用主函数
if __name__ == "__main__":
    main()