import asyncio
import aiohttp
import json


URL = 'http://104.248.47.74/dkrest/'


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


async def auth() -> tuple:
    """Authorize with NTNU email and registered phone number to get a session ID.

    :return: A tuple with session ID and user ID.
    """
    data = {'email': 'espenkve@stud.ntnu.no',
            'phone': '99735026'}
    data = json.dumps(data)
    response = await fetch(url=f'{URL}auth', data=data, method='POST')
    response = json.loads(response)

    print(response.get('comment'))
    session_id = response.get('sessionId')
    user_id = response.get('userId')

    return session_id, user_id


async def get_task(session_id: int, task_number: int) -> None:
    """Ask the server for a task.

    :param session_id: The session ID to identify the client.
    :param task_number: The task to get.
    :return: None
    """
    params = {'sessionId': session_id}
    response = await fetch(url=f'{URL}gettask/{task_number}')
    response = json.loads(response)
    await parse_get_task(response)


async def parse_get_task(response: dict) -> None:
    task_number = response.get('taskNr')
    description = response.get('description')
    arguments = response.get('arguments')
    print(f'Task {task_number}: {description}\nArguments: {arguments}')


async def parse_solve(response: dict) -> bool:
    """Parse the response from a solve request.

    :param response: The response to parse.
    :return: True if the task was solved correctly.
    """
    success = response.get('success')
    comment = response.get('comment')
    arguments = response.get('arguments')

    print(f'{comment}\nArguments: {arguments}')

    return success


async def main():

    await session.close()


loop = asyncio.get_event_loop()
session = aiohttp.ClientSession(loop=loop)
loop.run_until_complete(main())
loop.close()
