#!/usr/bin/env python3

from typing import Any

import zulip


def main() -> None:
	# Use the repository-local zuliprc by default.
	client = zulip.Client(config_file="zuliprc")

	request: dict[str, Any] = {
		"anchor": "newest",
		"num_before": 100,
		"num_after": 0,
		"narrow": [
			{"operator": "sender", "operand": "iago@zulip.com"},
			{"operator": "channel", "operand": "Verona"},
		],
	}

	result = client.get_messages(request)
	print(result)


if __name__ == "__main__":
	main()