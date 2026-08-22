# LightRAG 项目环境配置与运行全流程

本文档依据当前仓库（LightRAG `1.3.8`）的代码、`setup.py`、`env.example`、`Dockerfile` 和 `docker-compose.yml` 整理，覆盖从环境准备、模型配置、安装、启动，到文档入库、查询、停止及常见问题处理的完整流程。

> 推荐首次使用者优先选择“源码 + Python 虚拟环境”或“Docker Compose”两种方式之一。API 服务已经内置编译后的 WebUI，正常使用不需要单独安装 Node.js。

## 1. 项目组成与运行链路

项目的主要目录和文件如下：

| 路径 | 作用 |
| --- | --- |
| `lightrag/` | LightRAG Python 核心代码 |
| `lightrag/api/` | FastAPI 服务、认证和接口路由 |
| `lightrag/api/webui/` | API 内置的已编译 WebUI |
| `lightrag_webui/` | WebUI 前端源码，仅二次开发前端时使用 |
| `examples/` | OpenAI、Ollama、Azure OpenAI 等调用示例 |
| `env.example` | 环境变量模板，启动前复制为 `.env` |
| `config.ini.example` | 外部数据库连接模板 |
| `docker-compose.yml` | Docker Compose 部署定义 |
| `data/` | Docker 方式运行后产生的输入及持久化数据 |
| `inputs/`、`rag_storage/` | 源码方式运行时默认生成的输入和持久化目录 |

基本运行链路为：准备 LLM 与 Embedding 服务 → 启动 LightRAG API → 上传或扫描文档 → 后台建立向量和知识图谱索引 → 使用 WebUI 或 API 查询。

## 2. 环境要求

### 2.1 必需环境

- 操作系统：Windows 10/11、Linux 或 macOS。
- Python：`3.9` 及以上；源码和 Dockerfile 推荐使用 Python `3.11`。
- 可访问的 LLM 服务和 Embedding 服务。可使用 Ollama、OpenAI/OpenAI 兼容服务、LoLLMs 或 Azure OpenAI。
- 足够的磁盘空间保存模型、原始文档和索引数据。

### 2.2 按运行方式选择的环境

- 源码运行：Python、pip、venv；Git 仅在需要克隆代码时使用。
- Docker 运行：Docker Engine 或 Docker Desktop，以及 Docker Compose v2。
- 前端二次开发：Node.js 20+ 与 npm，或 Bun。普通部署不需要此项。
- 本地 Ollama：安装 Ollama，并提前拉取聊天模型和嵌入模型。

### 2.3 检查命令

```bash
python --version
python -m pip --version
git --version
docker --version
docker compose version
```

仅在开发前端时检查：

```bash
node --version
npm --version
# 或
bun --version
```

## 3. 获取项目并进入根目录

如果已经位于本项目目录，可跳过本节。

```bash
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG
```

后续命令除非特别说明，均在项目根目录执行。`.env` 必须放在服务的启动目录；最简单可靠的做法就是始终从项目根目录启动。

## 4. 选择模型后端

LightRAG 必须同时拥有以下两类服务：

1. LLM：用于实体/关系抽取、摘要及最终回答。
2. Embedding：用于文本向量化和相似度检索。

推荐从下面两套方案中选择一套。

### 4.1 方案 A：完全使用 Ollama（本地运行）

安装并启动 Ollama 后拉取模型：

```bash
ollama pull mistral-nemo
ollama pull bge-m3
ollama list
```

可根据机器性能更换聊天模型，但嵌入模型、维度和现有索引必须保持一致。默认 `bge-m3` 的维度为 `1024`。

### 4.2 方案 B：完全使用 OpenAI 或兼容接口

需要准备：

- API Base URL，例如 `https://api.openai.com/v1`；
- API Key；
- 一个聊天模型；
- 一个嵌入模型，并确认其向量维度。

例如 `text-embedding-3-small` 默认输出维度为 `1536`，对应 `.env` 中应设置 `EMBEDDING_DIM=1536`。如果使用第三方兼容接口，应以服务提供方实际返回的维度为准。

### 4.3 方案 C：OpenAI LLM + Ollama Embedding

仓库的 `env.example` 默认采用此组合：LLM 请求 OpenAI，Embedding 请求本机 Ollama。该方式既需要有效的 OpenAI Key，也需要本机 Ollama 已运行并安装 `bge-m3`。

## 5. 创建并配置 `.env`

### 5.1 复制模板

Windows PowerShell：

