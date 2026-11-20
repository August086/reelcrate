# ReelCrate

> Keep the good frames. 把好视频，收进匣子。

[GitHub](https://github.com/August086/reelcrate) · [Release v1.2.0](https://github.com/August086/reelcrate/releases/tag/v1.2.0) · [验收报告](docs/验收报告.md)

粘贴一个链接，提取原画质视频与字幕，再用 AI 把长视频读成五分钟。前端是电影感的工作台，后端直接封装 yt-dlp，不引入数据库和任务队列。

## 功能

- **多平台解析**：yt-dlp 覆盖 1800+ 站点，已验证 B 站、TED、通用 MP4 直链；YouTube 代码支持但当前开发网络不可达。
- **代理优先下载**：服务端下载 / 合并后提供文件，支持进度、中文文件名、临时文件清理。单文件格式可另取直链。
- **B 站适配**：公开 Web API + WBI 签名 + buvid 引导；有登录 Cookie 时优先人工 CC / B 站 AI 字幕，匿名最高约 480P。
- **无字幕兜底**：平台没有字幕时，可手动触发本地 Whisper 语音转写；音频不上传，转写后可正常总结、导图、问答和导出字幕。
- **AI 精读**：字幕提取 → DeepSeek 流式总结 → 思维导图 → 基于字幕的追问。
- **字幕导出**：SRT / VTT / TXT 三种格式，带时间戳。
- **导图导出**：可交互 markmap，全屏、SVG、4K PNG（实测 3840×2528）。
- **移动端适配**：390px 宽度无横向滚动，格式网格与下载入口可用。
- **不做假数据**：没有配置 DeepSeek Key 时只提取字幕，不伪造 AI 结果。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Tailwind CSS 3 + markmap + html-to-image |
| 后端 | FastAPI + yt-dlp + imageio-ffmpeg + OpenAI SDK |
| 文本模型 | DeepSeek（OpenAI 兼容协议，可用任意兼容服务替换） |
| 语音模型 | faster-whisper small（本地 CPU，ModelScope 下载；可切 medium） |
| 存储 | 无数据库；下载临时目录 + 30 分钟 TTL |
| 字体 | Space Grotesk Variable + 中文系统字体 |

## 快速启动

### 1. 配置

```powershell
cd backend
Copy-Item .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

`.env` 不会被提交。AI 不是必填；不填时字幕仍可用。

### 2. 后端

在仓库根目录：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

`imageio-ffmpeg` 自带 ffmpeg 二进制，无需系统安装 ffmpeg。首次使用无字幕转写时会自动下载 Whisper 模型；也可以提前下载：

```powershell
.\.venv\Scripts\python.exe backend\download_asr.py
```

默认模型 `small` 约 486MB，缓存到 `backend/models/`（已 gitignore）。

### 3. 前端开发

```powershell
cd frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173`。Vite 会把 `/api` 代理到 `127.0.0.1:8000`。

### 4. 生产 / 验收

```powershell
cd frontend
npm run build

cd ..\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

打开 `http://127.0.0.1:8000`，前端由 FastAPI 直接托管，同源请求 API。

也可以从仓库根目录一键启动：

```powershell
.\start.ps1
```

Linux / macOS：

```bash
./start.sh
```

## 配置项

| 变量 | 必填 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | AI 必填 | DeepSeek Key |
| `DEEPSEEK_BASE_URL` | 否 | 默认 `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 否 | 默认 `deepseek-chat` |
| `BILIBILI_SESSDATA` | 否 | B 站登录 Cookie，解锁高画质 / CC 字幕 |
| `BILIBILI_COOKIE` | 否 | 完整 B 站 Cookie，优先于上项 |
| `YTDLP_COOKIEFILE` | 否 | Netscape 格式 cookies.txt，供 YouTube 等使用 |
| `ASR_ENABLED` | 否 | 默认 true；关闭后不提供本地语音转写 |
| `ASR_MODEL` | 否 | `small`（默认）或 `medium`（更准、更慢、约 1.5GB） |
| `ASR_AUTO` | 否 | 默认 false；true 时无字幕视频自动开始转写 |
| `ASR_MAX_DURATION_MIN` | 否 | 默认 60 分钟，超过直接拒绝 |
| `ASR_CPU_THREADS` | 否 | 默认 8；CPU 推理线程数 |
| `MAX_FILE_SIZE_MB` | 否 | 默认 2048 |
| `MAX_CONCURRENT_DOWNLOADS` | 否 | 默认 2 |
| `JOB_TTL_SECONDS` | 否 | 默认 1800 秒后清理任务文件 |

## 主要 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/config` | AI / 平台能力 |
| POST | `/api/parse` | `{ url }` → 视频信息 + 格式 |
| POST | `/api/downloads` | 创建代理下载任务 |
| GET | `/api/downloads/{id}` | 任务状态 / 进度 |
| GET | `/api/downloads/{id}/file` | 下载文件 |
| POST | `/api/direct-url` | 单文件直链探测 |
| POST | `/api/summarize` | SSE：subtitle → summary → mindmap → done；`allow_asr=true` 启用无字幕转写 |
| POST | `/api/chat` | SSE：answer → done |

接口文档：`http://127.0.0.1:8000/api/docs`

## 实现要点

- **下载任务制**：`POST /api/downloads` 立即返回 `job_id`，后台线程下载 / 合并，前端轮询进度，完成后浏览器请求文件。避免把整部视频读进内存。
- **B 站**：`finger/spi` 获取 buvid → `view` → WBI `playurl` → DASH 视频/音频分别下载 → ffmpeg `-c copy` 合并。CDN 失败自动切 `backupUrl`。
- **TED 字幕**：yt-dlp 返回的是 HLS 字幕播放列表，后端解析 m3u8、并发拉取 38 个 VTT 分片，按时间轴合并（约 10 秒），并做连续重复字幕去重。
- **三级字幕兜底**：平台人工字幕 → B 站 AI 字幕（`ai-zh` 优先）→ 本地 Whisper。Whisper 下载音频、ffmpeg 转 16k PCM、单模型互斥推理、SSE 推送进度；转写结果复用现有字幕导出与 AI 流程。
- **AI**：SSE token 用 JSON 编码，换行不会被协议拆断；总结与导图分两次调用；Markdown 经 DOMPurify 清洗。
- **安全**：只允许 http/https；解析域名并拒绝内网 / 回环 / 元数据地址；文件大小与并发限制；临时文件自动清理。

## 测试

在仓库根目录：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

当前 23 个单元测试覆盖 URL 校验、私网拦截、文件名、VTT/SRT/JSON3/JSON 字幕解析、语言选择、截断、格式估算、SSE 编码、B 站字幕优先、B 站仅音频选择与 ASR 元数据。真实模型与真实下载的验收结果见 `docs/验收报告.md`。

本机已完成真实链路验收：B 站 360P 下载 14,767,133 字节并合并；TED 391 条字幕；真实 DeepSeek 生成 710 字总结、344 字导图与问答；SRT 30,481 字节；PNG 3840×2528。无字幕 B 站视频 `BV1JdNy63EJL`（9:35）经本地 Whisper 生成 312 条字幕、5865 字文本，再生成 900 字总结与 372 字导图，端到端约 123.6 秒。详细证据见 `docs/验收报告.md`。

手工验收建议：

1. B 站：`https://www.bilibili.com/video/BV1GJ411x7h7/` → 选择 360P → 下载 → 检查文件可播放。
2. TED：`https://www.ted.com/talks/chimamanda_ngozi_adichie_the_danger_of_a_single_story` → 等字幕 → 总结 / 导图 / 问答 → 导出 SRT 与 4K PNG。
3. 无字幕：`https://www.bilibili.com/video/BV1JdNy63EJL/` → 点击「开始语音转写」→ 等本地 Whisper → 导出 SRT / 查看总结。
4. 移动端：390px 宽度检查无横向滚动、格式选择、下载入口、语音转写入口。

## 已知限制

- YouTube 在当前开发网络不可达，代码路径已保留，未做真实链路验证。
- Vimeo 未登录时被平台拒绝解析。
- B 站匿名解析通常最高 480P；CC / AI 字幕需要登录 Cookie。番剧 / 课程未做适配。
- 本地 Whisper 首次需下载约 486MB 模型；9:35 视频约 1.5-2 分钟，60 分钟视频可能约 10 分钟；机器转写可能有错字。
- 直链受平台防盗链影响，失败时请使用代理下载。
- 批量下载、用户系统、支付为后续规划；当前定价区是产品占位，不收费。

## 目录

```
backend/          FastAPI、yt-dlp、B 站适配、ASR、AI、测试
backend/models/   Whisper 模型缓存（gitignore）
frontend/         Vue 3 + Vite + Tailwind
docs/             需求、方案评审、字幕兜底方案、验收报告
start.ps1         Windows 一键启动
start.sh          Linux/macOS 一键启动
```

## 免责声明

本项目仅用于个人学习与内容备份。请遵守目标平台的服务条款与版权规定，不要用于未授权的批量采集或商业分发。工具不存储视频文件与观看记录，临时文件会在任务结束后自动清理。

## License

MIT。第三方依赖（yt-dlp、Vue、FastAPI、Whisper 等）保留各自许可证。

