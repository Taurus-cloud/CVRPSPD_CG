import time
import gurobipy as gp
from gurobipy import GRB
from gurobipy import setParam
from source.info.input_data import InputData
from source.info.config import Config
from source.model.model_manager import ModelManager
from source.model.origin_model import OriginModel
from source.result.processor import ResultProcessor
from source.utils import log, status
import logging


if __name__ == "__main__":
    # 设置Gurobi参数
    setParam("LogFile", "gurobi_log.log")  # 指定日志文件
    setParam("OutputFlag", 1)  # 允许输出（1=开启，0=完全关闭）
    setParam("LogToConsole", 0)  # 禁止控制台输出（只写入文件）

    # 初始路径：每个客户单独成一条路径
    config = Config()
    input_data = InputData()
    logger = log.setup_log(config.output_folder)
    status.out_status(0)
    st = time.time()
    try:
        # 初始化模型
        origin_model = OriginModel(input_data=input_data)
        origin_model.initialize()
        # 求解原始模型
        origin_solution = origin_model.solve()
        logging.info(f"原始模型中，总成本: {origin_solution['total_cost']:.2f}")
        for k, path in origin_solution['routes'].items():
            logging.info(f"原始模型中，车辆{k}路径: {'->'.join(map(str, path))}")
            logging.info(f"原始模型中，车辆{k}的载货量: {origin_solution['loads'][k]}")

        model_manager = ModelManager(input_data=input_data)
        model_manager.run_cg_model()
        rmp_total_cost = model_manager.rmp.mp_obj
        logging.info(f"松弛的cg模型中，总成本: {rmp_total_cost}")

        cg_routes = model_manager.imp_routes
        cg_total_cost = model_manager.imp_total_cost
        logging.info(f"完整的cg模型中，选择路径: {cg_routes}")
        logging.info(f"完整的cg模型中，总成本: {cg_total_cost}")

        result_processor = ResultProcessor(res=cg_routes)

        logging.info("success")
        logging.info("Total running time:{}".format((time.time() - st)))

        status.out_status(1)

    except Exception as e:
        logging.exception(e)
        logging.error("fail")
        logging.info("Total running time: {}".format(time.time() - st))
        status.out_status(-1)