```powershell
Copy-Item env.example .env
```

Linux/macOS：

```bash
cp env.example .env
```

不要把真实 API Key 提交到版本控制。当前 `.gitignore` 已忽略 `.env` 类文件。

### 5.2 最小配置：完全使用 Ollama

编辑 `.env`，至少确认以下内容：

```dotenv
HOST=0.0.0.0
PORT=9621
SUMMARY_LANGUAGE=Chinese

LLM_BINDING=ollama
LLM_MODEL=mistral-nemo:latest
LLM_BINDING_HOST=http://localhost:11434
MAX_TOKENS=8192

EMBEDDING_BINDING=ollama
EMBEDDING_MODEL=bge-m3:latest
EMBEDDING_DIM=1024
EMBEDDING_BINDING_HOST=http://localhost:11434
```

如果 LightRAG 在 Docker 中运行，而 Ollama 在宿主机运行，应将两个 Ollama 地址改为：

```dotenv
LLM_BINDING_HOST=http://host.docker.internal:11434
EMBEDDING_BINDING_HOST=http://host.docker.internal:11434
```

### 5.3 最小配置：完全使用 OpenAI

```dotenv
HOST=0.0.0.0
PORT=9621
SUMMARY_LANGUAGE=Chinese

LLM_BINDING=openai
LLM_MODEL=gpt-4o-mini
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=替换为真实密钥
MAX_TOKENS=32768

EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_BINDING_API_KEY=替换为真实密钥
```

第三方 OpenAI 兼容平台需同时替换模型名、Host 和 Key。

### 5.4 建议关注的通用参数

| 参数 | 当前模板默认值 | 说明 |
| --- | ---: | --- |
| `PORT` | `9621` | API 和内置 WebUI 端口 |
| `SUMMARY_LANGUAGE` | `English` | 中文知识库建议改为 `Chinese` |
| `MAX_ASYNC` | `4` | LLM 最大并发请求数 |
| `MAX_PARALLEL_INSERT` | `2` | 并行处理文档数，建议不超过 `MAX_ASYNC / 2` |
| `CHUNK_SIZE` | `1200` | 文档切块大小，推荐范围 500～1500 |
| `CHUNK_OVERLAP_SIZE` | `100` | 相邻文本块重叠大小 |
| `TIMEOUT` | `240` | 模型请求超时秒数 |
| `LIGHTRAG_API_KEY` | 未启用 | 对外部署时建议设置 API 访问密钥 |

> 系统环境变量的优先级高于 `.env`。修改 `.env` 后若发现未生效，请关闭当前终端并打开新终端，然后重新启动服务。

## 6. 运行方式一：源码 + Python 虚拟环境（推荐开发使用）

