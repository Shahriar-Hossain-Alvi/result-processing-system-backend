# this project is using python 3.12 interpreter
from fastapi import FastAPI
import uvicorn

app = FastAPI()



if __name__ == "__main__":
    # asyncio.run(init_db())
    uvicorn.run(app, host="0.0.0.0", port=8000)
