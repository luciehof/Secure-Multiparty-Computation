"""
Secret sharing scheme.
"""

from typing import List
from random import randint

class Share:
    """
    A secret share in a finite field.
    """

    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"Share({self.value})"

    def __add__(self, other):
        return Share(str(int(self.value) + int(other.value)))

    def __sub__(self, other):
        return Share(str(int(self.value) - int(other.value)))

    def __mul__(self, other):
        return Share(str(int(self.value) * int(other.value)))


def share_secret(secret: int, num_shares: int) -> List[Share]:
    """Generate secret shares."""
    shares = []
    for i in range(num_shares - 1):
        num_to_be_assigned = (num_shares-1) - i # -1 because a share can be 0
        share_bound = secret - sum(shares) - num_to_be_assigned
        shares.append(randint(0, share_bound) if share_bound > 0 else 0)

    shares.append(secret - sum(shares))
    # shuffle shares list for randomness in shares assignment

    return list(map(lambda x: Share(str(x)), shares))


def reconstruct_secret(shares: List[Share]) -> int:
    """Reconstruct the secret from shares."""
    sum = 0
    for share in shares:
        sum += int(share.value)
        
    return sum


# Feel free to add as many methods as you want.
