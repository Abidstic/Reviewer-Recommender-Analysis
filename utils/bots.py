"""One bot rule for every algorithm and for the ground truth.

Mirsaeedi & Rigby (2020) Sec. 3.1 exclude changes made by bots, so bots must not
gain knowledge, count as activity, be recommended, or count as actual reviewers.
"""
from typing import Optional

# Bot accounts whose login lacks the '[bot]' suffix (GitHub type "Bot").
BOT_LOGINS = frozenset({'Copilot'})


def is_bot(username: Optional[str]) -> bool:
    return bool(username) and ('[bot]' in username.lower() or username in BOT_LOGINS)
