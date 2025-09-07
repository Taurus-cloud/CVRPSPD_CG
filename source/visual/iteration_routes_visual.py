import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import hsv_to_rgb
import numpy as np
from ..info.input_data import InputData
from source.model.model_manager import ModelManager
import logging


class IterationVisualization:
    def __init__(self, input_data: InputData, model_manager: ModelManager):
        """
        初始化迭代可视化类
        :param input_data: 包含客户点信息的 InputData 实例
        :param model_manager: 包含迭代路径信息的 ModelManager 实例
        """
        self.input_data = input_data
        self.model_manager = model_manager
        self.customer_positions = input_data.get_customer_positions()

    def visualize_iteration(self, iteration_idx, routes):
        """可视化特定迭代的路径集合"""
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 10))

        # 绘制客户点
        for cust_id, (x, y) in self.customer_positions.items():
            ax.scatter(x, y, color='blue', s=100)
            ax.text(x, y, f"{cust_id}", fontsize=12, ha='right')

        # 绘制灰色虚线连接每个客户点
        for i, (cust_i, pos_i) in enumerate(self.customer_positions.items()):
            for cust_j, pos_j in list(self.customer_positions.items())[i + 1:]:
                ax.plot([pos_i[0], pos_j[0]], [pos_i[1], pos_j[1]],
                        color='gray', linestyle='--', linewidth=0.5)

        # 为每条路径生成不同的颜色
        num_routes = len(routes)
        colors = [hsv_to_rgb((i / num_routes, 0.8, 0.9)) for i in range(num_routes)]

        # 绘制路径
        for idx, route in enumerate(routes):
            path = route['path']
            color = colors[idx % len(colors)]

            for i in range(len(path) - 1):
                start_id, end_id = path[i], path[i + 1]
                start_pos = self.customer_positions[start_id]
                end_pos = self.customer_positions[end_id]

                # 绘制箭头
                ax.annotate("", xy=(end_pos[0], end_pos[1]),
                            xytext=(start_pos[0], start_pos[1]),
                            arrowprops=dict(arrowstyle="->", color=color, lw=2))

        # 设置图形标题和坐标轴标签
        ax.set_title(f"Iteration {iteration_idx}: Routes", fontsize=16)
        ax.set_xlabel("X Coordinate", fontsize=12)
        ax.set_ylabel("Y Coordinate", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)

        return fig, ax

    def create_animation(self):
        """创建展示所有迭代过程的动画"""
        # 获取所有迭代的路径集合
        iteration_routes = self.model_manager.iteration_routes

        if not iteration_routes:
            logging.error("No iteration routes recorded!")
            return

        # 创建初始图形
        fig, ax = plt.subplots(figsize=(12, 10))

        # 绘制客户点
        for cust_id, (x, y) in self.customer_positions.items():
            ax.scatter(x, y, color='blue', s=100)
            ax.text(x, y, f"{cust_id}", fontsize=12, ha='right')

        # 绘制灰色虚线连接每个客户点
        for i, (cust_i, pos_i) in enumerate(self.customer_positions.items()):
            for cust_j, pos_j in list(self.customer_positions.items())[i + 1:]:
                ax.plot([pos_i[0], pos_j[0]], [pos_i[1], pos_j[1]],
                        color='gray', linestyle='--', linewidth=0.5)

        # 设置图形标题和坐标轴标签 - 初始设为第一次迭代
        ax.set_title("Column Generation - Iteration 0", fontsize=16)
        ax.set_xlabel("X Coordinate", fontsize=12)
        ax.set_ylabel("Y Coordinate", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)

        # 存储所有路径的箭头对象
        arrows = []

        def init():
            """初始化动画"""
            # 初始化时就显示第一帧的路径，而不是空白图
            routes = iteration_routes[0]
            num_routes = len(routes)
            colors = [hsv_to_rgb((i / num_routes, 0.8, 0.9)) for i in range(num_routes)]

            for idx, route in enumerate(routes):
                path = route['path']
                color = colors[idx % len(colors)]

                for i in range(len(path) - 1):
                    start_id, end_id = path[i], path[i + 1]
                    start_pos = self.customer_positions[start_id]
                    end_pos = self.customer_positions[end_id]

                    arrow = ax.annotate("", xy=(end_pos[0], end_pos[1]),
                                        xytext=(start_pos[0], start_pos[1]),
                                        arrowprops=dict(arrowstyle="->", color=color, lw=2))
                    arrows.append(arrow)

            return arrows

        def update(frame):
            """更新动画帧"""
            # 清除上一帧的所有箭头
            for arrow in arrows:
                arrow.remove()
            arrows.clear()

            # 获取当前迭代的路径集合
            routes = iteration_routes[frame]

            # 为每条路径生成不同的颜色
            num_routes = len(routes)
            colors = [hsv_to_rgb((i / num_routes, 0.8, 0.9)) for i in range(num_routes)]

            # 更新标题
            ax.set_title(f"Column Generation - Iteration {frame}", fontsize=16)

            # 绘制路径
            for idx, route in enumerate(routes):
                path = route['path']
                color = colors[idx % len(colors)]

                for i in range(len(path) - 1):
                    start_id, end_id = path[i], path[i + 1]
                    start_pos = self.customer_positions[start_id]
                    end_pos = self.customer_positions[end_id]

                    # 绘制箭头
                    arrow = ax.annotate("", xy=(end_pos[0], end_pos[1]),
                                        xytext=(start_pos[0], start_pos[1]),
                                        arrowprops=dict(arrowstyle="->", color=color, lw=2))
                    arrows.append(arrow)

            return arrows

            # 创建动画

        ani = animation.FuncAnimation(fig, update, frames=len(iteration_routes),
                                      init_func=init, blit=True, interval=1500)

        return ani, fig

    def visualize_all_iterations(self):
        """可视化所有迭代，并保存为单独的图片"""
        iteration_routes = self.model_manager.iteration_routes

        if not iteration_routes:
            logging.error("No iteration routes recorded!")
            return

        for i, routes in enumerate(iteration_routes):
            fig, ax = self.visualize_iteration(i, routes)
            plt.tight_layout()
            plt.savefig(f"iteration_{i}_routes.png")
            plt.close(fig)

        logging.info(f"Saved {len(iteration_routes)} iteration images")

    def show_animation(self):
        """显示迭代过程的动画"""
        ani, fig = self.create_animation()
        if ani is not None:
            plt.tight_layout()
            plt.show()
        else:
            logging.error("Failed to create animation")

    def save_animation(self, filename="cg_iterations.gif"):
        """保存迭代过程的动画为GIF文件"""
        ani, fig = self.create_animation()
        if ani is not None:
            ani.save(filename, writer='pillow', fps=1)
            plt.close(fig)
            logging.info(f"Animation saved to {filename}")
        else:
            logging.error("Failed to create animation")