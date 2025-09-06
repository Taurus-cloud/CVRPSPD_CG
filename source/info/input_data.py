from ..do.vehicle import  Vehicle
from ..do.customer import Customer
from ..info.config import Config
from ..utils import filename
from typing import Dict
import math
import csv

class InputData:
    def __init__(self):
        self.customer_dict : Dict[int, Customer] = {}
        self.vehicle_info = None
        self.distance_matrix : Dict[tuple[int, int], float] = {}
        self.config = Config()
        self._init_customer_dict_and_vehicle_info()
        self._init_distance_matrix()

    def _init_customer_dict_and_vehicle_info(self):
        """从CSV文件加载客户和车辆数据"""
        # 1. 读取客户数据
        with open("{}{}".format(self.config.input_folder, filename.CUSTOMER_FILE, 'r', encoding='utf-8')) as f:
            reader = csv.DictReader(f)
            for row in reader:
                cust_id = int(row['customer_id'])
                self.customer_dict[cust_id] = Customer(
                    customer_id=cust_id,
                    x_coord=int(row['x_coord']),
                    y_coord=int(row['y_coord']),
                    delivery_qty=int(row['delivery_qty']),
                    pick_up_qty=int(row['pick_up_qty']),
                    service_time=int(row['service_time'])
                )

        # 2. 读取车辆数据
        with open("{}{}".format(self.config.input_folder, filename.VEHICLE_FILE, 'r', encoding='utf-8')) as f:
            reader = csv.DictReader(f)  # 注意分隔符是制表符
            row = next(reader)  # 只读取第一行
            self.vehicle_info = Vehicle(
                count=int(row['vehicle_count']),
                capacity=int(row['vehicle_capacity'])
            )


    def _init_distance_matrix(self):
        """计算所有客户点之间的欧氏距离"""
        customers = list(self.customer_dict.values())
        for i in customers:
            for j in customers:
                dx = i.x_coord - j.x_coord
                dy = i.y_coord - j.y_coord
                self.distance_matrix[(i.customer_id, j.customer_id)] = math.sqrt(dx ** 2 + dy ** 2)

