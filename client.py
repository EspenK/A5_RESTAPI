import asyncio
import aiohttp
import json
from functools import reduce
from hashlib import md5
import ipaddress
import logging
import functools
import inspect
import datetime
import configparser


URL = 'http://104.248.47.74/dkrest/'


config = configparser.ConfigParser()
config.read('config.ini')


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s; %(name)s; %(levelname)s; %(message)s')

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('debug.log')

console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

log.addHandler(console_handler)
log.addHandler(file_handler)


def logger(func):
    """Decorator to log function name and arguments when called, and log it's result.
    :param func: The function to decorate.
    :return: The wrapped function.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            log.debug(f'{func.__name__} called with args {args}, kwargs {kwargs}')
            result = await func(*args, **kwargs)
            log.debug(f'{func.__name__} returns {result}')
            return result
    else:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            log.debug(f'{func.__name__} called with args {args}, kwargs {kwargs}')
            result = func(*args, **kwargs)
            log.debug(f'{func.__name__} returns {result}')
            return result
    return wrapped


def timeit(func):
    """Decorator to log function name execution time.
    :param func: The function to decorate.
    :return: The wrapped function.
    """
    if inspect.iscoroutinefunction(func):
        async def wrapped(*args, **kwargs):
            start_time = datetime.datetime.now()
            result = await func(*args, **kwargs)
            end_time = datetime.datetime.now()
            delta = end_time - start_time
            log.debug(f'{func.__name__} executed in {delta.total_seconds() * 1000:.2f} milliseconds')
            return result
    else:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            start_time = datetime.datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.datetime.now()
            delta = end_time - start_time
            log.debug(f'{func.__name__} executed in {delta.total_seconds() * 1000:.2f} milliseconds')
            return result
    return wrapped


@timeit
@logger
async def fetch(url: str, params: dict = None, data = None, method: str = 'GET') -> [dict, str, None]:
    """Make a request with the provided method, url and parameters and return the content

    :param url: The url to request data from.
    :param params: A dictionary of key value pairs to be sent as parameters.
    :param data: Data to be sent in the body of the request.
    :param method: The HTTP method to use for the request.
    :return: The contents of the response.
    """
    async with session.request(method=method, url=url, params=params, data=data) as response:
        if response.content_type == 'application/json':
            return await response.json()
        else:
            return await response.text()


@timeit
@logger
async def auth() -> tuple:
    """Authorize with NTNU email and registered phone number to get a session ID.

    :return: A tuple with session ID and user ID.
    """
    data = {'email': config['auth']['email'],
            'phone': config['auth']['phone']}
    data = json.dumps(data)
    response = await fetch(url=f'{URL}auth', data=data, method='POST')
    if type(response) is not dict:
        response = json.loads(response)

    log.info(response.get('comment'))
    session_id = response.get('sessionId')
    user_id = response.get('userId')

    return session_id, user_id


@timeit
@logger
async def get_task(session_id: int, task_number: int) -> list:
    """Ask the server for a task.

    :param session_id: The session ID to identify the client.
    :param task_number: The task to get.
    :return: None
    """
    params = {'sessionId': session_id}
    response = await fetch(url=f'{URL}gettask/{task_number}', params=params)
    if type(response) is not dict:
        response = json.loads(response)
    arguments = await parse_get_task(response)
    return arguments


@timeit
@logger
async def parse_get_task(response: dict) -> list:
    task_number = response.get('taskNr')
    description = response.get('description')
    arguments = response.get('arguments')
    log.info(f'Task {task_number}: {description}')
    log.info(f'Arguments: {arguments}')
    return arguments


@timeit
@logger
async def parse_solve(response: dict) -> bool:
    """Parse the response from a solve request.

    :param response: The response to parse.
    :return: True if the task was solved correctly.
    """
    success = response.get('success')
    comment = response.get('comment')

    log.info(f'Comment: {comment}')

    return success


@timeit
@logger
async def results(session_id: int) -> None:
    """

    :param session_id: The session ID to identify the client.
    """
    response = await fetch(url=f'{URL}results/{session_id}')
    if type(response) is not dict:
        response = json.loads(response)
    student = response.get('student')
    achievements = response.get('results')
    total_result = response.get('totalResult')
    passed = response.get('passed')
    passed_string = 'passed with score' if passed else 'have not passed, current score'
    log.info(f'Student {student} {passed_string} {total_result}.')
    log.info(f'Achievements: {achievements}')


@timeit
@logger
async def solve_task1(session_id: int) -> bool:
    """Solve task 1.

    Send message 'Hello'.

    :param session_id: The session ID to identify the client.
    :return: True if the task was solved correctly.
    """
    await get_task(session_id, 1)
    data = {'sessionId': session_id,
            'msg': 'Hello'}
    data = json.dumps(data)
    response = await fetch(url=f'{URL}solve', data=data, method='POST')
    if type(response) is not dict:
        response = json.loads(response)
    success = await parse_solve(response)

    return success


@timeit
@logger
async def solve_task2(session_id: int) -> bool:
    """Solve task 2.

    Echo the response from get_task(). Send arguments[0].

    :param session_id: The session ID to identify the client.
    :return: True if the task was solved correctly.
    """
    arguments = await get_task(session_id, 2)
    data = {'sessionId': session_id,
            'msg': arguments[0]}
    data = json.dumps(data)
    response = await fetch(url=f'{URL}solve', data=data, method='POST')
    if type(response) is not dict:
        response = json.loads(response)
    success = await parse_solve(response)

    return success


@timeit
@logger
async def solve_task3(session_id: int) -> bool:
    """Solve task 3.

    Multiply all the numbers in arguments and send the product.

    :param session_id: The session ID to identify the client.
    :return: True if the task was solved correctly.
    """
    arguments = await get_task(session_id, 3)
    arguments = list(map(lambda num: int(num), arguments))
    product = reduce((lambda x, y: x * y), arguments)

    data = {'sessionId': session_id,
            'result': product}
    data = json.dumps(data)
    response = await fetch(url=f'{URL}solve', data=data, method='POST')
    if type(response) is not dict:
        response = json.loads(response)
    success = await parse_solve(response)

    return success


@timeit
@logger
async def solve_task4(session_id: int) -> bool:
    """Solve task 4.

    The task returns a md5 hash. Find the number that was used to make the hash.
    The number is between 0 and 99999. Make a for loop and make a hash for every
    number until a hash is equal to the one we are checking against. Send the number.

    :param session_id: The session ID to identify the client.
    :return: True if the task was solved correctly.
    """
    arguments = await get_task(session_id, 4)
    pin_hash = arguments[0]
    pin = None
    for number in range(0, 99999):
        if md5(str(number).encode('utf-8')).hexdigest() == pin_hash:
            pin = number
            break

    data = {'sessionId': session_id,
            'pin': pin}
    data = json.dumps(data)
    response = await fetch(url=f'{URL}solve', data=data, method='POST')
    if type(response) is not dict:
        response = json.loads(response)
    success = await parse_solve(response)

    return success


@timeit
@logger
async def solve_secret(session_id: int) -> bool:
    """Solve secret task.

    Use the ipaddress module to make a IPv4 network with the given properties.
    Select the first IP address in the network and send it.

    :param session_id: The session ID to identify the client.
    :return: True if the task was solved correctly.
    """
    arguments = await get_task(session_id, 2016)
    address = arguments[0]
    netmask = arguments[1]

    network = ipaddress.IPv4Network(f'{address}/{netmask}')
    ip = str(next(network.hosts()))

    data = {'sessionId': session_id,
            'ip': ip}
    data = json.dumps(data)
    response = await fetch(url=f'{URL}solve', data=data, method='POST')
    if type(response) is not dict:
        response = json.loads(response)
    success = await parse_solve(response)

    return success


@timeit
@logger
async def main():
    session_id, user_id = await auth()

    await solve_task1(session_id)
    await solve_task2(session_id)
    await solve_task3(session_id)
    await solve_task4(session_id)
    await solve_secret(session_id)

    await results(session_id)

    await session.close()


loop = asyncio.get_event_loop()
session = aiohttp.ClientSession(loop=loop)
loop.run_until_complete(main())
loop.close()
