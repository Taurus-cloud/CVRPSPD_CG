import matplotlib.pyplot as plt
from ..info.input_data import InputData
from source.model.origin_model import OriginModel
import os
import logging

class OriginRoutesVisualization:
    def __init__(self, input_data: InputData, origin_model: OriginModel):
        """
        初始化可视化类
        :param input_data: 包含客户点信息的 InputData 实例
        :param origin_model: 包含车辆路径信息的 OriginModel 实例
        """
        self.input_data = input_data
        self.origin_model = origin_model

    def visualize_routes(self):
        """可视化客户点和车辆路径"""
        customers = list(self.input_data.customer_dict.values())

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
        for i in range(len(customers)):
            for j in range(i + 1, len(customers)):
                plt.plot([x_coords[i], x_coords[j]], [y_coords[i], y_coords[j]], color='gray', linestyle='--', linewidth=0.5)

        # 定义颜色列表，用于区分不同车辆的路径
        colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink', 'olive', 'cyan', 'magenta']

        # 提取车辆路径
        solution = self.origin_model.solve()  # 求解模型并获取结果
        for k, path in solution['routes'].items():

            # 获取车辆路径的颜色
            color = colors[k % len(colors)]  # 循环使用颜色列表

            # 绘制路径
            for i in range(len(path) - 1):
                start_customer_id = path[i]
                end_customer_id = path[i + 1]

                # 获取起点和终点的坐标
                start_customer = self.input_data.customer_dict[start_customer_id]
                end_customer = self.input_data.customer_dict[end_customer_id]

                # 绘制箭头
                plt.annotate("",
                             xy=(end_customer.x_coord, end_customer.y_coord),
                             xytext=(start_customer.x_coord, start_customer.y_coord),
                             arrowprops=dict(arrowstyle="->", color=color, lw=2))

        # 设置图形标题和坐标轴标签
        plt.title("Customer Locations and Vehicle Routes--OM", fontsize=16)
        plt.xlabel("X Coordinate", fontsize=12)
        plt.ylabel("Y Coordinate", fontsize=12)

        # 显示网格
        plt.grid(True, linestyle='--', alpha=0.5)

        # 1. 定义保存目录（当前工作目录下的visualize文件夹）
        save_dir = "visualize"
        # 2. 若文件夹不存在，则创建（支持多级目录，避免路径错误）
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)  # 不存在时创建文件夹
        # 3. 拼接完整保存路径（文件夹 + 文件名，自动适配系统路径分隔符）
        save_path = os.path.join(save_dir, "Vehicle Routes--OM.png")
        # 4. 保存图像（dpi=300保证清晰度，bbox_inches避免标题/标签被截断）
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        # 显示图形（需在savefig之后，否则保存的是空白图）
        plt.show()