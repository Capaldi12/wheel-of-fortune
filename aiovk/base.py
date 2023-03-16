"""Async VK API wrapper."""
__all__ = ['VK', 'VKError', 'MethodGroup', 'Method']

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
                 session: Optional[ClientSession] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Can be used in multiple inheritance

        self._version = version
        self._token = token

        self._owns_session = session is None
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

        await self.before_request(method, params)

        data = await self._invoke(method, params)

        return await self.after_request(method, params, data)

    async def _invoke(self, method: str,
                      params: dict[str, Any]) -> dict[str, Any]:
        """Actual method call."""

        async with self._session.get(
            self._base_url + method,
            params=params | self.base_params  # urlencoded automatically
        ) as resp:
            data = await resp.json()

        try:
            return data['response']
        except KeyError:
            raise VKError(method, data['error']) from None

    async def before_request(self, method: str, params: dict[str, Any]) -> None:
        """Add/remove/modify parameters if necessary."""
        pass

    async def after_request(self, method: str, params: dict[str, Any],
                            data: dict[str, Any]) -> Any:
        """Convert data to desired format."""
        return data

    def __getattr__(self, group_name: str):
        return MethodGroup(self, group_name)

    async def __aenter__(self) -> "VK":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.dispose()

    async def dispose(self):
        """Disposes of any resources that were created.
        Any use beyond the call of this method is undefined behavior."""

        if self._owns_session and self._session:
            await self._session.close()
            self._session = None


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
