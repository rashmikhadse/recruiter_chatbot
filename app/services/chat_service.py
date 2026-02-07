# app/services/chat_service.py

from app.repositories.chat_repo import ChatRepository
from app.repositories.conversation_repo import ConversationRepository

# 🔹 NEW imports for the pipeline
from app.user_query.planner_agent import classify_intent
from app.user_query.metadata_filtering.mongodb_agent import run_mongodb_agent
from app.user_query.response_agent import format_response
from app.job.job_pipeline import run_job_ingestion_pipeline
import asyncio

from app.user_query.bm25_search.bm25_search import run_bm25_search
from app.user_query.semantic_search.semantic_search import run_semantic_search


class ChatService:
    def __init__(self):
        # Repository responsible for storing and retrieving chat messages
        self.chat_repo = ChatRepository()

        # Repository responsible for conversation metadata (title, timestamps)
        self.conversation_repo = ConversationRepository()

    def _generate_title_from_message(self, message: str) -> str:
        """
        Generate a deterministic conversation title from the first user message.
        """

        cleaned = message.strip()

        if not cleaned:
            return "New Chat"

        words = cleaned.split()
        title_words = words[:6]

        return " ".join(title_words).title()

    def process_message(self, conversation_id: str, user_message: str) -> str:
        """
        Process a user message within a conversation.

        PIPELINE:
        UI → Planner → MongoDB Agent → Response Agent → UI
        """

        # --------------------------------------------------
        # 0️⃣ DEFENSIVE CHECK: ensure conversation exists
        # --------------------------------------------------

        conversation = self.conversation_repo.get_by_id(conversation_id)

        if conversation is None:
            conversation = self.conversation_repo.create_conversation(
                user_id="default_user"
            )
            conversation_id = conversation["conversation_id"]

        # --------------------------------------------------
        # 1️⃣ Save the user's message (SOURCE OF TRUTH)
        # --------------------------------------------------

        self.chat_repo.save_message(
            conversation_id=conversation_id,
            role="user",
            message=user_message,
        )

        # --------------------------------------------------
        # 2️⃣ Retrieve message history (used only for title)
        # --------------------------------------------------

        history = self.chat_repo.get_history(conversation_id)
        user_messages = [m for m in history if m["role"] == "user"]
        is_first_message = len(user_messages) == 1

        # --------------------------------------------------
        # 3️⃣ Generate title ONLY on first user message
        # --------------------------------------------------

        if is_first_message:
            title = self._generate_title_from_message(user_message)
            self.conversation_repo.update_title(
                conversation_id=conversation_id,
                title=title,
            )

        
        

        # --------------------------------------------------
        # 4️⃣ PLANNER AGENT — intent classification
        # --------------------------------------------------

        planner_output = classify_intent(user_message)
        print("🧭 Planner response:", planner_output)

        intent = planner_output["intent"]

        # --------------------------------------------------
        # 5️⃣ ROUTING BASED ON PLANNER DECISION
        # --------------------------------------------------

        if intent == "metadata_filtering":
            # MongoDB agent builds + executes query
            results = run_mongodb_agent(user_message)

            # Response agent formats UI-friendly output
            assistant_reply = format_response(user_message, results)


        elif intent == "job_description":

            async def job_flow():
                # 1️⃣ Fetch resumes
                resume_list = run_mongodb_agent(user_message)

                # 2️⃣ JD ingestion (must complete first)
                ingested_job_result = run_job_ingestion_pipeline(user_message)

                # 3️⃣ Run searches in parallel
                bm25_task = asyncio.create_task(
                    run_bm25_search(ingested_job_result, resume_list)
                )

                semantic_task = asyncio.create_task(
                    run_semantic_search(ingested_job_result, resume_list)
                )

                bm25_results, semantic_results = await asyncio.gather(
                    bm25_task, semantic_task
                )

                # 4️⃣ Reciprocal Rank Fusion
                rrf_results = run_rrf(bm25_results, semantic_results)

                # 5️⃣ Response formatting
                return format_response(user_message, rrf_results)

            assistant_reply = asyncio.run(job_flow())


        else:
            # Defensive fallback
            assistant_reply = "Sorry, I could not understand your request."



        self.chat_repo.save_message(
            conversation_id=conversation_id,
            role="assistant",
            message=assistant_reply,
        )

        # --------------------------------------------------
        # 7️⃣ Update conversation timestamp
        # --------------------------------------------------

        self.conversation_repo.update_timestamp(conversation_id)

        # --------------------------------------------------
        # 8️⃣ Return response to UI
        # --------------------------------------------------

        return assistant_reply
