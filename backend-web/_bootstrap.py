"""
Backend-Web߼

ҵ߼ڴļʵ֣main.py ΪС׮

ܣ
1. FastAPIӦ
2. CORS
3. ؾ̬ļĿ¼
4. ־ʹloguru
5. API·
6. ͳһ
7. ݿӼ
"""
from __future__ import annotations

import asyncio
import faulthandler
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from common.db.error_messages import get_public_database_error_message
from common.utils.logging_utils import setup_logging
from common.utils.network_utils import resolve_listen_host

faulthandler.enable()

settings = get_settings()

# ־̨ + ļ + أ
setup_logging(
    log_file=Path(__file__).parent / "logs" / "backend-web.log",
    log_level=settings.log_level,
    third_party_loggers=["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "httpx", "httpcore", "sqlalchemy"],
)


async def check_database_connection():
    """
    ݿ
    
    ʧܣ¼˳
    """
    try:
        from common.db.session import async_engine
        from sqlalchemy import text
        
        logger.info("ڼݿ...")
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("ݿӳɹ")
        return True
    except Exception as e:
        logger.error(f"ݿʧ: {str(e)}")
        logger.error("ݿú")
        logger.error(f"ݿַ: {settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ӧڹ"""
    logger.info(f"{settings.project_name} ...")
    logger.info(f"˿: {settings.service_port}")
    logger.info(f"ݿ: {settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}")
    
    # ݿ
    if not await check_database_connection():
        logger.error("ݿʧܣ˳")
        sys.exit(1)
    
    # ʼݿ⣨Ĭݵȣ
    try:
        from common.db.init_database import init_database
        await init_database()
    except Exception as e:
        logger.error(f"ݿʼʧ: {e}")
    
    # Լ JWT Կ/ĬֵʱԶǿԿ־ûԴף
    try:
        from app.services.jwt_secret_service import ensure_jwt_secret_key
        await ensure_jwt_secret_key(settings)
    except Exception as e:
        logger.error(f"JWT ԿԼʧ: {e}")

    # ʼ API ƣͨݿ⹲ͬһơ
    try:
        from common.utils.internal_token_service import ensure_internal_api_token
        await ensure_internal_api_token(settings)
    except Exception as e:
        logger.error(f"ڲ API Ƴʼʧ: {e}")
        raise

    # Լ AI ̻񣺰ǰĽΪʧܣ״̬Զִͣ
    try:
        from app.services.ai_listing_task_service import mark_stale_running_failed
        await mark_stale_running_failed()
    except Exception as e:
        logger.error(f"AI̻Լʧ: {e}")

    # ݿ־
    from common.utils.logging_utils import apply_db_log_retention, run_db_log_retention_sync
    await apply_db_log_retention()
    log_retention_sync_task = asyncio.create_task(run_db_log_retention_sync())
    
    # ȷϴĿ¼
    static_path = Path(settings.static_dir)
    upload_dirs = [
        static_path / "uploads",
        static_path / "uploads" / "face",
        static_path / "uploads" / "default_reply",
        static_path / "uploads" / "item_reply",
        static_path / "uploads" / "keywords",
        static_path / "uploads" / "confirm_receipt",
        static_path / "uploads" / "images",
        static_path / "uploads" / "files",
    ]
    for upload_dir in upload_dirs:
        upload_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"̬ļĿ¼: {static_path.absolute()}")
    logger.info("ϴĿ¼Ѵ")
    
    #  Goofish ʱɼ񣨿ͨýã
    if settings.auto_start_crawl_jobs:
        try:
            await start_goofish_crawl_jobs()
        except Exception as e:
            logger.error(f" Goofish ʱɼʧ: {e}")
    else:
        logger.info("ѽԶGoofishʱɼAUTO_START_CRAWL_JOBS=false")
    
    yield
    
    logger.info(f"{settings.project_name} ر...")
    
    # ֹͣIMỰ
    try:
        from app.services.chat_new import get_im_session_manager
        chat_manager = get_im_session_manager()
        await chat_manager.disconnect_all()
        logger.info("IMỰֹͣ")
    except Exception as e:
        logger.error(f"ֹͣIMỰʧ: {e}")
    
    # ֹͣ Goofish ʱɼ
    try:
        await stop_goofish_crawl_jobs()
    except Exception as e:
        logger.error(f"ֹͣ Goofish ʱɼʧ: {e}")
    
    # رHTTPͻ
    from app.core.http_client import close_http_client
    await close_http_client()
    logger.info("HTTPͻѹر")

    # رոõ goofish API ӳ
    from common.services.order_service import close_goofish_connector
    await close_goofish_connector()
    logger.info("goofish API ӳѹر")

    log_retention_sync_task.cancel()
    try:
        await log_retention_sync_task
    except asyncio.CancelledError:
        pass


async def start_goofish_crawl_jobs():
    """õ Goofish ʱɼ"""
    from app.services.goofish_crawler import get_goofish_crawl_manager
    from common.db.session import async_session_maker
    from sqlalchemy import select
    from common.models.goofish_crawl_job import GoofishCrawlJob
    
    logger.info("ʼ Goofish ʱɼ...")
    
    manager = get_goofish_crawl_manager()
    
    async with async_session_maker() as session:
        # ѯõ
        result = await session.execute(
            select(GoofishCrawlJob).where(GoofishCrawlJob.enabled == True)
        )
        jobs = result.scalars().all()
        
        started_count = 0
        for job in jobs:
            try:
                manager.start_job(job_id=job.id)
                started_count += 1
                logger.info(f" Goofish ɼ: job_id={job.id}, keyword={job.keyword}")
            except Exception as e:
                logger.error(f" Goofish ɼʧ: job_id={job.id}, error={e}")
        
        logger.info(f"Goofish ʱɼɣ {started_count} ")


async def stop_goofish_crawl_jobs():
    """ֹͣ Goofish ʱɼ"""
    from app.services.goofish_crawler import get_goofish_crawl_manager
    
    try:
        manager = get_goofish_crawl_manager()
        await manager.stop_all()
        logger.info(" Goofish ʱɼֹͣ")
    except Exception as e:
        logger.error(f"ֹͣ Goofish ʱɼʧ: {e}")


# FastAPIӦ
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ؾ̬ļĿ¼
static_path = Path(settings.static_dir)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"̬ļ·ѹ: /static -> {static_path.absolute()}")


