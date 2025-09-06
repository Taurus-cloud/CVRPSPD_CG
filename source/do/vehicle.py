class Vehicle:
    def __init__(self,
                 capacity: int,
                 count: int):
        self.capacity = capacity
        self.count = count

    def __str__(self):
        return f"vehicle_qty:{self.count},capacity:{self.capacity}"
