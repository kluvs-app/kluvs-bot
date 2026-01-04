"""
Brains Service - AI intelligence layer powered by kluvs-brain

This service provides the bot's AI capabilities through the kluvs-brain SDK,
which handles RAG-powered questions, book summaries, and Socratic tutoring.

The kluvs-brain engine now supports:
- Enhanced metadata with page_label and content types (CHUNK, GLOSSARY, SUMMARY)
- Improved match thresholds for better quality results
- Scope-aware SQL filtering
"""
from typing import Optional
from kluvs_brain import SocraticEngine, BrainError, RetrievalError, ReasoningError


class BrainsService:
    """
    AI service wrapper for kluvs-brain's SocraticEngine.

    This service provides a Discord-bot-friendly async interface to the AI backend,
    handling RAG-powered questions about books using Socratic tutoring methodology.

    Attributes:
        engine: The underlying SocraticEngine from kluvs-brain
        default_scope: Hardcoded scope filter for the experimental phase
    """

    def __init__(self, supabase_url: str, supabase_key: str, openai_key: str):
        """
        Initialize the brains service with API credentials.

        Args:
            supabase_url: Supabase project URL for the brains backend
            supabase_key: Supabase API key for authentication
            openai_key: OpenAI API key for GPT and embeddings

        Raises:
            ValueError: If any required credentials are missing

        Note:
            The underlying SocraticEngine uses:
            - AsyncOpenAI for reasoning
            - OpenAI text-embedding-3-small for vector search
            - GPT-4o for generating responses
            - Scope-aware SQL filtering with match_threshold=0.2
        """
        if not all([supabase_url, supabase_key, openai_key]):
            raise ValueError("All API credentials required for BrainsService")

        print("[INFO] Initializing BrainsService with SocraticEngine")
        self.engine = SocraticEngine(supabase_url, supabase_key, openai_key)

        # Hardcoded scope for experimental phase
        # TODO: Make this dynamic based on book/session data
        self.default_scope = "humanitarian_ai_experiment"

        print(f"[INFO] BrainsService initialized with default scope: {self.default_scope}")

    async def ask(
        self,
        question: str,
        book_title: str,
        scope: Optional[str] = None
    ) -> str:
        """
        Ask a question about a book using RAG-powered Socratic tutoring.

        This method uses the SocraticEngine to search relevant book excerpts
        and generate a Socratic response with hints and follow-up questions.

        Args:
            question: The student's question about the book
            book_title: Title of the book being discussed
            scope: Optional scope filter for the RAG search
                  (defaults to hardcoded experimental scope)

        Returns:
            Socratic response with hints, context, and follow-up questions

        Raises:
            RetrievalError: If no knowledge is found or database is unavailable
            ReasoningError: If the AI engine fails to generate a response
            BrainError: For other brain-related errors

        Note:
            The SocraticEngine now supports:
            - Enhanced metadata with page_label and type fields
            - Content types: CHUNK, GLOSSARY, SUMMARY
            - Match threshold of 0.2 for better quality
            - Comprehensive logging for debugging
        """
        actual_scope = scope or self.default_scope

        print(f"[INFO] Processing question for book='{book_title}', scope='{actual_scope}'")
        print(f"[INFO] Question: {question}")

        try:
            # Call the async SocraticEngine.ask() method
            # This will:
            # 1. Generate embeddings for the question
            # 2. Search vector DB with scope-aware filtering
            # 3. Build context from retrieved chunks (with type and page_label)
            # 4. Generate Socratic response using GPT-4o
            response = await self.engine.ask(
                student_query=question,
                scope=actual_scope,
                book_title=book_title
            )

            print(f"[SUCCESS] Successfully generated response for '{book_title}'")
            return response

        except RetrievalError as e:
            # Book not found or database unavailable
            print(f"[ERROR] RetrievalError: {str(e)}")
            raise

        except ReasoningError as e:
            # AI engine failed to generate response
            print(f"[ERROR] ReasoningError: {str(e)}")
            raise

        except BrainError as e:
            # Other brain-related errors
            print(f"[ERROR] BrainError: {str(e)}")
            raise

        except Exception as e:
            # Unexpected errors - wrap in BrainError for consistency
            print(f"[ERROR] Unexpected error: {str(e)}")
            raise BrainError(f"Unexpected error: {str(e)}")
