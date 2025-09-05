import os
import pandas as pd
import numpy as np
import json
from tqdm import tqdm
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 配置类
class Config:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE_PATH = os.path.join(CURRENT_DIR, "config.json")

    # 数据文件路径
    PROCESSED_REPORTS_PATH = os.path.join(CURRENT_DIR, "..", "processed_reports.csv")
    PROCESSED_IMAGES_PATH = os.path.join(CURRENT_DIR, "..", "processed_images.npy")
    TRAIN_REPORTS_PATH = os.path.join(CURRENT_DIR, "..", "train_reports.csv")
    TRAIN_IMAGES_PATH = os.path.join(CURRENT_DIR, "..", "train_images.npy")
    TEST_REPORTS_PATH = os.path.join(CURRENT_DIR, "..", "test_reports.csv")
    TEST_IMAGES_PATH = os.path.join(CURRENT_DIR, "..", "test_images.npy")

    # 默认配置
    DEFAULT_CONFIG = {
        "VECTOR_DB_PATH": os.path.join(CURRENT_DIR, "chroma_db"),
        "EMBEDDING_MODEL": "shibing624/text2vec-base-chinese",
        "LOCAL_MODEL_PATH": None,
        "PROXY": None,
        "BATCH_SIZE": 100,
        "DOWNLOAD_TIMEOUT": 30,
        "MAX_RETRIES": 3
    }

    # 加载配置
    @classmethod
    def load_config(cls):
        config = cls.DEFAULT_CONFIG.copy()
        if os.path.exists(cls.CONFIG_FILE_PATH):
            try:
                with open(cls.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                print(f"已加载配置文件: {cls.CONFIG_FILE_PATH}")
            except Exception as e:
                print(f"加载配置文件出错: {e}，使用默认配置")
        else:
            print(f"配置文件不存在: {cls.CONFIG_FILE_PATH}，使用默认配置")
            # 创建示例配置文件
            try:
                with open(cls.CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cls.DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
                print(f"已创建示例配置文件: {cls.CONFIG_FILE_PATH}")
            except Exception as e:
                print(f"创建示例配置文件失败: {e}")
        return config

# 初始化配置
config = Config.load_config()
VECTOR_DB_PATH = config["VECTOR_DB_PATH"]
EMBEDDING_MODEL = config["EMBEDDING_MODEL"]
LOCAL_MODEL_PATH = config["LOCAL_MODEL_PATH"]
PROXY = config["PROXY"]
BATCH_SIZE = config["BATCH_SIZE"]
DOWNLOAD_TIMEOUT = config["DOWNLOAD_TIMEOUT"]
MAX_RETRIES = config["MAX_RETRIES"]

# 加载数据
def load_data():
    """加载处理后的文本和图像数据"""
    print("加载处理后的数据...")
    try:
        # 加载文本数据
        processed_reports = pd.read_csv(Config.PROCESSED_REPORTS_PATH)
        train_reports = pd.read_csv(Config.TRAIN_REPORTS_PATH)
        test_reports = pd.read_csv(Config.TEST_REPORTS_PATH)

        # 加载图像数据
        processed_images = np.load(Config.PROCESSED_IMAGES_PATH, allow_pickle=True)
        train_images = np.load(Config.TRAIN_IMAGES_PATH, allow_pickle=True)
        test_images = np.load(Config.TEST_IMAGES_PATH, allow_pickle=True)

        print(f"""成功加载数据:
- 处理后的报告: {len(processed_reports)} 条
- 训练集报告: {len(train_reports)} 条
- 测试集报告: {len(test_reports)} 条
- 处理后的图像: {len(processed_images)} 张
- 训练集图像: {len(train_images)} 张
- 测试集图像: {len(test_images)} 张""")

        return {
            "processed_reports": processed_reports,
            "train_reports": train_reports,
            "test_reports": test_reports,
            "processed_images": processed_images,
            "train_images": train_images,
            "test_images": test_images
        }
    except Exception as e:
        print(f"加载数据时出错: {e}")
        raise

# 设置环境变量
import os

def set_environment_variables():
    """设置环境变量，包括代理"""
    if PROXY:
        os.environ["HTTP_PROXY"] = PROXY
        os.environ["HTTPS_PROXY"] = PROXY
        print(f"已设置代理: {PROXY}")
    else:
        # 清除可能存在的代理设置
        if "HTTP_PROXY" in os.environ:
            del os.environ["HTTP_PROXY"]
        if "HTTPS_PROXY" in os.environ:
            del os.environ["HTTPS_PROXY"]

# 初始化向量数据库
def init_vector_db():
    """初始化向量数据库"""
    print(f"初始化向量数据库，使用模型: {EMBEDDING_MODEL}")
    
    try:
        # 先设置环境变量（包括代理）
        set_environment_variables()
        
        # 然后设置下载超时环境变量
        if DOWNLOAD_TIMEOUT:
            os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = str(DOWNLOAD_TIMEOUT)
            print(f"已设置HF_HUB_DOWNLOAD_TIMEOUT: {DOWNLOAD_TIMEOUT}秒")
        
        # 打印当前环境变量状态以便调试
        print("当前环境变量设置:")
        print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', '未设置')}")
        print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', '未设置')}")
        print(f"HF_HUB_DOWNLOAD_TIMEOUT: {os.environ.get('HF_HUB_DOWNLOAD_TIMEOUT', '未设置')}")

        # 加载嵌入模型的参数
        model_kwargs = {
                "device": "cpu"
            }

        # 检查是否使用本地模型
        if LOCAL_MODEL_PATH:
            print(f"使用本地模型: {LOCAL_MODEL_PATH}")
            embeddings = HuggingFaceEmbeddings(
                model_name=LOCAL_MODEL_PATH,
                model_kwargs=model_kwargs
            )
        else:
            # 在线下载模型，添加重试机制
            from tenacity import retry, stop_after_attempt, wait_exponential
            import time

            @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=1, max=10))
            def load_embeddings_with_retry():
                return HuggingFaceEmbeddings(
                    model_name=EMBEDDING_MODEL,
                    model_kwargs=model_kwargs
                )

            print(f"尝试下载模型，最多重试 {MAX_RETRIES} 次...")
            embeddings = load_embeddings_with_retry()

        # 初始化向量数据库
        vector_db = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=embeddings
        )

        print(f"向量数据库初始化成功，存储路径: {VECTOR_DB_PATH}")
        return vector_db, embeddings
    except Exception as e:
        print(f"初始化向量数据库时出错: {e}")
        print("提示: 您可以尝试以下解决方法:")
        print("1. 检查网络连接是否正常")
        print("2. 在Config类中设置正确的代理服务器")
        print("3. 提前下载模型并设置LOCAL_MODEL_PATH指向本地模型目录")
        raise

