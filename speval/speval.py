import json
import os

import sqlite3
import time

import logging
logger = logging.getLogger('speval')



def deserialize_json_value(value):
    """Deserialize json ``value`` paying special attention to corner cases

    Parameters
    ----------
    value : `str` or None
        json document to deserialize

    Returns
    -------
    object
        deserialized ``value``
    """

    if (value is None) or (value == ''):
        return value

    return json.loads(value)


def connect_evals(fname):
    """Opens exclusive connection to a sqlite3 database.

    Parameters
    ----------
    fname : `str`
        file name of sqlite3 database

    Returns
    -------
    connection : `sqlite3.Connection`
        Connection object to a sqlite database
    """
    conn = sqlite3.connect(fname, isolation_level = 'EXCLUSIVE')
    conn.execute('BEGIN EXCLUSIVE')

    return conn


def load_evals(fname):
    """Returns a list of evaluations extracted from sqlite database

    This is useful helper function for easily retrieving information from
    the sqlite database.

    Parameters
    ----------
    fname : `str`
        file name of sqlite3 database

    Returns
    -------
    evaluations : `list` of `dict`
        List of evaluations where each evaluation is a dictionary of
            ``"name"``
                Name of evaluation
            ``"status"`` : { 'pending', 'completed', 'in_progress' }
                status of evaluation
            ``"updated"`` : `int`
                time of the last evaluation change as unix timestamp
            ``"result"``
                result of the evaluation
            ``"args"``
                arguments passed to evaluation
    """

    conn = sqlite3.connect(fname)

    evals = []

    for (name,status,updated,result,args) in conn.execute(
        'SELECT * FROM evals'
    ):
        evals.append({
            'name'    : name,
            'status'  : status,
            'updated' : updated,
            'result'  : deserialize_json_value(result),
            'args'    : deserialize_json_value(args),
        })

    conn.close()

    return evals


def init_evals(conn, eval_space):
    """Initializes sqlite table for storing evaluations.

    Notes
    -----
    This function assumes that evals table has not been created/populated.

    Parameters
    ----------
    conn : `sqlite3.Connection`
        connection to a sqlite3 database
    eval_space : `dict`
        dictionary describing evaluation space where keys are names of
        evaluations and values are the arguments that will be passed to
        evaluation function

    """

    conn.execute('''
CREATE TABLE evals (
    name TEXT, status TEXT, updated INTEGER, result TEXT, args TEXT
)
''')

    keys = list(eval_space.keys())
    keys.sort()

    for k in keys:
        conn.execute(
            'INSERT INTO evals VALUES (?,?,?,?,?)',
            (k, 'pending', time.time(), None, json.dumps(eval_space[k]))
        )


def check_evals_initialized(conn):
    """Check that evals table has been created in a sqlite3 database

    Parameters
    ----------
    conn : `sqlite3.Connection`
        connection to a sqlite3 database

    Returns
    -------
    is_created : `bool`
        `True` if table was created and `False` otherwise

    """

    cur = conn.execute(
        '''SELECT name FROM sqlite_master WHERE type='table' AND name=?''',
        ('evals',)
    )

    return not (cur.fetchone() is None)


def reset_stalled_evals(conn, timeout):
    """Check that evals table has been created in a sqlite3 database

    Parameters
    ----------
    conn : `sqlite3.Connection`
        connection to a sqlite3 database
    timeout : `int` or `None`
        number of seconds after which evaluation is considered stalled.
        If ``timeout`` is `None` this functions does nothing.

    """

    if timeout is None:
        return

    current_time = time.time()

    if logger.getEffectiveLevel() <= logging.INFO:
        cur = conn.execute(
            ''' SELECT name,updated
                FROM evals
                WHERE updated < ? AND status = 'in_progress' ''',
            (current_time - timeout, )
        )

        for (name, updated) in cur:

            inactive_time = current_time - updated

            logger.info(
                "Found stalled eval: %s, which was inactive for %d seconds."
                " Resetting.", name, inactive_time
            )

    conn.execute(
        ''' UPDATE evals
            SET status = 'pending', updated = ?
            WHERE updated < ? AND status = 'in_progress' ''',
        (current_time, current_time - timeout)
    )


