import uvicorn

if __name__ == "__main__":
    # Start uvicorn server listening on port 8000, autodetecting code modifications via reload=True
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
