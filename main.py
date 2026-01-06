from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from routers import ctrl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DETECTION_PIC_DIR = os.path.join(
    BASE_DIR,
    r"draw-cushion-pins-detection/PinsCtrlData/DetectionRecords/DetectionPictures"
)

app = FastAPI()

########################################################################
# 加载静态文件
########################################################################
app.mount("/statics", StaticFiles(directory="statics", html=True), name="statics")
app.mount("/images", StaticFiles(directory=DETECTION_PIC_DIR), name="images")

app.include_router(ctrl.router, prefix="/ctrl")

@app.get("/")
async def index(request: Request):
    return RedirectResponse("/ctrl")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
