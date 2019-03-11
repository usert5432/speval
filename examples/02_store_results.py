import time
import random

from speval import speval

def func(arg):
    random.seed(time.time())
    result = random.random()

    print("Returning result '%g' from eval %d" % (result, arg))
    time.sleep(1)

    return result

eval_space = list(range(100))

speval(func, eval_space, "/tmp/02_store_results.db", timeout = 60)
