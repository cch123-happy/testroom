from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# 存储所有活跃的 WebSocket 连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# WebSocket 路由
@app.websocket("/ws/{client_name}")
async def websocket_chat(websocket: WebSocket, client_name: str):
    await manager.connect(websocket)
    await manager.broadcast(f"【{client_name}】加入了聊天室")

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_name}:{data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"【{client_name}】离开了聊天室")

# 前端页面（测试用）
@app.get("/")
async def get():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>聊天室</title>
    <style>
        #messages { height: 300px; border: 1px solid #ccc; overflow-y: scroll; }
    </style>
</head>
<body>
    <h1>FastAPI 聊天室</h1>
    
    <!-- 1. 用户名输入区 -->
    <div id="login">
        <input type="text" id="username" placeholder="输入你的名字" />
        <button onclick="connect()">加入聊天</button>
    </div>

    <!-- 2. 聊天区（默认隐藏） -->
    <div id="chat" style="display:none">
        <div id="messages"></div>
        <input type="text" id="message" placeholder="输入消息" />
        <button onclick="send()">发送</button>
    </div>

    <script>
        let ws;  // 存储 WebSocket 连接

        // 连接 WebSocket
        function connect() {
            const username = document.getElementById("username").value;
            if (!username) return alert("请输入名字！");

            // 连接 FastAPI 的 WebSocket 路由
            ws = new WebSocket(`ws://${location.host}/ws/${username}`);

            // 接收消息时的处理
            ws.onmessage = (event) => {
                const messages = document.getElementById("messages");
                messages.innerHTML += `<div>${event.data}</div>`;
                messages.scrollTop = messages.scrollHeight;  // 自动滚动到底部
            };

            // 显示聊天区，隐藏登录区
            document.getElementById("login").style.display = "none";
            document.getElementById("chat").style.display = "block";
        }

        // 发送消息
        function send() {
            const message = document.getElementById("message").value;
            if (!message) return;

            ws.send(message);  // 通过 WebSocket 发送消息
            document.getElementById("message").value = "";  // 清空输入框
        }

        // 按回车发送消息
        document.getElementById("message").addEventListener("keyup", (e) => {
            if (e.key === "Enter") send();
        });
    </script>
</body>
</html>
    """)