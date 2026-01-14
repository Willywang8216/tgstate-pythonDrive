# tgState-Python

**基于 Telegram 的无限私有云存储 & 永久图床系统**

将您的 Telegram 频道或群组瞬间变身为功能强大的私有网盘与图床。无需服务器存储空间，借助 Telegram 的无限云端能力，实现文件管理、外链分享、图片托管等功能。

---

## 🚀 一键部署

无需下载代码，无需手动安装环境，只需一台安装了 Docker 的服务器（Linux/Windows/Mac 均可）。

### 1️⃣ 默认一键安装（推荐）
默认使用 **8000** 端口，从 GHCR 拉取最新镜像，并持久化数据。

```bash
docker volume create tgstate-data >/dev/null 2>&1; docker rm -f tgstate 2>/dev/null || true; docker pull ghcr.io/buyi06/tgstate-python:latest && docker run -d --name tgstate --restart unless-stopped -p 8000:8000 -v tgstate-data:/app/data ghcr.io/buyi06/tgstate-python:latest
```

**✅ 部署成功后：**
请在浏览器访问：`http://您的服务器IP:8000`

---

### 🛠️ 备用端口示例
如果您的 **8000** 端口不通或已被占用，可以使用以下命令改为 **15767** 端口：

```bash
docker volume create tgstate-data >/dev/null 2>&1; docker rm -f tgstate 2>/dev/null || true; docker pull ghcr.io/buyi06/tgstate-python:latest && docker run -d --name tgstate --restart unless-stopped -p 15767:8000 -v tgstate-data:/app/data ghcr.io/buyi06/tgstate-python:latest
```

---

## ⚙️ 首次配置教程

部署后首次访问网页，会进入“引导页”设置管理员密码。之后请进入 **“系统设置”** 完成核心配置。

### 第一步：获取 BOT_TOKEN
1.  在 Telegram 搜索 **[@BotFather](https://t.me/BotFather)** 并点击“开始”。
2.  发送指令 `/newbot` 创建新机器人。
3.  按提示输入 Name（名字）和 Username（用户名，必须以 `bot` 结尾）。
4.  成功后，复制 **HTTP API Token**（即 `BOT_TOKEN`）。

### 第二步：获取 Chat ID (CHANNEL_NAME)
1.  **准备群组/频道**：
    *   您可以新建一个群组或频道（公开或私密均可）。
    *   **关键操作**：必须将您的机器人拉入该群组/频道，并设为**管理员**（给予所有权限）。
2.  **获取 ID**：
    *   在群组/频道内随便发送一条文本消息。
    *   在浏览器访问：`https://api.telegram.org/bot<您的Token>/getUpdates`
        *   *请将 `<您的Token>` 替换为实际的 BOT_TOKEN。*
    *   查看返回的 JSON，找到 `chat` 字段下的 `id`。
        *   通常是以 `-100` 开头的数字（例如 `-1001234567890`）。
    *   **如果是公开频道**：也可以直接使用频道用户名（例如 `@my_channel_name`）。

> **💡 提示**：如果 `getUpdates` 返回空 (`"result": []`)，请尝试在群里多发几条消息，或者去 @BotFather 关闭机器人的 Group Privacy 模式。

### 第三步：填写配置
回到网页的“系统设置”，填入：
*   **BOT_TOKEN**: 第一步获取的 Token。
*   **CHANNEL_NAME**: 第二步获取的 Chat ID（推荐使用数字 ID）。
*   **BASE_URL** (可选): 您的访问域名或 IP（例如 `http://1.2.3.4:8000` 或 `https://pan.example.com`），用于生成正确的文件分享链接。

保存后即可开始使用！

---

## 🌐 反向代理示例 (Caddy)

如果您使用 Caddy 作为反向代理，可以在您的 `Caddyfile` 中追加以下配置（仅供参考）：

```caddy
buyi.us.ci {
    encode gzip
    reverse_proxy 127.0.0.1:8000
}
```

*注意：请根据实际情况修改域名和端口。*

---

## 📂 功能特性
*   **无限存储**：依赖 Telegram 频道，容量无上限。
*   **短链接分享**：生成简洁的分享链接（`/d/xyz123`），自动适配当前访问域名。
*   **拖拽上传**：支持批量拖拽上传，大文件自动分块。
*   **图床模式**：支持 Markdown/HTML 格式一键复制，适配 PicGo。
*   **隐私安全**：所有数据存储在您的私有频道，Web 端支持密码保护。

---

## 📄 License
MIT License
