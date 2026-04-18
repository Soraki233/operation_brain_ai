import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.deps import get_current_user
from db.models.user import User
from db.session import AsyncSession, AsyncSessionLocal, get_db
from repository.chat_repo import ChatRepo
from repository.knowledge_repo import KnowledgeRepo
from schema.chat_schema import (
    ChatAskSchema,
    ChatCitationSchema,
    ChatMessageItemSchema,
    ChatThreadCreateSchema,
    ChatThreadItemSchema,
)
from core.reponse import success_response
from service.agent_service import AgentService


logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["chat"])


# --------------------------------- 工具 ---------------------------------


def _message_to_schema(message) -> ChatMessageItemSchema:
    """把 ChatMessage ORM 对象转成 schema，citations 从 meta_json 反序列化。"""
    raw_citations = (message.meta_json or {}).get("citations") or []
    citations = [
        ChatCitationSchema.model_validate(c) for c in raw_citations
    ]
    return ChatMessageItemSchema(
        id=message.id,
        role=message.role,
        content=message.content,
        citations=citations,
        created_at=message.created_at,
    )


def _sse_event(event: str, data: dict) -> str:
    """格式化单个 SSE 事件帧。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ------------------------------ 会话 CRUD ------------------------------


@chat_router.post("/threads", summary="创建会话")
async def create_thread(
    payload: ChatThreadCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = await ChatRepo.create_thread(current_user, payload.title, db)
    return success_response(data=ChatThreadItemSchema.model_validate(thread))


@chat_router.get("/threads", summary="获取当前用户的会话列表")
async def list_threads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    threads = await ChatRepo.list_threads(current_user, db)
    return success_response(
        data=[ChatThreadItemSchema.model_validate(t) for t in threads]
    )


@chat_router.delete("/threads/{thread_id}", summary="删除会话（软删）")
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = await ChatRepo.delete_thread(thread_id, current_user, db)
    return success_response(data=ChatThreadItemSchema.model_validate(thread))


@chat_router.get(
    "/threads/{thread_id}/messages", summary="获取会话的消息列表"
)
async def list_messages(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    messages = await ChatRepo.list_messages(thread_id, current_user, db)
    return success_response(
        data=[_message_to_schema(m) for m in messages]
    )


# --------------------------------- 问答（SSE） ---------------------------------


@chat_router.post(
    "/threads/{thread_id}/ask",
    summary="RAG 问答（SSE 流式）",
    response_model=None,
)
async def ask(
    thread_id: str,
    payload: ChatAskSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE 协议：
    - event: citations   data: { citations: [...] }
    - event: token       data: { delta: "..." }（多条）
    - event: done        data: { message_id, title }
    - event: error       data: { message }（流内错误）

    说明：StreamingResponse 的生命周期独立于 Depends 注入的 db（请求体结束即关闭），
    因此在 generator 里另开 AsyncSessionLocal() 保证长连接期间持有有效 session。
    """
    # 先用请求级 session 完成用户消息落库 + 权限校验，避免 SSE 建连后才报错
    thread = await ChatRepo.get_thread(thread_id, current_user, db)
    question = payload.content.strip()
    if not question:
        raise HTTPException(status_code=400, detail="提问内容不能为空")

    await ChatRepo.append_message(thread, "user", question, db)
    # 首次提问用用户问题回填标题
    if thread.title == "新对话":
        await ChatRepo.update_thread_title(thread, question[:20], db)

    # 若前端没有传 kb_ids，按当前用户可见的全部知识库检索
    if payload.kb_ids:
        kb_ids = list(payload.kb_ids)
    else:
        kbs = await KnowledgeRepo.get_knowledge_list(current_user.id, db)
        kb_ids = [kb.id for kb in kbs]

    # 历史（不含刚追加的 user 消息）—— 这里直接重新拉最近 N 条（含刚追加的）也可以，
    # 但 build_messages 末尾再单独追加一次 HumanMessage，所以这里排除最新的 user 消息。
    history_all = await ChatRepo.get_recent_messages(thread.id, db)
    if history_all and history_all[-1].role == "user":
        history_all = history_all[:-1]

    agent = AgentService()

    async def event_stream() -> AsyncIterator[str]:
        # 在生成器内部用独立 session，保证 SSE 长连接期间持有有效连接
        async with AsyncSessionLocal() as session:
            try:
                # 重新拉会话引用
                result_thread = await ChatRepo.get_thread(
                    thread.id, current_user, session
                )

                citations, context_text = await agent.retrieve(
                    question, kb_ids=kb_ids, db=session
                )
                yield _sse_event("citations", {"citations": citations})

                buffer: list[str] = []
                async for token in agent.astream_answer(
                    history_all, context_text, question
                ):
                    buffer.append(token)
                    yield _sse_event("token", {"delta": token})

                answer = "".join(buffer).strip()
                assistant_message = await ChatRepo.append_message(
                    result_thread,
                    "assistant",
                    answer,
                    session,
                    citations=citations,
                )

                yield _sse_event(
                    "done",
                    {
                        "message_id": assistant_message.id,
                        "title": result_thread.title,
                    },
                )
            except Exception as e:
                logger.exception("SSE 问答失败: thread_id=%s", thread_id)
                yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # 关闭反向代理缓冲，保证 token 及时下发
            "X-Accel-Buffering": "no",
        },
    )
