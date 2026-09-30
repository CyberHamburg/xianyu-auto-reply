"""
ݿRedis֤ģ

ܣ
1. ֤MySQLǷ
2. ֤RedisǷ
3. GUIã֤ûдϢ
"""
import socket


def check_mysql_connection(host: str, port: int, user: str, password: str, database: str) -> dict:
    """
    MySQLݿ
    
    ͨsocket˿Ƿɴٳpymysqlʵӡ
    
    Args:
        host: MySQLַ
        port: MySQL˿
        user: û
        password: 
        database: ݿ
    Returns:
        ֵ:
        - success: bool Ƿɹ
        - message: str ˵
    """
    # ȼ˿ڿɴ
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
    except socket.timeout:
        return {"success": False, "message": f"ӳʱ޷ӵ {host}:{port}"}
    except socket.error as e:
        return {"success": False, "message": f"{host}:{port} ɴ - {e}"}
    
    # ʵݿ
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10,
            charset="utf8mb4",
        )
        conn.ping(reconnect=False)
        conn.close()
        return {"success": True, "message": "MySQLӳɹ"}
    except ImportError:
        return {"success": False, "message": "ȱpymysql鰲װ"}
    except Exception as e:
        return {"success": False, "message": f"MySQLʧ: {e}"}


def check_redis_connection(host: str, port: int, password: str, db: int) -> dict:
    """
    Redis
    
    ԽRedisӲִPING
    
    Args:
        host: Redisַ
        port: Redis˿
        password: Redis루Ϊַ
        db: Redisݿ
    Returns:
        ֵ:
        - success: bool Ƿɹ
        - message: str ˵
    """
    # ȼ˿ڿɴ
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
    except socket.timeout:
        return {"success": False, "message": f"ӳʱ޷ӵ {host}:{port}"}
    except socket.error as e:
        return {"success": False, "message": f"{host}:{port} ɴ - {e}"}
    
    # ʵRedis
    try:
        import redis
        r = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            db=db,
            socket_connect_timeout=10,
            decode_responses=True,
        )
        r.ping()
        r.close()
        return {"success": True, "message": "Redisӳɹ"}
    except ImportError:
        return {"success": False, "message": "ȱredis鰲װ"}
    except Exception as e:
        return {"success": False, "message": f"Redisʧ: {e}"}
