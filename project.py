# pip install fastapi uvicorn pymongo
# run:  uvicorn main:app --reload

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum

from pymongo import MongoClient

app = FastAPI()

client = MongoClient("mongodb://localhost:27017")
db = client["hospital_support"]
requests_col = db["requests"]


@app.get("/")
def home():
    return {"message": "Hospital Support Request System"}


class Category(str, Enum):
    equipment_issue = "EQUIPMENT_ISSUE"
    maintenance = "MAINTENANCE"
    it_issue = "IT_ISSUE"
    facility_request = "FACILITY_REQUEST"


class Status(str, Enum):
    new = "NEW"
    assigned = "ASSIGNED"
    in_progress = "IN_PROGRESS"
    on_hold = "ON_HOLD"
    resolved = "RESOLVED"
    closed = "CLOSED"


class RequestCreate(BaseModel):
    title: str
    description: str
    category: Category
    status: Status


class RequestResponse(RequestCreate):
    id: str


def doc_to_response(doc) -> dict:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


@app.get("/requests")
def request_read_all():
    return [doc_to_response(d) for d in requests_col.find()]


@app.get("/requests/{id}")
def request_read_by_id(id: str):
    doc = requests_col.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Request not found")
    return doc_to_response(doc)


@app.post("/requests", status_code=201, response_model=RequestResponse)
def request_create(payload: RequestCreate):
    result = requests_col.insert_one(payload.model_dump())
    doc = payload.model_dump()
    doc["id"] = str(result.inserted_id)
    return doc


@app.put("/requests/{id}", response_model=RequestResponse)
def request_update(id: str, payload: RequestCreate):
    result = requests_col.update_one({"_id": ObjectId(id)}, {"$set": payload.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    doc = payload.model_dump()
    doc["id"] = id
    return doc


@app.delete("/requests/{id}")
def request_delete(id: str):
    result = requests_col.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Request deleted"}