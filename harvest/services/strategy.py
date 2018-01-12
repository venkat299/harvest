from abc import ABC, abstractmethod

class Strategy(ABC):

    # def __init__(self, strategy):
        # self._conn = sqlite3.connect('./harvest/../../db/harvest.db')

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def predict(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def schedule_task(self):
        pass

    # def save(self):
    #     cursor = self._conn.cursor()
    #     cursor.execute('''delete from strategy
    #                       where strategy=?''',
    #                    (self.strategy,))
    #     cursor.execute('''INSERT INTO strategy
    #                       VALUES (?,?,?,?)''',
    #                    self._get_display_values())
    #     self._conn.commit()
