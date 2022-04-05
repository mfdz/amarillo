from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from routers.carpool import carpools
from services.gtfs import gtfs_rt

router = APIRouter(
    prefix="/gtfs-rt",
    tags=["gtfs-rt"]
)


# TODO add from original spec:
#       parameters:
#         - in: query
#           name: bbox
#           description: Geographical bounding box at least one stop of the offer needs to be contained in, in format minLat,minLon,maxLat,maxLon
#           schema:
#             type: string
#             pattern: ^\-?d{1,2}(.\d{1,7}),-?\d{1,3}(.\d{1,7}),-?\d{1,2}(.\d{1,7}),-?\d{1,3}(.\d{1,7})
#             example: 10,50,11,51

@router.get("/",
            summary="Get GTFS-RT feed",
            description="Returns a GTFS-RT feed including all trip updates since "
                        "yesterday's midnight.")
async def read_gtfs_rt(format: str = 'protobuf'):
    data = gtfs_rt(carpools, format)
    if "json" == format.lower():
        return JSONResponse(content=data)
    else:
        return Response(content=data, media_type="application/x-protobuf")

# TODO /interpolate:
#     post:
#       tags:
#       - gtfs
#       description: Internally performs a street routing between the stops of the supplied carpool and inserts stops in the vicinity of that estimated route as intermediate stops.
#       responses:
