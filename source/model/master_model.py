from typing import List
import gurobipy as gp
from gurobipy import GRB
import logging
from ..info.input_data import InputData
from ..info.config import Config

class RestrictedMasterProblem:
    def __init__(self, initial_routes,
                 input_data: InputData):
        self.input_data = input_data
        self.model = gp.Model("RMP")
        self.routes = initial_routes
        self.lambdas = {}
        self.pi = {}
        self.theta = 0
        self.num_customers = len(self.input_data.customer_dict)-1

        # 创建变量
        for idx, route in enumerate(self.routes):
            self.lambdas[idx] = self.model.addVar(vtype=GRB.CONTINUOUS, name=f"lambda_{idx}",lb=0,ub=1)

        # 目标函数
        self.model.setObjective(
            gp.quicksum(route["cost"] * self.lambdas[idx] for idx, route in enumerate(self.routes)),
            GRB.MINIMIZE
        )

        # 客户覆盖约束
        self.coverage_constrs = {}
        for i in range(1, self.num_customers + 1):
            expr = gp.LinExpr()
            for idx, route in enumerate(self.routes):
                if i in route["path"][1:-1]:
                    expr += self.lambdas[idx]
            self.coverage_constrs[i] = self.model.addConstr(expr == 1, name=f"cover_{i}")

        # 车辆数量约束
        self.vehicle_constr = self.model.addConstr(
            gp.quicksum(self.lambdas[idx] for idx in range(len(self.routes))) <= self.input_data.vehicle_info.count,
            name="vehicle_limit"
        )

    def solve(self):
        self.model.optimize()
        self.mp_obj = self.model.ObjVal
        if self.model.status == GRB.OPTIMAL:
            for i in range(1, self.num_customers + 1):
                self.pi[i] = self.coverage_constrs[i].Pi
            self.theta = self.vehicle_constr.Pi
            return True
        return False

    def add_route(self, new_route):
        for current_route in self.routes:
            if current_route['path'] == new_route['path']:
                logging.info("生成重复解，pass")
                return
        idx = len(self.routes)
        self.routes.append(new_route)
        new_lambda = self.model.addVar(vtype=GRB.CONTINUOUS, name=f"lambda_{idx}",lb=0,ub=1)
        self.lambdas[idx] = new_lambda

        # 更新目标函数
        self.model.setObjective(
            self.model.getObjective() + new_route["cost"] * new_lambda,
            GRB.MINIMIZE
        )

        # 更新客户覆盖约束系数
        for i in range(1, self.num_customers + 1):
            if i in new_route["path"][1:-1]:
                self.model.chgCoeff(self.coverage_constrs[i], new_lambda, 1.0)

            # 移除原有车辆约束并重新添加（确保包含新变量）
        self.model.remove(self.vehicle_constr)  # 移除旧约束
        self.vehicle_constr = self.model.addConstr(
            gp.quicksum(self.lambdas[idx] for idx in self.lambdas) <= self.input_data.vehicle_info.count,
            name="vehicle_limit"
        )

        self.model.update()

    def is_route_exist(self, route_path: List[int]):
        for route in self.routes:
            if route['path'] == route_path:
                return True
        return False
