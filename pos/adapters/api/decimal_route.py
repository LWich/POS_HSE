import json
from collections.abc import Callable, Coroutine
from decimal import Decimal, InvalidOperation
from math import isfinite
from sys import float_info
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute


def parse_decimal(value: str) -> Decimal:
    try:
        number = Decimal(value)
    except InvalidOperation:
        return Decimal("NaN")
    # Preserve the validation error for JSON numbers that previously parsed as infinity
    if number.adjusted() >= float_info.max_10_exp and not isfinite(float(number)):
        return Decimal("NaN")
    return number


class DecimalRequest(Request):
    async def json(self) -> Any:
        if not hasattr(self, "_decimal_json"):
            self._decimal_json = json.loads(await self.body(), parse_float=parse_decimal)
        return self._decimal_json


class DecimalRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            return await handler(DecimalRequest(request.scope, request.receive))

        return handle