def grab_pending_eval(conn):
    """Selects 'pending' evaluation from an sqlite3 database, then sets its
       status to 'in_progress' and last updated time to current time.

    Notes
    -----
    This function is not atomic. The database should be locked properly to
    avoid race conditions.

    Parameters
    ----------
    conn : `sqlite3.Connection`
        connection to a sqlite3 database

    Returns
    -------
    name
        name of the selected evaluation
    args
        arguments of the selected evaluation
    found : `bool`
        flag indicating whether 'pending' evaluation was found
    """

    name  = None
    args  = None
    found = False

    cur = conn.execute(
        '''SELECT name,args FROM evals WHERE status='pending' LIMIT 1'''
    )

    result = cur.fetchone()

    if result is None:
        return (name, args, found)

    name  = result[0]
    args  = deserialize_json_value(result[1])
    found = True

    conn.execute(
        '''UPDATE evals SET status='in_progress',updated=? WHERE name=?''',
        (time.time(), name, )
    )

    return (name, args, found)


def get_pending_eval(fname, eval_space, timeout = None):
    """Opens sqlite3 database and finds still 'pending' evaluation.

    If database have not been initialized yet this function will populate it
    with entries from `eval_space`. Also, if `timeout` is not none this
    function will review evaluation that are currently 'in_progress' and
    reset them back to 'pending' state if they have not been updated longer
    then `timeout` seconds.

    Parameters
    ----------
    fname : `str`
        file name of sqlite3 database
    eval_space : `dict`
        dictionary describing evaluation space where keys are names of
        evaluations and values are the arguments that will be passed to
        evaluation function
    timeout : `int` or `None`
        number of seconds after which evaluation is considered stalled.

    Returns
    -------
    name
        name of the 'pending' evaluation
    args
        arguments of the 'pending' evaluation
    found : `bool`
        flag indicating whether 'pending' evaluation was found
    """

    conn = connect_evals(fname)

    if not check_evals_initialized(conn):
        logger.info("Initializing evals...")
        init_evals(conn, eval_space)

    logger.debug("Resetting stalled evals...")
    reset_stalled_evals(conn, timeout)

    logger.debug("Finding pending eval...")
    (name, conf, found) = grab_pending_eval(conn)

    if found:
        logger.info("Found pending eval '%s'", name)

    conn.commit()
    conn.close()

    return (name, conf, found)


def save_eval_result(fname, name, result):
    """Opens sqlite3 database and updates result of evaluation with given name.

    Parameters
    ----------
    fname : `str`
        file name of sqlite3 database
    name
        evaluation name
    result
        evaluation result
    """

    conn = connect_evals(fname)

    if not check_evals_initialized(conn):
        raise RuntimeError("Database is not initialized")

    current_time = time.time()

    conn.execute(
        '''UPDATE evals
           SET status = 'completed', updated = ?, result = ?
           WHERE name = ?
        ''',
        (current_time, json.dumps(result), name)
    )

    conn.commit()
    conn.close()


def speval(func, eval_space, evals_fname, timeout = None):
    """Evaluates function ``func`` over each entry in ``eval_space``.

    This function opens connection a sqlite3 database ``evals_fname``.
    If the database does not exist it first populates db from ``eval_space``.

    Then as long as there is any non evaluated configuration left in the
    database this function calls ``func`` with corresponding configuration,
    and saves result returned by the ``func`` back into the database.

    Parameters
    ----------
    func : callable
        function that will be called for with arguments from each item
        in ``eval_space``
    eval_space : `list` or `dict`
        `list` of evaluation arguments or `dict` where keys are names
        of the evaluation and values are the evaluation arguments
    evals_fname : `str`
        file name of sqlite3 database
    timeout : `int`, optional
        number of seconds after which evaluation is considered stalled.

    See also
    --------
    load_evals
        function to easily retrieve evaluation results from the
        ``evals_fname`` sqlite3 database.
    """


    os.makedirs(os.path.dirname(evals_fname), exist_ok = True)

    if isinstance(eval_space, list):
        eval_space = { idx : v for (idx,v) in enumerate(eval_space) }

    while True:
        name, conf, found = get_pending_eval(evals_fname, eval_space, timeout)

        if not found:
            logging.info("No more pending evals")
            break

        result = func(conf)

        save_eval_result(evals_fname, name, result)