### 6.1 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
```

如果 PowerShell 禁止执行激活脚本，可仅对当前用户放开签名脚本：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Linux/macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

### 6.2 安装项目及 API 依赖

```bash
python -m pip install -e ".[api]"
```

验证安装：

```bash
lightrag-server --help
python -c "import lightrag; print(lightrag.__version__)"
```

项目通过 `pipmaster` 在需要时安装部分存储或模型适配依赖。若首次启动时出现缺少特定后端包的提示，按错误信息安装对应依赖后重启。

### 6.3 启动服务

```bash
lightrag-server
```

也可以直接通过模块启动：

```bash
python -m lightrag.api.lightrag_server
```

常用启动参数示例：

```bash
lightrag-server --host 0.0.0.0 --port 9621 --log-level INFO
```

Linux 生产环境可以使用多进程模式；Windows 不支持 Gunicorn：

```bash
lightrag-gunicorn --workers 4
```

首次启动会在启动目录创建默认的 `inputs/` 和 `rag_storage/`。终端需要保持运行。

## 7. 运行方式二：Docker Compose（推荐快速部署）

### 7.1 准备挂载文件和目录

项目的 Compose 文件会挂载 `.env`、`config.ini` 以及两个数据目录。必须先创建实际文件，避免 Docker 将不存在的文件路径创建为目录。

Windows PowerShell：

```powershell
Copy-Item env.example .env
Copy-Item config.ini.example config.ini
New-Item -ItemType Directory -Force data\rag_storage, data\inputs
```

Linux/macOS：

```bash
cp env.example .env
cp config.ini.example config.ini
mkdir -p data/rag_storage data/inputs
```

如果只使用默认本地文件存储，`config.ini` 保留模板内容即可；只有改用 Neo4j、PostgreSQL、MongoDB、Redis、Qdrant 等外部存储时才需要配置相应连接。

### 7.2 启动

使用当前源码构建镜像并后台运行：

```bash
docker compose up -d --build
```

查看状态和日志：

```bash
docker compose ps
docker compose logs -f lightrag
```

如果希望直接使用 Compose 中指定的远程镜像，可执行：

```bash
docker compose pull
docker compose up -d
```

容器内数据位置为 `/app/data/rag_storage` 和 `/app/data/inputs`，分别持久化到宿主机 `data/rag_storage/` 与 `data/inputs/`。

## 8. 验证服务

服务默认地址如下：

- WebUI：<http://localhost:9621/webui>
- 根地址：<http://localhost:9621/>，会跳转至 WebUI
- 健康检查：<http://localhost:9621/health>
- Swagger API 文档：<http://localhost:9621/docs>
- OpenAPI 定义：<http://localhost:9621/openapi.json>

命令行健康检查：

```bash
curl http://localhost:9621/health
```

Windows PowerShell 也可以使用：

```powershell
Invoke-RestMethod http://localhost:9621/health
```

若启用了 `LIGHTRAG_API_KEY`，调用受保护接口时添加请求头：

```text
X-API-Key: 你的密钥
```

## 9. 导入文档并建立索引

### 9.1 使用 WebUI（最简单）

1. 打开 <http://localhost:9621/webui>。
2. 进入文档管理页面。
3. 上传项目支持的文档，等待后台处理完成。
4. 在文档列表中确认状态已完成，再开始查询。

索引过程会调用 LLM 和 Embedding，耗时取决于文档长度、模型速度及并发参数。上传接口返回成功只表示任务已进入后台，不表示索引已经完成。

### 9.2 扫描输入目录

源码运行时，将文件放入 `inputs/`；Docker 运行时，将文件放入 `data/inputs/`。然后调用：

```bash
curl -X POST http://localhost:9621/documents/scan
```

也可以启动时自动扫描：

```bash
lightrag-server --auto-scan-at-startup
```

### 9.3 通过 API 写入纯文本

```bash
curl -X POST http://localhost:9621/documents/text \
  -H "Content-Type: application/json" \
  -d '{"text":"LightRAG 是一个结合向量检索与知识图谱的 RAG 系统。","file_source":"manual-input"}'