def convert_to_basic_type(value):
    """将值转换为ChromaDB支持的基本类型"""
    if pd.isna(value):
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (list, tuple)):
        # 将列表或元组转换为字符串
        return str(value)
    elif isinstance(value, dict):
        # 将字典转换为字符串
        return str(value)
    elif hasattr(value, 'shape'):
        # 处理numpy数组等有shape属性的对象
        shape = value.shape
        if len(shape) == 3:
            return f"{shape[0]}x{shape[1]}x{shape[2]}"
        elif len(shape) == 2:
            return f"{shape[0]}x{shape[1]}"
        else:
            return str(shape)
    else:
        # 其他类型转换为字符串
        return str(value)

# 准备文档数据
def prepare_documents(reports_df, images=None, dataset_type="processed"):
    """准备文档数据用于向量存储"""
    documents = []
    metadatas = []

    print(f"准备 {dataset_type} 数据集的文档...")
    for idx, row in tqdm(reports_df.iterrows(), total=len(reports_df)):
        # 创建文档内容
        content_parts = []
        if 'findings' in row and pd.notna(row['findings']):
            content_parts.append(f"检查结果: {row['findings']}")
        if 'impression' in row and pd.notna(row['impression']):
            content_parts.append(f"印象: {row['impression']}")
        if 'findings_tokens' in row and pd.notna(row['findings_tokens']):
            content_parts.append(f"检查结果分词: {row['findings_tokens']}")
        if 'impression_tokens' in row and pd.notna(row['impression_tokens']):
            content_parts.append(f"印象分词: {row['impression_tokens']}")

        # 如果没有足够的内容，跳过此记录
        if not content_parts:
            continue

        content = "\n".join(content_parts)
        document_id = f"{dataset_type}_doc_{idx}"

        # 创建元数据
        metadata = {
            "document_id": document_id,
            "dataset_type": dataset_type,
            "index": idx
        }

        # 添加额外的元数据字段
        for col in reports_df.columns:
            if col not in ['findings', 'impression', 'findings_tokens', 'impression_tokens'] and pd.notna(row[col]):
                metadata[col] = convert_to_basic_type(row[col])

        # 如果有图像数据，添加图像信息
        if images is not None and idx < len(images):
            metadata["has_image"] = True
            metadata["image_shape"] = convert_to_basic_type(images[idx].shape)
        else:
            metadata["has_image"] = False

        documents.append(content)
        metadatas.append(metadata)

    print(f"准备完成，共 {len(documents)} 个文档")
    return documents, metadatas

# 批量添加文档到向量数据库
def add_documents_to_db(vector_db, documents, metadatas):
    """批量添加文档到向量数据库"""
    print(f"将 {len(documents)} 个文档添加到向量数据库...")
    try:
        # 批量处理
        for i in range(0, len(documents), BATCH_SIZE):
            batch_end = min(i + BATCH_SIZE, len(documents))
            batch_docs = documents[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]

            vector_db.add_texts(
                texts=batch_docs,
                metadatas=batch_metadatas,
                ids=[f"doc_{i+j}" for j in range(len(batch_docs))]
            )
            print(f"已添加 {batch_end}/{len(documents)} 个文档")

        # 持久化数据库
        vector_db.persist()
        print("文档添加完成并已持久化")
    except Exception as e:
        print(f"添加文档到向量数据库时出错: {e}")
        raise

# 主函数
def main():
    """主函数"""
    try:
        # 1. 加载数据
        data = load_data()

        # 2. 初始化向量数据库
        vector_db, embeddings = init_vector_db()

        # 3. 准备并添加处理后的所有数据
        docs, metadatas = prepare_documents(data["processed_reports"], data["processed_images"], "processed")
        add_documents_to_db(vector_db, docs, metadatas)

        # 4. 准备并添加训练集数据
        train_docs, train_metadatas = prepare_documents(data["train_reports"], data["train_images"], "train")
        add_documents_to_db(vector_db, train_docs, train_metadatas)

        # 5. 准备并添加测试集数据
        test_docs, test_metadatas = prepare_documents(data["test_reports"], data["test_images"], "test")
        add_documents_to_db(vector_db, test_docs, test_metadatas)

        print("向量数据库构建完成！")
        print(f"数据库存储位置: {VECTOR_DB_PATH}")
        print("你可以在后续的RAG应用中使用这个向量数据库进行检索。")
    except Exception as e:
        print(f"程序执行出错: {e}")
        raise

if __name__ == "__main__":
    main()