# API·
from app.api import api_router

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    ӿ
    
    Returns:
        񽡿״̬
    """
    from common.db.session import async_engine
    from sqlalchemy import text
    
    # ݿ
    db_status = "unknown"
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        logger.error(f"ݿӼʧ: {str(e)}")
        db_status = "disconnected"
    
    return {
        "success": True,
        "code": 200,
        "message": "",
        "data": {
            "service": settings.project_name,
            "version": settings.version,
            "status": "running",
            "database": db_status,
        },
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """ HTTP 쳣תΪĿͳһ HTTP 200 ҵӦ"""
    logger.warning(
        "HTTP쳣: {} - {}\n·: {}\n󷽷: {}",
        exc.status_code,
        exc.detail,
        request.url.path,
        request.method,
    )
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """УתΪĿͳһ HTTP 200 ҵӦ"""
    # ¼ Pydantic error пܰԭģCookieݣ
    error_fields = [
        {
            "loc": [str(part) for part in error.get("loc", ())],
            "type": str(error.get("type", "unknown")),
        }
        for error in exc.errors()
    ]
    logger.warning(
        "Уʧ: fields={}\n·: {}\n󷽷: {}",
        error_fields,
        request.url.path,
        request.method,
    )
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "code": 400,
            "message": "ȷ",
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    ȫ쳣
    
    δ쳣,ͳһʽĴӦ
    """
    # ¼־
    # ע⣺loguru Ĭ϶ message  str.format(*args, **kwargs)
    #  f-string  str(exc) ƴ message str(exc) к '{xxx}' 
    #  ResponseValidationError ıͺ dict repr
    # loguru Щ '{xxx}' Ϊ format ռλ KeyError
    # ȫ쳣ڸԭʼ
    # Ѷֵ̬ͨλò룬message  '{}' ռλargs ڵ '{' ᱻ format
    # ͬʱ logger.opt(exception=exc)  loguru Զ tracebackɵ exc_info=True
    logger.opt(exception=exc).error(
        "ȫ쳣: {}: {}\n·: {}\n󷽷: {}",
        type(exc).__name__,
        str(exc),
        request.url.path,
        request.method,
    )
    
    # HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=200,  # ͳһ200
            content={
                "success": False,
                "code": exc.status_code,
                "message": exc.detail,
                "data": None,
            },
        )
    
    # ֪ʩ쳣תΪʾû¶ջݿַ
    public_error_message = get_public_database_error_message(exc)

    # 쳣
    return JSONResponse(
        status_code=200,  # ͳһ200
        content={
            "success": False,
            "code": 500,
            "message": public_error_message or f"ڲ: {str(exc)}",
            "data": None,
        },
    )


def run_server():
    """HTTP񣨹 main.py  __main__ ã"""
    import uvicorn

    # ַĬ :: ˫ջWindows  IPv6 ʱԶ˵ 0.0.0.0
    listen_host = resolve_listen_host(settings.host, settings.service_port)

    uvicorn.run(
        "main:app",
        host=listen_host,
        port=settings.service_port,
        reload=False,
        log_level=settings.log_level.lower(),
        # ־ãȷ Uvicorn ־Ҳͨ־ error.log
        log_config=None,
    )
