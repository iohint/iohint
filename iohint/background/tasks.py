from . import app

@app.task
def add(x, y):
    print('executing add, woot', x, y)
    return x + y

@app.task
def mul(x, y):
    return x * y
