import time

from speval import speval

def func(arg):
    print("Hello world: %d" % (arg))
    time.sleep(2)

eval_space = list(range(100))

speval(func, eval_space, "/tmp/01_hello_world.db", timeout = 60)
