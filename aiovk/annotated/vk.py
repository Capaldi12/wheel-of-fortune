"""Annotated version of VK API wrapper."""
__all__ = ['VK', 'VKError', 'MethodGroup', 'Method']

import random
from typing import Any

from ..base import VK as BaseVK, MethodGroup, Method, VKError
from .poller import Poller


class VK(BaseVK):
    """Annotated version of VK API wrapper."""

    _rules = {
        '*': {
            'prepare_params': {
                'keyboard': lambda k: k.to_json()
            }
        },

        'messages.send': {
            'add_params': {
                'random_id': lambda:
                    random.getrandbits(31) * random.choice([-1, 1])
            }
        },
        'groups.getLongPollServer': {
            'convert_result': lambda data, params, self=None: Poller(
                self, params['group_id'],
                data['server'], data['key'], data['ts'],
                session=self._session if self else None
            )
        }
    }

    async def before_request(self, method: str, params: dict[str, Any]) -> None:
        await self._process_before_rule('*', params)
        await self._process_before_rule(method, params)

    async def _process_before_rule(self, match: str,
                                   params: dict[str, Any]) -> dict[str, Any]:

        if rule := self._rules.get(match):
            if prepare_params := rule.get('prepare_params'):
                for k, v in prepare_params.items():
                    if k in params:
                        params[k] = v(params[k])
            if add_params := rule.get('add_params'):
                for k, v in add_params.items():
                    if k not in params:
                        params[k] = v()  # type: ignore

        return params

    async def after_request(self, method: str, params: dict[str, Any],
                            data: dict[str, Any]) -> Any:
        if rule := self._rules.get(method):
            if convert_result := rule.get('convert_result'):
                return convert_result(data, params, self=self)

        return data
