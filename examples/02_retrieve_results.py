import time

from speval import load_evals

evals = load_evals("/tmp/02_store_results.db")

for e in evals:
    if e['result'] is None:
        continue

    print("Evaluation %s. Completed on %s. Returned '%g'." % (
        e['name'],
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e['updated'])),
        e['result'],
    ))

