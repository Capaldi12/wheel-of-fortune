"""Async VK API."""

from typing import Optional, Any

from aiohttp import ClientSession


class VKError(Exception):
    """Error in VK API call."""

    def __init__(self, method, *args):
        super().__init__(*args)
        self.method: str = method

    def __str__(self) -> str:
        return f'({self.method}: {", ".join(str(a) for a in self.args)})'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}{self}'


class VK:
    """Async VK API wrapper."""

    _base_url: str = "https://api.vk.com/method/"

    def __init__(self, token: str, version: float | str = '5.131',
                 session: Optional[ClientSession] = None):

        self._version = version
        self._token = token

        if session:
            self._session = session
        else:
            self._session = ClientSession()

    @property
    def base_params(self) -> dict[str, Any]:
        """These parameters are inserted into every API call."""
        return {'access_token': self._token, 'v': self._version}

    async def __call__(self, method: str, **params):
        """Call the method with given name and parameters."""

        async with self._session.get(
            self._base_url + method,
            params=self.base_params | params  # urlencoded automatically
        ) as resp:
            data = await resp.json()

        try:
            return data['response']
        except KeyError:
            raise VKError(method, data['error']) from None

    def __getattr__(self, group_name: str):
        return MethodGroup(self, group_name)

    async def dispose(self):
        await self._session.close()


class MethodGroup:
    """VK API method group."""

    def __init__(self, vk: VK, name: str):
        self._vk: VK = vk
        self._name: str = name

    def __getattr__(self, method_name: str):
        return Method(self, method_name)


class Method:
    """VK API method."""

    def __init__(self, group: MethodGroup, name: str):
        self._group: MethodGroup = group
        self._name: str = name

    @property
    def qualified_name(self) -> str:
        # noinspection PyUnresolvedReferences,PyProtectedMember
        return f'{self._group._name}.{self._name}'

    async def __call__(self, **params):
        # noinspection PyUnresolvedReferences,PyProtectedMember
        return await self._group._vk(self.qualified_name, **params)
