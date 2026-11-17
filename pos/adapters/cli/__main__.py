import sys
from argparse import Namespace
from collections.abc import Callable

from pos.adapters.cli.parser import build_parser
from pos.domain.errors import AssessmentError


def main() -> int:
    arguments = build_parser().parse_args()
    handler: Callable[[Namespace], None] = arguments.handler
    try:
        handler(arguments)
    except AssessmentError as error:
        print(f"Ошибка. {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
