from ..do.vehicle import  Vehicle
from ..do.customer import Customer
from ..info.config import Config
from ..utils import filename
from typing import Dict
import math
import csv
import matplotlib.pyplot as plt
import os

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

    def visualize_customers(self):
        """可视化客户数据"""
        customers = list(self.customer_dict.values())

        # 提取客户信息
        customer_ids = [customer.customer_id for customer in customers]
        x_coords = [customer.x_coord for customer in customers]
        y_coords = [customer.y_coord for customer in customers]

        # 创建图形
        plt.figure(figsize=(10, 8))

        # 绘制客户点
        for i, (x, y) in enumerate(zip(x_coords, y_coords)):
            plt.scatter(x, y, color='blue', s=100)  # 绘制点
            plt.text(x, y, f"{customer_ids[i]}", fontsize=12, ha='right')  # 标注客户ID

        # 绘制灰色虚线连接每个客户点
        for i in range(len(customer_ids)):
            for j in range(i + 1, len(customer_ids)):
                plt.plot([x_coords[i], x_coords[j]], [y_coords[i], y_coords[j]], color='gray', linestyle='--',
                         linewidth=0.5)

        # 设置图形标题和坐标轴标签
        plt.title("Customer Locations", fontsize=16)
        plt.xlabel("X Coordinate", fontsize=12)
        plt.ylabel("Y Coordinate", fontsize=12)

        # 显示网格
        plt.grid(True, linestyle='--', alpha=0.5)

        # 1. 定义保存目录（当前工作目录下的visualize文件夹）
        save_dir = "visualize"  # 文件夹名称
        # 2. 若文件夹不存在，则创建（避免路径不存在报错）
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)  # 创建文件夹（支持多级目录，如"a/b/c"）
        # 3. 拼接完整保存路径（文件夹 + 文件名）
        save_path = os.path.join(save_dir, "Customer Locations.png")
        # 4. 保存图像（dpi=300保证清晰度，bbox_inches避免标题/标签被截断）
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        # 显示图形（需在savefig之后，否则保存的是空白图）
        plt.show()

    def get_customer_positions(self):
        """获取客户点的坐标"""
        return {cust.customer_id: (cust.x_coord, cust.y_coord) for cust in self.customer_dict.values()}