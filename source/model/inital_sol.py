from ..info.input_data import InputData


class InitialSol:
    def __init__(self, input_data: InputData):
        self.input_data = input_data
        self.initial_routes = []
        self.num_customers = len(self.input_data.customer_dict) - 1  # 排除车场
        self._get_initial_routes()

    def _get_initial_routes(self):
        """生成满足车辆数限制的初始路径"""
        num_vehicles = self.input_data.vehicle_info.count
        capacity = self.input_data.vehicle_info.capacity

        # 1. 提取需服务的客户列表（排除车场）
        customers = [i for i in self.input_data.customer_dict if i != 0]

        # 2. 按总需求降序排序（送货+取货）
        sorted_customers = sorted(
            customers,
            key=lambda x: (
                    self.input_data.customer_dict[x].delivery_qty
                    + self.input_data.customer_dict[x].pick_up_qty
            ),
            reverse=True
        )

        # 3. 使用首次适应递减算法分组
        groups = []
        current_group = []
        current_load = 0

        for cust in sorted_customers:
            delivery = self.input_data.customer_dict[cust].delivery_qty
            pickup = self.input_data.customer_dict[cust].pick_up_qty
            total_demand = delivery + pickup

            # 容量检查：总需求不超过车辆容量
            if current_load + total_demand > capacity:
                groups.append(current_group)
                current_group = []
                current_load = 0

            current_group.append(cust)
            current_load += total_demand

        if current_group:
            groups.append(current_group)

        # 4. 确保分组数不超过车辆数（关键修改）
        if len(groups) > num_vehicles:
            # 合并多余的分组（示例策略：将最后几个小组合并到前几个组）
            while len(groups) > num_vehicles:
                extra_group = groups.pop()
                groups[-1].extend(extra_group)

        # 5. 为每组生成路径（按插入顺序）
        for group in groups[:num_vehicles]:  # 严格限制不超过可用车辆数
            if not group:
                continue

            # 路径构造策略：车场 -> 客户1 -> 客户2 -> ... -> 车场
            path = [0] + group + [0]

            # 计算路径成本（简单累加相邻节点距离）
            cost = 0
            for i in range(len(path) - 1):
                cost += self.input_data.distance_matrix.get(
                    (path[i], path[i + 1]), 0
                )

            self.initial_routes.append({
                "path": path,
                "cost": cost,
                "demand": sum(
                    self.input_data.customer_dict[c].delivery_qty
                    + self.input_data.customer_dict[c].pick_up_qty
                    for c in group
                )
            })

        # 6. 验证分组可行性
        if len(self.initial_routes) > num_vehicles:
            raise ValueError("无法生成可行初始解：客户需求超过车辆容量限制")