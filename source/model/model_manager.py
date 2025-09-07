import logging
from collections import defaultdict

import gurobipy as gp
from gurobipy import GRB
from ..info.input_data import InputData
from ..info.config import Config
from ..model.master_model import RestrictedMasterProblem
from ..model.sub_model import PricingSubproblem
from ..model.inital_sol import InitialSol
from ..utils import constant,timing

class ModelManager:
    def __init__(self,
                 input_data: InputData,
                 ):
        self.input_data = input_data
        self.initial_sol = InitialSol(input_data=self.input_data)
        self.iteration_routes = []  # 用于记录每次迭代的路径集合(为了迭代可视化)

    @timing.record_time_decorator(task_name="列生成后生成整数解的时长")
    def get_integer_sol(self, rmp):
        imp_route = dict() # 求解整数解
        logging.info("\nSolving integer solution...")
        for v in rmp.model.getVars():
            v.vtype = GRB.BINARY
        rmp.model.optimize()
        if rmp.model.status == GRB.OPTIMAL:
            logging.info("Integer solution:")
            total_cost = 0
            for idx, route in enumerate(rmp.routes):
                if rmp.lambdas[idx].X > 0.5:
                    imp_route[f"Route {idx}"] = {'cost':route['cost'], 'path': route['path']}
                    total_cost += route["cost"]
            logging.info(f"Total Cost: {total_cost}")
            return imp_route, total_cost

    @timing.record_time_decorator(task_name="列生成迭代的时长")
    def run_cg_model(self):# 创建受限主问题
        self.rmp = RestrictedMasterProblem(initial_routes=self.initial_sol.initial_routes,
                                      input_data=self.input_data)

        # 记录初始路径集合(为了迭代可视化)
        self.iteration_routes.append(self.rmp.routes.copy())

        # 列生成迭代
        iteration = 0
        while True:
            logging.info(f"\n=== Column Generation Iteration {iteration} ===")

            # 1. 求解主问题（RMP）
            if not self.rmp.solve():
                break  # 主问题无解
            # 2. 创建定价子问题并求解所有可行路径
            self.psp = PricingSubproblem(input_data=self.input_data,
                                         dual_values={'pi': self.rmp.pi,
                                                      'theta': self.rmp.theta})
            feasible_routes = self.psp.solve()  # 获取所有缩减成本<0的路径

            # 3. 终止条件：没有新路径或所有路径不满足缩减成本要求
            if not feasible_routes:
                logging.info("No new routes found. Terminating.")
                break

            # 4. 过滤并添加新路径到主问题
            routes_added = False # (为了迭代可视化)
            for route in feasible_routes:
                # 检查路径是否已存在（避免重复添加）
                if self.rmp.is_route_exist(route['path']):
                    continue

                # 检查缩减成本是否足够小（避免数值误差误判）
                if route["reduced_cost"] < -1e-6:
                    logging.info(
                        f"Adding route: {route['path']}, "
                        f"Reduced Cost: {route['reduced_cost']:.2f}"
                    )
                    self.rmp.add_route(route)
                    routes_added = True# (为了迭代可视化)

            # (为了迭代可视化)
            if routes_added:
                # 只有在添加了新路径时才记录当前迭代的路径集合
                self.iteration_routes.append(self.rmp.routes.copy())

            iteration += 1

        # 输出最终解
        logging.info("\nFinal solution (Linear Relaxation):")
        for idx, route in enumerate(self.rmp.routes):
            if self.rmp.lambdas[idx].X > 0.01:
                logging.info(f"Route {idx}: {route['path']}, Cost: {route['cost']}, Lambda: {self.rmp.lambdas[idx].X:.2f}")

        self.imp_routes, self.imp_total_cost = self.get_integer_sol(rmp=self.rmp)


