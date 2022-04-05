from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from routers.carpool import carpools
from services.gtfs import gtfs_rt

router = APIRouter(
    prefix="/gtfs-rt",
    tags=["gtfs-rt"]
)


@router.get("/")
async def read_gtfs_rt(format: str = 'protobuf'):
    data = gtfs_rt(carpools, format)
    if "json" == format.lower():
        return JSONResponse(content=data)
    else:
        return Response(content=data, media_type="application/x-protobuf")
