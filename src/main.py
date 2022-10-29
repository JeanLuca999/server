from fastapi import FastAPI

app = FastAPI()


@app.post("/register")
def register():
    pass


@app.post("/login")
def login():
    pass