```

PowerShell 示例：

```powershell
$body = @{
    text = "LightRAG 是一个结合向量检索与知识图谱的 RAG 系统。"
    file_source = "manual-input"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:9621/documents/text `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## 10. 执行查询

### 10.1 使用 WebUI

在 WebUI 的检索页面输入问题，并选择查询模式：

- `naive`：只做普通文本块检索；
- `local`：偏重实体邻域和局部关系；
- `global`：偏重全局关系和主题；
- `hybrid`：结合 local 与 global；
- `mix`：结合知识图谱与向量检索，通常适合作为默认选择；
- `bypass`：跳过 RAG，直接请求底层 LLM。

### 10.2 使用 API

```bash
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d '{"query":"这批文档的核心内容是什么？","mode":"mix","response_type":"Multiple Paragraphs"}'
```

PowerShell 示例：

```powershell
$body = @{
    query = "这批文档的核心内容是什么？"
    mode = "mix"
    response_type = "Multiple Paragraphs"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:9621/query `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

流式查询接口为 `POST /query/stream`。完整请求字段和响应结构以 <http://localhost:9621/docs> 中当前运行版本的定义为准。

## 11. 独立开发 WebUI（可选）

API 已内置可用 WebUI，只有修改 React 前端源码时才执行本节。

```bash
cd lightrag_webui
```

复制开发环境配置：

Windows PowerShell：

```powershell
Copy-Item env.local.sample .env.local
npm install
npm run dev-no-bun
```

Linux/macOS：

```bash
cp env.local.sample .env.local
npm install
npm run dev-no-bun
```

`.env.local` 默认将请求代理到 `http://localhost:9621`，因此后端 API 必须同时运行。使用 Bun 时可改为：

```bash
bun install
bun run dev
```

构建前端：

```bash
npm run build-no-bun
```

## 12. 存储配置与数据安全

当前代码默认使用无需外部数据库的本地存储：

- KV：`JsonKVStorage`
- 向量库：`NanoVectorDBStorage`
- 图存储：`NetworkXStorage`
- 文档状态：`JsonDocStatusStorage`

适合本地测试和小规模使用。生产环境可在 `.env` 中选择 PostgreSQL、Neo4j、MongoDB、Milvus、Qdrant、Redis 等实现，并在 `config.ini` 或环境变量中补充连接信息。

例如统一使用 PostgreSQL 存储：

```dotenv
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
LIGHTRAG_GRAPH_STORAGE=PGGraphStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage
```

重要限制：

- 在首次写入文档前确定存储实现；已有数据后不要直接切换存储类型。
- 建好索引后不要随意修改 `EMBEDDING_MODEL` 或 `EMBEDDING_DIM`，否则新旧向量不兼容。
- 调整嵌入模型、维度或底层存储时，应使用新的空工作目录重新建库。
- 定期备份 `.env`（安全保存，不进入 Git）、`config.ini` 和持久化数据目录。

## 13. 停止、重启与更新

### 13.1 源码方式

前台运行时按 `Ctrl+C` 停止。重新启动前激活虚拟环境：

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
lightrag-server
```

Linux/macOS：

```bash
source .venv/bin/activate
lightrag-server
```

更新依赖：

```bash
git pull
python -m pip install -e ".[api]" --upgrade
```

### 13.2 Docker 方式

```bash
docker compose stop
docker compose start
docker compose restart
docker compose down
```

`docker compose down` 会删除容器和默认网络，但当前 Compose 的数据位于宿主机挂载目录，不会随容器删除。更新后重建：

```bash
git pull
docker compose up -d --build
```

## 14. 常见问题排查

### 14.1 端口 9621 被占用

修改 `.env` 中的 `PORT`，例如：

```dotenv
PORT=9622
```

源码方式也可临时运行：

```bash
lightrag-server --port 9622
```

### 14.2 无法连接 Ollama

先检查 Ollama：

```bash
ollama list
curl http://localhost:11434/api/tags
```

Docker 中不能用 `localhost` 访问宿主机 Ollama，应使用 `host.docker.internal`。Linux Docker 已在当前 Compose 中配置 `host-gateway` 映射。

### 14.3 模型不存在或名称错误

```bash
ollama list
ollama pull bge-m3
ollama pull mistral-nemo
```

确保 `.env` 的名称与 `ollama list` 输出一致，包括标签。

### 14.4 OpenAI 返回 401、403 或 404

- 401/403：检查 Key、账号权限或代理平台鉴权方式。
- 404：检查 Base URL 是否包含正确的 `/v1`，模型名是否由该平台提供。
- 同时检查终端中是否存在覆盖 `.env` 的旧系统环境变量。

### 14.5 Embedding 维度不匹配

确认 `EMBEDDING_DIM` 与服务真实输出一致。若已经用错误维度生成部分索引，应停止服务，换用新的空工作目录重新索引；不要把不同维度的数据混在同一个库中。

### 14.6 上传成功但查询不到内容

- 上传是后台任务，等待文档状态完成后再查询。
- 查看服务日志中是否有 LLM 超时、限流或模型上下文不足。
- 检查 Embedding 服务是否可访问。
- 先用 `naive` 或 `mix` 模式测试，再调整 `TOP_K`、`COSINE_THRESHOLD` 等检索参数。

### 14.7 Docker 启动时提示挂载错误

确认项目根目录中的 `.env` 和 `config.ini` 都是文件而不是目录。如果此前 Docker 自动创建了同名目录，应停止 Compose，移走同名目录，再从示例文件复制生成正确文件。

### 14.8 修改 `.env` 后未生效

停止服务，关闭旧终端，打开新终端后重新启动。Docker 方式执行：

```bash
docker compose down
docker compose up -d
```

## 15. 上线前检查清单

- [ ] Python 或 Docker 版本检查通过。
- [ ] `.env` 已创建，且未提交真实密钥。
- [ ] LLM 与 Embedding 的 Host、模型名、Key 均正确。
- [ ] `EMBEDDING_DIM` 与嵌入模型真实维度一致。
- [ ] Docker 部署时已创建 `config.ini` 和数据目录。
- [ ] `/health` 返回正常，WebUI 可以打开。
- [ ] 测试文档成功入库，状态处理完成。
- [ ] `POST /query` 能返回与测试文档相关的答案。
- [ ] 对外开放时已设置 `LIGHTRAG_API_KEY` 或登录认证，并限制防火墙端口。
- [ ] 已规划持久化目录备份和日志轮转。

完成以上步骤后，LightRAG 即具备从文档导入、知识图谱与向量索引构建，到 WebUI/API 检索问答的完整运行能力。
