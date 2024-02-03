from threading import Lock

class SingletonModel:
    _instances = None
    _lock = Lock()
    def __new__(cls):
        with cls. _lock:
            if cls._instances == None:
                cls._instances = super().__new__(cls)
        return cls._instances
    
    def __init__(self) -> None:
        pass