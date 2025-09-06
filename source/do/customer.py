class Customer:
    def __init__(self,
                 customer_id:int,
                 x_coord: int,
                 y_coord: int,
                 delivery_qty: int,
                 pick_up_qty: int,
                 service_time: int):
        self.customer_id = customer_id
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.delivery_qty = delivery_qty
        self.pick_up_qty = pick_up_qty
        self.service_time = service_time

    def __str__(self):
        return f"customer_id:{self.customer_id},x_coord:{self.x_coord},y_coord:{self.y_coord}"