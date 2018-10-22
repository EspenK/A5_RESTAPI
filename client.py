import asyncio
import aiohttp
import json


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


async def main():

    await session.close()


loop = asyncio.get_event_loop()
session = aiohttp.ClientSession(loop=loop)
loop.run_until_complete(main())
loop.close()
