from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

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

# 前端页面
@app.get("/")
async def get():
    return FileResponse("static/index.html")

# 上传csv
@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    # 读取CSV文件内容
    contents = await file.read()
    
    # 使用pandas解析CSV（需安装pandas）
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

    with open (file.filename,"wb") as buff:
        buff.write(contents)
    
    # 转换为字典列表
    data = df.to_dict(orient="records")
    
    return JSONResponse({
        "filename": file.filename,
        "data": data  # 返回解析后的数据
    })