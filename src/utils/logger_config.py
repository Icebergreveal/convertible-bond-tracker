import os
from loguru import logger
from datetime import datetime
from typing import Optional

def setup_logger(
    log_dir: str = "logs",
    log_level: str = "INFO",
    rotation: str = "100 MB",
    retention: str = "30 days"
) -> logger:
    """
    配置日志系统
    
    Args:
        log_dir: 日志存储目录
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        rotation: 日志文件轮转大小
        retention: 日志保留时间
    
    Returns:
        配置好的logger实例
    """
    os.makedirs(log_dir, exist_ok=True)
    
    current_date = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"app_{current_date}.log")
    
    logger.remove()
    
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=rotation,
        retention=retention,
        compression="zip",
        encoding="utf-8"
    )
    
    logger.add(
        lambda msg: print(msg),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )
    
    logger.info("日志系统初始化完成")
    logger.info(f"日志文件路径: {log_file}")
    logger.info(f"日志级别: {log_level}")
    
    return logger

def log_step_start(step_name: str, **kwargs):
    """记录步骤开始"""
    logger.info(f"========== 开始执行: {step_name} ==========")
    if kwargs:
        logger.info(f"参数: {kwargs}")

def log_step_complete(step_name: str, duration: Optional[float] = None, **kwargs):
    """记录步骤完成"""
    if duration:
        logger.info(f"========== 完成执行: {step_name} (耗时: {duration:.2f}秒) ==========")
    else:
        logger.info(f"========== 完成执行: {step_name} ==========")
    if kwargs:
        logger.info(f"结果: {kwargs}")

def log_step_error(step_name: str, error: Exception, context: Optional[dict] = None):
    """记录步骤错误"""
    logger.error(f"========== 执行失败: {step_name} ==========")
    logger.error(f"错误信息: {str(error)}")
    logger.error(f"错误类型: {type(error).__name__}")
    if context:
        logger.error(f"上下文信息: {context}")

def log_data_quality(step_name: str, total: int, success: int, failed: int):
    """记录数据质量统计"""
    rate = (success / total) * 100 if total > 0 else 0
    logger.info(f"[{step_name}] 数据质量统计:")
    logger.info(f"  总数: {total}")
    logger.info(f"  成功: {success}")
    logger.info(f"  失败: {failed}")
    logger.info(f"  成功率: {rate:.2f}%")

def log_api_call(api_name: str, success: bool, duration: float, **kwargs):
    """记录API调用"""
    if success:
        logger.debug(f"API调用成功: {api_name} (耗时: {duration:.2f}秒)")
    else:
        logger.error(f"API调用失败: {api_name} (耗时: {duration:.2f}秒)")
        if kwargs:
            logger.error(f"详细信息: {kwargs}")

def log_validation_result(record_id: str, valid: bool, errors: list = None):
    """记录校验结果"""
    if valid:
        logger.debug(f"校验通过: {record_id}")
    else:
        logger.warning(f"校验失败: {record_id}")
        if errors:
            for error in errors:
                logger.warning(f"  - {error}")

if __name__ == "__main__":
    setup_logger()
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.critical("严重错误")
