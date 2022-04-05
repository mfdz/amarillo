from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from typing import Dict

from models.Carpool import Carpool

carpools: Dict[str, Carpool] = {
#    cp0.id: cp0,
#    cp1.id: cp1
}

router = APIRouter(
    prefix="/carpool",
    tags=["carpool"]
)

@router.put("/",
         operation_id="updatecarpool",
         summary="Update an existing carpool",
         # TODO description="",
         response_model=Carpool,
         description="Carpool object that should be updated",
         status_code=status.HTTP_202_ACCEPTED,
         # TODO next to the status codes are "Links". There is nothing shown now.
         # Either show something there, or hide the Links, or do nothing.
         responses={400: {"description": "Invalid"},
                    404: {"description": "Carpool not found"},
                    # TODO note that automatic validations against the schema
                    # are returned with code 422, also shown in Swagger.
                    # maybe 405 is not needed?
                    405: {"description": "Validation exception"}})
async def put_carpool(cp: Carpool):
    exists = carpools.get(cp.id) != None

    if not exists:
        raise HTTPException(status_code=404, detail="Carpool not found")

    if cp.lastUpdated == None:
        cp.lastUpdated = datetime.now()

    carpools[cp.id] = cp

    return cp


@router.post("/")
async def post_carpool(cp: Carpool) -> Carpool:
    if cp.lastUpdated == None:
        cp.lastUpdated = datetime.now()

    exists = carpools.get(cp.id) != None

    if exists:
        raise "TODO carpool exist"

    carpools[cp.id] = cp

    return cp


# TODO make use of agencyId
@router.get("/{agencyId}/{carpoolId}")
async def get_carpool(agencyId: str, carpoolId: str) -> Carpool:
    exists = carpools.get(carpoolId) != None

    if not exists:
        return "TODO carpool does not exist"

    return carpools[carpoolId]


# TODO make use of agencyId
@router.delete("/{agencyId}/{carpoolId}")
async def delete_carpool(agencyId: str, carpoolId: str):
    exists = carpools.get(carpoolId) != None

    if not exists:
        return "TODO carpool does not exist"

    carpools[carpoolId] = None
    return "TODO success "
