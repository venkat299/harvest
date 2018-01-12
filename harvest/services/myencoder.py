import json
import numpy as np
import logging
log = logging.getLogger(__name__)

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        log.debug('in json encode:',obj)
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.float64):
            return float(obj)
        else:
            return super(MyEncoder, self).default(obj)