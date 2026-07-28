# Python AI Learn

一组面向 Python AI 应用开发的入门示例，包含图像铅笔画转换、基于通义千问兼容接口的命令行问答，以及 Gradio 网页聊天界面。

## 项目总览

仓库包含两个独立的 Python 项目。根目录适合学习图像处理、提示词和 Gradio；`beambox-agent` 是一个可运行的企业资料研究 Agent，拥有自己的依赖、配置、知识库与测试。两个项目应分别创建虚拟环境和安装依赖。

| 项目 | 位置 | 适用场景 | 启动入口 |
| --- | --- | --- | --- |
| Python AI Learn 示例 | 仓库根目录 | 学习 Gradio、OpenCV、OpenAI 兼容接口 | `python test.py`、`python prompt.py`、`python call_qwen.py` |
| Beambox 企业资料 Agent | `beambox-agent/` | 查询本地知识库，必要时检索公开网页，并生成带来源的回答 | `beambox-agent`、`beambox-agent-web`、`beambox-kb` |

### Beambox 企业资料 Agent

该 Agent 面向深圳光胜人工智能科技有限公司及旗下 Beambox 品牌。它会优先检索随仓库提供的 SQLite 知识库；只有资料不足或问题要求最新信息时，才会搜索公开网页。回答中的链接必须来自实际工具结果，避免模型凭空编造来源。

进入子项目并单独安装：

```powershell
cd beambox-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

在 `beambox-agent/.env` 中配置 DashScope 兼容接口：

```dotenv
OPENAI_API_KEY=your_dashscope_api_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
```

常用命令：

```powershell
# 交互式终端问答
beambox-agent --verbose

# 启动 Gradio 网页界面
beambox-agent-web --port 7860 --inbrowser

# 查看随仓库提供的知识库覆盖情况
beambox-kb stats

# 运行 Agent 测试，不消耗模型额度
python -m unittest discover -s tests -v
```

完整的知识库维护、工具调用、来源约束和安全说明请见 [beambox-agent/README.md](beambox-agent/README.md)。

## 功能

| 示例 | 文件 | 说明 |
| --- | --- | --- |
| 图像转铅笔画 | `test.py` | 使用 OpenCV 和 NumPy 将上传的图片转换为灰度铅笔素描。 |
| 命令行上下文问答 | `prompt.py` | 将上下文与问题发送给 `qwen-plus`，演示基础提示词组织。 |
| 网页聊天 | `call_qwen.py` | 使用 Gradio `ChatInterface` 构建通义千问 `qwen-max` 聊天页面。 |
| Notebook | `prompt.ipynb` | 用于后续交互式实验的 Jupyter Notebook 占位文件。 |

## 环境要求

- Python 3.10 或更高版本
- 能访问 DashScope 兼容模式 API 的 API Key
- Windows PowerShell、macOS Terminal 或 Linux Shell

项目已在 Python 3.13 环境中配置和验证依赖。

## 安装

克隆仓库并进入目录：

```bash
git clone https://github.com/wzj1228516103/python-ai-learn.git
cd python-ai-learn
```

创建并激活虚拟环境。

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

安装依赖：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 配置 API Key

示例通过 `python-dotenv` 从项目根目录的 `.env` 文件读取密钥。先复制模板：

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

编辑 `.env`，填入自己的密钥：

```dotenv
OPENAI_API_KEY=your_api_key_here
```

`.env` 已被 Git 忽略，不会提交到仓库。不要将真实 API Key 写入源码、Notebook 或提交记录；如果密钥泄露，应立即在服务商控制台轮换。

也可以临时通过环境变量提供密钥。

Windows PowerShell：

```powershell
$env:OPENAI_API_KEY = "your_api_key_here"
```

macOS / Linux：

```bash
export OPENAI_API_KEY="your_api_key_here"
```

## 运行示例

### 图像转铅笔画

```bash
python test.py
```

终端会显示 Gradio 本地地址，通常为 `http://127.0.0.1:7860`。在页面上传图片即可获得素描结果。

核心流程位于 `image_to_sketch`：

1. 将 PIL 图片转为单通道灰度图。
2. 对灰度数组反相并进行高斯模糊。
3. 再次反相模糊结果。
4. 用 OpenCV 的 `divide` 混合原图与处理结果，突出边缘和线条。

### 命令行上下文问答

```bash
python prompt.py
```

脚本会把内置的 `instruction`、`context` 和 `query` 拼接成提示词，调用 DashScope 的 OpenAI 兼容接口，并在终端打印回答。默认模型为 `qwen-plus`。

### Gradio 聊天页面

```bash
python call_qwen.py
```

打开终端输出的本地地址，即可与默认的 `qwen-max` 模型对话。脚本会将 Gradio 提供的历史消息转换为 OpenAI Chat Completions 所需的 `messages` 列表。

### Jupyter Notebook

```bash
jupyter notebook
```

浏览器会打开 Jupyter 页面。新建或编辑 `prompt.ipynb` 后，选择该项目的 Python 虚拟环境作为内核。

## 项目结构

```text
python-ai-learn/
├── .env.example        # 环境变量模板，不包含真实密钥
├── .gitignore          # 忽略密钥、虚拟环境和缓存
├── call_qwen.py        # Gradio 通义千问聊天示例
├── prompt.ipynb        # Jupyter Notebook 实验文件
├── prompt.py           # 命令行上下文问答示例
├── requirements.txt    # Python 依赖及版本
├── test.py             # 图像转铅笔画 Gradio 应用
└── README.md
```

## 主要依赖

| 包 | 用途 |
| --- | --- |
| `gradio` | 快速创建图像和聊天网页界面。 |
| `numpy` | 高效处理图像的多维像素数组。 |
| `opencv-python` | 提供 `cv2` 图像处理功能，例如高斯模糊和图像混合。 |
| `openai` | 调用 OpenAI 兼容的 Chat Completions API。 |
| `python-dotenv` | 从 `.env` 文件读取 API Key 等环境变量。 |
| `notebook` | 提供 Jupyter Notebook 本地运行环境。 |
| `pandas` | 为数据处理实验预留的表格数据工具。 |

## 常见问题

### `ModuleNotFoundError`

通常是未激活虚拟环境，或依赖未安装。先激活 `.venv`，再执行：

```bash
python -m pip install -r requirements.txt
```

在 VS Code 中，请将 Python 解释器切换为项目中的 `.venv`。

### `OPENAI_API_KEY environment variable not set`

确认项目根目录存在 `.env`，并且其中的变量名必须为 `OPENAI_API_KEY`。修改 `.env` 后请重新启动脚本。

### API 请求失败

确认 API Key 有效、账户具有对应模型权限，并检查网络是否可以访问：

```text
https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 安全说明

- 不要提交 `.env`、虚拟环境或任何包含凭据的文件。
- 不要把 API Key 放在 Python 源码中。
- 共享截图、日志或 Notebook 前，检查其中是否含有密钥和个人信息。

## License

当前仓库尚未指定许可证。需要公开复用时，可根据用途添加 MIT、Apache-2.0 或其他合适的许可证。
