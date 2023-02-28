"""Annotated version of VK API wrapper."""
__all__ = ['VK', 'VKError', 'MethodGroup', 'Method']

import random
from typing import Any

from ..base import VK as BaseVK, MethodGroup, Method, VKError
from .poller import Poller


class VK(BaseVK):
    """Annotated version of VK API wrapper."""

    _rules = {
        'messages.send': {
            'prepare_params': {
                'keyboard': lambda k: k.to_json()
            },
            'add_params': {
                'random_id': lambda:
                    random.getrandbits(31) * random.choice([-1, 1])
            }
        },
        'groups.getLongPollServer': {
            'convert_result': lambda data, self=None: Poller(
                self, data['server'], data['key'], data['ts'],
                session=self._session if self else None)
        }
    }

    async def before_request(self, method: str, params: dict[str, Any]) -> None:
        if rule := self._rules.get(method):
            if prepare_params := rule.get('prepare_params'):
                for k, v in prepare_params.items():
                    if k in params:
                        params[k] = v(params[k])
            if add_params := rule.get('add_params'):
                for k, v in add_params.items():
                    if k not in params:
                        params[k] = v()

    async def after_request(self, method: str, data: dict[str, Any]) -> Any:
        if rule := self._rules.get(method):
            if convert_result := rule.get('convert_result'):
                return convert_result(data, self=self)

        return data
