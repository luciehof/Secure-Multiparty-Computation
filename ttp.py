"""
Trusted parameters generator.

MODIFY THIS FILE.
"""

import collections
from typing import (
    Dict,
    Set,
    Tuple,
)
from random import randint


from communication import Communication
from secret_sharing import(
    share_secret,
    Share,
)

# Feel free to add as many imports as you want.


class TrustedParamGenerator:
    """
    A trusted third party that generates random values for the Beaver triplet multiplication scheme.
    """


    def __init__(self):
        self.participant_ids: Set[str] = set()
        self.dict_castor: Dict = {}


    def add_participant(self, participant_id: str) -> None:
        """
        Add a participant.
        """
        self.participant_ids.add(participant_id)

    def retrieve_share(self, client_id: str, op_id: str) -> Tuple[Share, Share, Share]:
        """
        Retrieve a triplet of shares for a given client_id.
        """
        if op_id not in self.dict_castor.keys():
            a,b,c = self.generate_beaver()
            a_shares = share_secret(a,len(self.participant_ids))
            b_shares = share_secret(b,len(self.participant_ids))
            c_shares = share_secret(c,len(self.participant_ids))

            self.dict_castor[op_id] = {}
            for idx,cid in enumerate(self.participant_ids):
                self.dict_castor[op_id][cid] = (a_shares[idx], b_shares[idx], c_shares[idx])

        return self.dict_castor[op_id][client_id]

    # Feel free to add as many methods as you want.
    def generate_beaver(self):
        a = randint(1,1000)
        b = randint(1,1000)
        c = a*b
        return a,b,c

