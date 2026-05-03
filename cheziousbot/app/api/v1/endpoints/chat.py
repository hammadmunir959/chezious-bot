import uuid
import logging
from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service, user_service, session_service
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def chat_endpoint(request: Request, payload: ChatRequest):
    """
    Main conversational endpoint (Async).
    """
    try:
        # 1. Resolve user
        user = await user_service.get_or_404(payload.user_id)
        
        # 2. Resolve thread/session
        thread_id = await session_service.resolve_or_create(user.id, payload.thread_id)
        
        logger.info(f"Incoming chat request for user {user.id} on thread {thread_id}")
        
        # 3. Process chat
        response = await chat_service.process_chat(
            message=payload.message,
            user_id=user.id,
            thread_id=thread_id
        )
        return response
    except HTTPException as e:
        # Re-raise HTTP exceptions to let FastAPI handle them
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in chat_endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )
    
@router.post("/stream")
async def stream_chat_endpoint(request: Request, payload: ChatRequest):
    """
    Streaming conversational endpoint (Async).
    """
    from fastapi.responses import StreamingResponse
    
    try:
        # 1. Resolve user
        user = await user_service.get_or_404(payload.user_id)
        
        # 2. Resolve thread/session
        thread_id = await session_service.resolve_or_create(user.id, payload.thread_id)
        
        logger.info(f"Incoming streaming chat request for user {user.id} on thread {thread_id}")
        
        # 3. Return streaming response
        return StreamingResponse(
            chat_service.stream_chat(
                message=payload.message,
                user_id=user.id,
                thread_id=thread_id
            ),
            media_type="text/event-stream"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in stream_chat_endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming initialization failed: {str(e)}"
        )
