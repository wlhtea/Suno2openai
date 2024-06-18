import uvicorn

log_config = uvicorn.config.LOGGING_CONFIG
default_format = "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
access_format = (r'%(asctime)s | %(levelname)s | %(client_addr)s: %(request_line)s %(status_code)s | %(filename)s:%('
                 r'lineno)d')
log_config["formatters"]["default"]["fmt"] = default_format
log_config["formatters"]["access"]["fmt"] = access_format
log_config["formatters"]["default"]["datefmt"] = '%Y-%m-%d %H:%M:%S'
log_config["formatters"]["access"]["datefmt"] = '%Y-%m-%d %H:%M:%S'

# 启动服务
uvicorn.run("main:app", host="0.0.0.0", port=8000)
