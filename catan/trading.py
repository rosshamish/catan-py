import logging
from collections import Counter


class CatanTrade(object):
    """
    class CatanTrade provides a mutable trade object for catan

    The trade relationship is one-to-one, and supports any number of
    each of the resources going in both directions.

    Usually, the current player is the giver, and the other entity the getter.
    Think of it as: the current player gives resources, and gets some in return.

    Use give() and get() to add resources to the trade.

    Resources cannot be removed from the trade. If you want this functionality,
    delete the trade and build a new one instead.
    """
    def __init__(self, giver=None, getter=None):
        self._give = list()
        self._get = list()
        self._giver = giver
        self._getter = getter

    def give(self, terrain, num=1):
        """
        Add a certain number of resources to the trade from giver->getter
        :param terrain: resource type, models.Terrain
        :param num: number to add, int
        :return: None
        """
        for _ in range(num):
            logging.debug('terrain={}'.format(terrain))
            self._give.append(terrain)

    def get(self, terrain, num=1):
        """
        Add a certain number of resources to the trade from getter->giver
        :param terrain: resource type, models.Terrain
        :param num: number to add, int
        :return: None
        """
        for _ in range(num):
            logging.debug('terrain={}'.format(terrain))
            self._get.append(terrain)

    def giver(self):
        return self._giver

    def getter(self):
        return self._getter

    def giving(self):
        """
        Returns tuples corresponding to the number and type of each
        resource in the trade from giver->getter

        :return: eg [(2, Terrain.wood), (1, Terrain.brick)]
        """
        logging.debug('give={}'.format(self._give))
        c = Counter(self._give.copy())
        return [(n, t) for t, n in c.items()]

    def getting(self):
        """
        Returns tuples corresponding to the number and type of each
        resource in the trade from getter->giver

        :return: eg [(2, Terrain.wood), (1, Terrain.brick)]
        """
        c = Counter(self._get.copy())
        return [(n, t) for t, n in c.items()]

    def num_giving(self):
        return len(self._give)

    def num_getting(self):
        return len(self._get)

    def set_giver(self, giver):
        self._giver = giver

    def set_getter(self, getter):
        self._getter = getter
