from fastapi import APIRouter, HTTPException
from app.schemas.agents import Agent
from app.db.firestore import get_firestore_db

router = APIRouter()


@router.post("/add-agent/")
async def add_agent(agent: Agent):
    db = get_firestore_db()

    docs = db.collection("agents").where("id", "==", agent.id).stream()
    if list(docs):
        raise HTTPException(status_code=400, detail="Company ID already exists")

    agent_data = agent.dict()
    db.collection("agents").add(agent_data)
    return {"message": "Agent added successfully!"}


@router.get("/get-agents/")
async def get_all_agents():
    db = get_firestore_db()

    docs = db.collection("agents").stream()

    agents = [doc.to_dict() for doc in docs]

    return agents


@router.get("/get-agent/{id}")
async def get_agent(id: str):
    db = get_firestore_db()

    docs = db.collection("agents").where("id", "==", id).stream()

    agent_data = None
    for doc in docs:
        agent_data = doc.to_dict()

    if not agent_data:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent_data


@router.put("/update-agent/{id}")
async def update_agent(id: str, agent: Agent):
    db = get_firestore_db()

    query = db.collection("agents").where("id", "==", id).limit(1)
    results = query.get()

    if not results:
        raise HTTPException(status_code=404, detail="Agent not found")

    doc_ref = results[0].reference
    doc_ref.update(agent.dict())

    return {"message": "Agent updated successfully!"}


@router.delete("/delete-agent/{id}")
async def delete_agent(id: str):
    db = get_firestore_db()

    query = db.collection("agents").where("id", "==", id).limit(1)
    results = query.get()

    if not results:
        raise HTTPException(status_code=404, detail="Agent not found")

    doc_ref = results[0].reference
    doc_ref.delete()

    return {"message": "Agent deleted successfully!"}
