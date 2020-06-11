def calculate_distance(d1, d2):
    return abs(d1.x - d2.x) + abs(d1.y - d2.y)


def add_class(dictionary):
    def decorator(cls):
        assert cls.id not in dictionary, "id duplicated"
        dictionary[cls.id] = cls
        return cls
    return decorator
