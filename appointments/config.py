class SingletonConfig:
    """
    Singleton class for global clinic configuration.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonConfig, cls).__new__(cls)
            # Initialize default settings
            cls._instance.default_slot_duration = 30
            cls._instance.operating_hours_start = "09:00"
            cls._instance.operating_hours_end = "17:00"
        return cls._instance
        