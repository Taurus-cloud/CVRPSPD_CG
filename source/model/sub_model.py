import logging
import heapq
from collections import defaultdict
from ..utils import constant


class PricingSubproblem:
    def __init__(self, dual_values, input_data):
        self.input_data = input_data
        self.dual_values = dual_values
        self.feasible_routes = []
        self.num_customers = len(input_data.customer_dict) - 1
        self.Q = input_data.vehicle_info.capacity  # 车辆容量
        # +++ 新增时间参数 +++
        self.v = constant.VEHICLE_SPEED  # 从配置获取速度
        self.tm = constant.MAX_TRAVEL_TIME  # 最大在途时间
        self.st = {i: input_data.customer_dict[i].service_time for i in input_data.customer_dict}  # 服务时间


    def solve(self):
        heap = []
        # 初始标签：从车场出发，载货量为0，但尚未确定实际需要的初始载货量
        initial_label = {
            "node": 0,
            "path": [0],
            "visited": set(),
            "initial_load": 0,
            "remaining_load": 0,
            "total_delivery": 0,
            "total_pickup": 0,
            "total_time": 0,  # 新增总时间（行驶+服务）
            "cost": 0
        }
        heapq.heappush(heap, (initial_label["cost"], id(initial_label), initial_label))
        dominance_dict = defaultdict(list)

        while heap:
            current_cost, _, current_label = heapq.heappop(heap)
            current_node = current_label["node"]

            # 剪枝：若标签被支配，跳过
            if self.is_dominated(current_label, dominance_dict[current_node]):
                continue

            dominance_dict[current_node].append(current_label)

            # 遍历所有可能的下一节点
            for next_node in range(self.num_customers + 1):
                if next_node == current_node or next_node in current_label["visited"]:
                    continue

                new_label = self.extend_label(current_label, next_node)
                if not new_label:
                    continue  # 路径不可行

                # 若回到车场，检查初始载货量是否满足总配送需求
                if next_node == 0:
                    if new_label["initial_load"] >= new_label["total_delivery"]:
                        reduced_cost = self.calculate_reduced_cost(new_label)
                        if reduced_cost < -1e-6:
                            self.feasible_routes.append({
                                "path": new_label["path"],
                                "cost": new_label["cost"],
                                "reduced_cost": reduced_cost
                            })
                    continue

                # 应用支配规则并加入队列
                if not self.is_dominated(new_label, dominance_dict[next_node]):

                    heapq.heappush(heap, (new_label["cost"], id(new_label), new_label))

        return self.feasible_routes

    def extend_label(self, label, next_node):
        """扩展标签到下一节点，返回新标签或None（若不可行）"""
        # 获取客户需求（车场无需求）
        if next_node == 0:
            delivery, pickup = 0, 0
        else:
            customer = self.input_data.customer_dict[next_node]
            delivery, pickup = customer.delivery_qty, customer.pick_up_qty

        # 计算新的总配送需求和总取货需求
        new_total_delivery = label["total_delivery"] + delivery
        new_total_pickup = label["total_pickup"] + pickup

        # 计算行驶时间（距离/速度）
        travel_time = self.input_data.distance_matrix[(label["node"], next_node)] / self.v
        # 服务时间（仅客户节点）
        service_time = self.st[next_node] if next_node != 0 else 0
        new_total_time = label["total_time"] + travel_time + service_time

        # +++ 时间约束检查 +++
        if new_total_time > self.tm:
            return None  # 超过最大时间限制

        # 关键修正：更新初始载货量（出发时必须携带足够的总配送需求）
        # 初始载货量 = max(当前初始载货量, 新的总配送需求)
        new_initial_load = max(label["initial_load"], new_total_delivery)

        # 检查车辆容量是否足够（初始载货量 + 取货量 - 配送量 ≤ Q）
        if new_initial_load + (new_total_pickup - new_total_delivery) > self.Q:
            return None

        # 更新剩余载货量（初始载货量 - 已配送总量 + 已取货总量）
        new_remaining_load = new_initial_load - new_total_delivery + new_total_pickup
        if new_remaining_load < 0:
            return None

        # 生成新标签
        new_label = {
            "node": next_node,
            "path": label["path"] + [next_node],
            "visited": label["visited"].copy(),
            "initial_load": new_initial_load,
            "remaining_load": new_remaining_load,
            "total_delivery": new_total_delivery,
            "total_pickup": new_total_pickup,
            "total_time": new_total_time,  # 记录累计时间
            "cost": label["cost"] + self.input_data.distance_matrix[(label["node"], next_node)]
        }
        if next_node != 0:
            new_label["visited"].add(next_node)

        return new_label

    def calculate_reduced_cost(self, label):
        """计算缩减成本：cost - sum(pi_i) + theta"""
        return label["cost"] - sum(self.dual_values['pi'][i] for i in label["visited"]) + self.dual_values['theta']

    @staticmethod
    def is_dominated(new_label, existing_labels):
        """检查新标签是否被支配"""
        for existing in existing_labels:
            time_condition = existing["total_time"] <= new_label["total_time"]
            load_condition = (existing["initial_load"] <= new_label["initial_load"] and
                              existing["remaining_load"] >= new_label["remaining_load"])
            visited_condition = existing["visited"].issubset(new_label["visited"])
            cost_condition = existing["cost"] <= new_label["cost"]

            # +++ 时间成为支配条件之一 +++
            if (time_condition and load_condition and
                    visited_condition and cost_condition):
                return True
        return False