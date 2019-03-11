speval
======
Simple Parallel Function Evaluator for python.

``speval`` is a python package that allows one to easily parallelize multiple
evaluations of some time consuming function. ``speval`` is designed to have
no extra dependencies and be extra simple to use.


Usage
=====
Let say we have a long running function ``eval_me`` and we would like to
evaluate it 100 times, each time with different parameters. And, moreover
perform these evaluations in parallel. We can easily achieve this with a
simple python script of the form:

.. code-block:: python

   from speval import speval

   list_of_args = [
      args_for_eval1,
      args_for_eval2,
      ...
      args_for_eval100,
   ]

   speval(eval_me, list_of_args, db_name)

Now, we can run one instance of this script and it will start evaluating
function ``eval_me`` for each point of ``list_of_args``. To parallelize
evaluations we just need to run another ``N`` instances of this script, and
they are going to distribute evaluations of ``eval_me`` among them, using
sqlite3 database ``db_name`` for synchronization.

Once all evaluations are complete we can use function ``load_evals`` to
retrieve results(if any) of each evaluation from the database ``db_name``.


Motivation
==========
``speval`` was written because the author needed a simple hyperparameter
optimization package without heavy dependencies(like ``mongodb``), or need to
properly set up workers on multiple machines.


Requirements
============
``python-3`` built with sqlite3 support(enabled by default)


Examples
========

A number of examples is stored in the ``examples`` subdirectory. Here is a
brief overview of them.

01. Hello World
---------------
Let's start with a primitive function to evaluate

.. code-block:: python

   import time

   def func(arg):
       print("Hello world: %d" % (arg))
       time.sleep(2)

Say we want to evaluate function ``func`` 100 times using evaluation index as
an argument to ``func``. To perform this we first need to define a list with
arguments for each evaluation

.. code-block:: python

   eval_space = list(range(100))

And then call ``speval``

.. code-block:: python

   from speval import speval

   speval(func, eval_space, "/tmp/01_hello_world.db", timeout = 60)

Here we see that ``speval`` takes function to evaluate ``func`` as a first
argument, list with arguments for each evaluation ``eval_space`` as a second
argument. We also pass there a sqlite database file name
(``"/tmp/01_hello_world.db"``) which will be used for coordination between
different processes. And a ``timeout`` parameter which tells ``speval`` that a
given evaluation of function ``func`` has failed if it was not completed in 60
seconds and therefore needs to be restarted.

Done. Now we can run the resulting script(e.g. ``examples/01_hello_world.py``)
as many times in parallel as many jobs we want to allocate for the task of
printing "Hello world".

For example, on a unix system one may run in a terminal

.. code-block:: console

   $ python examples/01_hello_world.py
   Hello world: 0
   Hello world: 1
   Hello world: 2
   Hello world: 3
   Hello world: 4
   ...

So, it will print ``"Hello world: N"`` each 2 seconds, and without further
intervention will finish in about 200 seconds. To parallelize printing
we can run another say 20 jobs in a separate terminal. E.g.

.. code-block:: console

   $ for i in {1..20}; do (python examples/01_hello_world.py &) ; done

Now, all pending hello worlds will be printed in just about 10 seconds.


02. Storing/Retrieving Function Results
---------------------------------------

In ``examples`` directory there are 2 scripts ``02_store_results.py`` and
``02_retrieve_results.py``. First script is just a modification of the hello
world example, where function ``func`` also returns a value, which is
automatically stored in the database. Second script there is used to
demonstrate how to retrieve saved results from the database.


03. Using speval for Hyperparameter Optimization
------------------------------------------------

Finally, there are another 2 examples ``03_fit_line.py`` and
``03_get_best_fit.py``, which demonstrate how to use ``speval`` for
hyperparameter optimization over a predefined search space(grid search or
randomized search). Here the first script evaluates objective function on each
point of the search space. This script can be run on the multiple machines in
parallel, provided they all have access to a shared mount on which a sqlite3
database resides.

The second script is can be used to find optimal values of hyperparameters from
the results of these evaluations stored in the database.


Limitations
===========

``speval`` uses sqlite3 internal advisory file locking mechanism to prevent
race conditions. This mechanism is known not to work properly for some network
filesystem `setups`__. So be advised if your database is on NFS mount.

Additionally, ``speval`` relies on json format to serialize parameters. So,
you need to make sure that ``eval_space`` and results returned by the
``eval_func`` are json serializable objects.

.. _sqlite_locking: https://www.sqlite.org/lockingv3.html#how_to_corrupt
__ sqlite_locking_


