import argparse

from speval import load_evals

parser = argparse.ArgumentParser("linear regression")
parser.add_argument(
    'method', metavar = 'METHOD', type = str, choices = [ 'rand', 'grid' ],
    nargs = '?', default = 'rand', help = 'Search Method'
)

args = parser.parse_args()


evals = load_evals("/tmp/03_fit_line_%s.db" % (args.method))

if evals is None:
    raise RuntimeError("Failed to load evals")

# Remove not completed evals
evals = [ e for e in evals if e['result'] is not None]

evals.sort(key = lambda e : e['result'])

a, b = evals[0]['args'].values()

print("Best parameters found a = %g, b = %g" % (a, b))
print("True parameters were  a = %g, b = %g" % (123, 456))
print("Objective function value = %e" % (evals[0]['result']))
