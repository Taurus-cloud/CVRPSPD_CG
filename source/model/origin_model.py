import logging

import gurobipy as gp
from gurobipy import GRB
import numpy as np
from ..info.input_data import InputData
from ..utils import constant,timing
from ..info.config import Config


class OriginModel:
    def __init__(self,
                 input_data: InputData):
        """
        :param customer_data: dict {customer_id: (q_plus, q_minus, x_coord, y_coord)}
        :param vehicle_capacity: 车辆最大载重Q
        """
        self.input_data = input_data
        # 数据预处理
        self.depot_id = 0  # 车场固定编号为0
        self.customers_id = [k for (k, customer_info) in self.input_data.customer_dict.items() if k != self.depot_id]
        self.K = list(range(input_data.vehicle_info.count))   # 车辆集合动态生成
        self.Q = self.input_data.vehicle_info.capacity

        # 创建Gurobi模型
        self.model = gp.Model("VRPSPD_Origin")

    def initialize(self):
        # 数据结构初始化
        self._init_sets()
        self._init_parameters()
        self._create_variables()
        self._add_constraints()
        self._set_objective()

    def _init_sets(self):
        """初始化基本集合"""
        self.V = [self.depot_id] + self.customers_id  # 所有节点
        self.N = self.customers_id  # 客户节点

    def _init_parameters(self):
        """初始化模型参数"""
        # 需求参数

        self.q_plus = {i: self.input_data.customer_dict[i].pick_up_qty for i in self.V}
        self.q_minus = {i: self.input_data.customer_dict[i].delivery_qty for i in self.V}

        # 服务时间参数 +++
        self.st = {i: self.input_data.customer_dict[i].service_time for i in self.V}

        # 从配置获取速度和时间限制 +++
        self.v = constant.VEHICLE_SPEED
        self.tm = constant.MAX_TRAVEL_TIME

        # 检查客户需求是否超过车辆容量
        for i in self.N:
            total_pickup = self.q_plus[i]
            total_delivery = self.q_minus[i]
            if total_pickup > self.Q or total_delivery > self.Q:
                raise ValueError(f"客户 {i} 的需求超过车辆容量 {self.Q}")

    def _create_variables(self):
        """创建决策变量"""
        # 路径选择变量（三维字典）
        self.x = self.model.addVars(
            [(i, j, k) for k in self.K
             for i in self.V
             for j in self.V if i == 0 or (i!= 0 and i != j)],
            vtype=GRB.BINARY,
            name="x"
        )
        logging.info("var 'variables_x' has been created")

        # 载货量变量（二维字典）
        self.u = self.model.addVars(
            [(i, k) for k in self.K for i in self.V],
            lb=0,
            ub=self.Q,
            vtype=GRB.CONTINUOUS,
            name="u"
        )
        logging.info("var 'variables_u' has been created")

    def _add_constraints(self):
        """添加所有约束条件"""
        self._add_visit_constraints()  # 约束1
        self._add_flow_balance()  # 约束2
        self._add_depot_constraints()  # 约束3
        self._add_load_consistency()  # 约束4
        self._add_capacity_constraints()  # 约束5
        self._add_initial_load_constraints()
        self._add_travel_time_constraints()

    def _add_visit_constraints(self):
        """约束1：每个客户被访问一次"""
        for i in self.N:
            self.model.addConstr(
                gp.quicksum(self.x[i, j, k]
                            for k in self.K
                            for j in self.V if j != i
                            ) == 1,
                f"visit_{i}"
            )
        logging.info("constr 'add_visit_constraints' has been finished")

    def _add_flow_balance(self):
        """约束2：流平衡"""
        for k in self.K:
            for i in self.V:  # 仅客户节点需要平衡
                self.model.addConstr(
                    gp.quicksum(self.x[i, j, k] for j in self.V if j != i) ==
                    gp.quicksum(self.x[j, i, k] for j in self.V if j != i),
                    f"flow_{i}_{k}"
                )
        logging.info(f"constr 'add_flow_balance' has been finished")

    def _add_depot_constraints(self):
        """约束3：车辆从depot出发并返回"""
        for k in self.K:
            # 出发约束
            self.model.addConstr(
                gp.quicksum(self.x[self.depot_id, j, k] for j in self.V) == 1,
                f"depart_{k}"
            )
            # 返回约束
            self.model.addConstr(
                gp.quicksum(self.x[j, self.depot_id, k] for j in self.V) == 1,
                f"return_{k}"
            )

        logging.info("constr 'add_depot_constraints' has been finished")

    def _add_load_consistency(self):
        """约束4：载货量递推（线性化）"""
        M = self.Q # 大M值取车辆容量
        for k in self.K:
            for i in self.V:
                for j in self.N:
                    if i == j:
                        continue
                    self.model.addConstr(
                        self.u[j, k] >= self.u[i, k] + self.q_plus[j] - self.q_minus[j]
                        - M * (1 - self.x[i, j, k]),
                        f"load_lb_{i}_{j}_{k}"
                    )
                    self.model.addConstr(
                        self.u[j, k] <= self.u[i, k] + self.q_plus[j] - self.q_minus[j]
                        + M * (1 - self.x[i, j, k]),
                        f"load_ub_{i}_{j}_{k}"
                    )
        logging.info("constr 'add_load_consistency' has been finished")

    def _add_capacity_constraints(self):
        """约束5：载重限制"""
        for k in self.K:
            for i in self.V:
                self.model.addConstr(
                    self.u[i, k] <= self.Q,
                    f"cap_{i}_{k}"
                )
                # self.model.addConstr(
                #     self.u[i, k] >= 0,
                #     f"nonneg_{i}_{k}"
                # )
        logging.info("constr 'add_capacity_constraints' has been finished")

    def _add_initial_load_constraints(self):
        """约束6:初始载货合理性"""
        for k in self.K:
            self.model.addConstr(
                self.u[self.depot_id, k] == gp.quicksum(
                    self.q_minus[i] * sum(self.x[i, j, k] for j in self.V if i != j) for i in self.N),
                f"initial_load_{k}"
            )
        logging.info("constr 'add_initial_load_constraints' has been finished")

    # +++ 新增约束方法 +++
    def _add_travel_time_constraints(self):
        """约束7：车辆在途时间（行驶+服务）不超过限制"""
        for k in self.K:
            # 计算总行驶时间（距离/速度）
            travel_time = gp.quicksum(
                (self.input_data.distance_matrix[i, j] / self.v) * self.x[i, j, k]
                for i in self.V
                for j in self.V
                if i != j
            )

            # 计算总服务时间（仅客户节点）
            service_time = gp.quicksum(
                self.st[i] * gp.quicksum(self.x[i, j, k] for j in self.V if j != i)
                for i in self.N
            )

            # 添加时间约束
            self.model.addConstr(
                travel_time + service_time <= self.tm,
                f"max_travel_time_{k}"
            )
        logging.info("constr 'add_travel_time_constraints' has been finished")


    def _set_objective(self):
        """目标函数：总行驶成本"""
        obj = gp.quicksum(
            self.input_data.distance_matrix[(i, j)] * self.x[i, j, k]
            for k in self.K
            for i in self.V
            for j in self.V
            if i != j
        )
        self.model.setObjective(obj, GRB.MINIMIZE)

    @timing.record_time_decorator(task_name="原始模型的求解时长")
    def solve(self):
        """求解"""
        self.model.update()  # 必须更新模型
        self.model.optimize()

        if self.model.status == GRB.OPTIMAL:
            self.model.write("model.lp")
            return self._extract_solution()
        elif self.model.status == GRB.INFEASIBLE:
            self.model.computeIIS()  # 计算不可行约束
            self.model.write("model.ilp")  # 导出不可行约束子集
            raise Exception("模型不可行，请检查 model.ilp 文件")

    def _extract_solution(self):
        """提取优化结果"""
        solution = {
            'total_cost': self.model.ObjVal,
            'routes': {},
            'loads': {}
        }

        for k in self.K:
            # 路径提取
            path = [self.depot_id]
            current = self.depot_id
            while True:
                next_nodes = [j for j in self.V
                              if j != current
                              and self.x[current, j, k].X > 0.5]
                if not next_nodes:
                    break
                next_node = next_nodes[0]
                path.append(next_node)
                current = next_node
                if current == self.depot_id:
                    break
            if len(path) == 1:
                continue

            # 载货量提取
            load_profile = {i: self.u[i, k].X for i in self.V}

            solution['routes'][k] = path
            solution['loads'][k] = load_profile

        return solution