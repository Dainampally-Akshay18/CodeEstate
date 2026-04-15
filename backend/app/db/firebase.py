"""
Firebase Database Connection and CRUD Operations.

Handles Firestore initialization and provides a clean database abstraction layer
for all CRUD operations. Single source of truth for database interactions.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from app.config import get_settings


class FirebaseConnectionError(Exception):
    """Base exception for Firebase connection errors."""
    pass


class FirebaseInitializationError(FirebaseConnectionError):
    """Raised when Firebase initialization fails."""
    pass


class FirebaseOperationError(FirebaseConnectionError):
    """Raised when a Firestore operation fails."""
    pass


class FirebaseConnection:
    """
    Firebase Firestore connection manager and CRUD operations.
    
    Implements singleton pattern for centralized database access.
    """

    _instance = None  # Singleton instance
    _db = None  # Firestore client

    def __init__(self):
        """Initialize Firebase connection."""
        if FirebaseConnection._db is None:
            self._initialize_connection()

    def _initialize_connection(self):
        """
        Initialize Firestore connection using Admin SDK.
        
        Reads Firebase credentials from environment variables and establishes
        a connection to Firestore. Uses singleton pattern to ensure only
        one database client is created.
        
        Raises:
            FirebaseInitializationError: If initialization fails.
        """
        try:
            settings = get_settings()
            
            # Build credentials from environment variables
            cred_dict = {
                "type": settings.firebase_type,
                "project_id": settings.firebase_project_id,
                "private_key_id": settings.firebase_private_key_id,
                "private_key": settings.firebase_private_key,
                "client_email": settings.firebase_client_email,
                "client_id": settings.firebase_client_id,
                "auth_uri": settings.firebase_auth_uri,
                "token_uri": settings.firebase_token_uri,
                "auth_provider_x509_cert_url": settings.firebase_auth_provider_x509_cert_url,
                "client_x509_cert_url": settings.firebase_client_x509_cert_url,
            }
            
            # Initialize Firebase app if not already done
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            
            # Get Firestore client
            FirebaseConnection._db = firestore.client()
        
        except Exception as e:
            raise FirebaseInitializationError(
                f"Failed to initialize Firebase: {str(e)}"
            )

    @classmethod
    def get_instance(cls) -> "FirebaseConnection":
        """
        Get or create Firebase connection singleton.
        
        Returns:
            FirebaseConnection: Singleton instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_db(cls):
        """
        Get Firestore client instance.
        
        Returns:
            firestore.Client: Firestore database client.
            
        Raises:
            FirebaseConnectionError: If client not initialized.
        """
        if cls._db is None:
            cls.get_instance()
        return cls._db


# ============================================================================
# DATABASE ACCESS LAYER
# ============================================================================

def get_db():
    """
    Get Firestore database client.
    
    Returns:
        firestore.Client: Firestore client for database operations.
    """
    return FirebaseConnection.get_db()


def get_room_ref(room_id: str):
    """
    Get reference to a room document in Firestore.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        DocumentReference: Reference to the room document.
    """
    return get_db().collection("rooms").document(room_id)


def get_game_state_ref(room_id: str):
    """
    Get reference to game state subcollection.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        CollectionReference: Reference to game_state collection.
    """
    return get_room_ref(room_id).collection("game_state")


# ============================================================================
# CRUD OPERATIONS - GENERIC
# ============================================================================

def set_document(
    collection: str,
    document_id: str,
    data: Dict[str, Any]
) -> None:
    """
    Set/create a document in Firestore (overwrites if exists).
    
    Args:
        collection: Collection name.
        document_id: Document ID.
        data: Document data (must be JSON-serializable).
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        get_db().collection(collection).document(document_id).set(data)
    except Exception as e:
        raise FirebaseOperationError(
            f"Failed to set document {document_id} in {collection}: {str(e)}"
        )


def get_document(
    collection: str,
    document_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get a document from Firestore.
    
    Args:
        collection: Collection name.
        document_id: Document ID.
        
    Returns:
        Dict: Document data, or None if not found.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        doc = get_db().collection(collection).document(document_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        raise FirebaseOperationError(
            f"Failed to get document {document_id} from {collection}: {str(e)}"
        )


def update_document(
    collection: str,
    document_id: str,
    data: Dict[str, Any]
) -> None:
    """
    Update specific fields in a Firestore document (merge, not overwrite).
    
    Args:
        collection: Collection name.
        document_id: Document ID.
        data: Fields to update (partial update).
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        get_db().collection(collection).document(document_id).update(data)
    except Exception as e:
        raise FirebaseOperationError(
            f"Failed to update document {document_id} in {collection}: {str(e)}"
        )


def delete_document(
    collection: str,
    document_id: str
) -> None:
    """
    Delete a document from Firestore.
    
    Args:
        collection: Collection name.
        document_id: Document ID.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        get_db().collection(collection).document(document_id).delete()
    except Exception as e:
        raise FirebaseOperationError(
            f"Failed to delete document {document_id} from {collection}: {str(e)}"
        )


def query_collection(
    collection: str,
    where_clause: tuple = None
) -> List[Dict[str, Any]]:
    """
    Query documents from a Firestore collection.
    
    Args:
        collection: Collection name.
        where_clause: Optional tuple (field, operator, value) for filtering.
        
    Returns:
        List: All matching documents.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        query = get_db().collection(collection)
        
        if where_clause:
            field, operator, value = where_clause
            query = query.where(field, operator, value)
        
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        raise FirebaseOperationError(
            f"Failed to query collection {collection}: {str(e)}"
        )


# ============================================================================
# ROOM-SPECIFIC OPERATIONS
# ============================================================================

def create_room(room_data: Dict[str, Any]) -> str:
    """
    Create a new room document in Firestore.
    
    Args:
        room_data: Room data including room_id.
        
    Returns:
        str: Room ID.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    room_id = room_data.get("room_id")
    if not room_id:
        raise ValueError("room_data must include room_id")
    
    try:
        set_document("rooms", room_id, room_data)
        return room_id
    except Exception as e:
        raise FirebaseOperationError(f"Failed to create room: {str(e)}")


def get_room(room_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a room document from Firestore.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        Dict: Room data, or None if not found.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    return get_document("rooms", room_id)


def update_room(room_id: str, room_data: Dict[str, Any]) -> None:
    """
    Update a room document in Firestore.
    
    Args:
        room_id: Room identifier.
        room_data: Fields to update.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        update_document("rooms", room_id, room_data)
    except Exception as e:
        raise FirebaseOperationError(f"Failed to update room {room_id}: {str(e)}")


def delete_room(room_id: str) -> None:
    """
    Delete a room document from Firestore.
    
    Args:
        room_id: Room identifier.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        delete_document("rooms", room_id)
    except Exception as e:
        raise FirebaseOperationError(f"Failed to delete room {room_id}: {str(e)}")


def list_rooms(status_filter: str = None) -> List[Dict[str, Any]]:
    """
    List all rooms, optionally filtered by status.
    
    Args:
        status_filter: Optional status to filter by (e.g., "waiting", "playing").
        
    Returns:
        List: All matching room documents.
        
    Raises:
        FirebaseOperationError: If operation fails.
    """
    try:
        if status_filter:
            return query_collection("rooms", ("status", "==", status_filter))
        else:
            return query_collection("rooms")
    except Exception as e:
        raise FirebaseOperationError(f"Failed to list rooms: {str(e)}")


# ============================================================================
# TRANSACTION OPERATIONS (for atomic updates)
# ============================================================================

def update_room_transaction(room_id: str, update_func) -> Any:
    """
    Perform an atomic transaction on a room document.
    
    Use this for operations that need to read and write atomically,
    preventing race conditions.
    
    Args:
        room_id: Room identifier.
        update_func: Function that takes room_data and returns updated data.
        
    Returns:
        Any: Result from the update function.
        
    Raises:
        FirebaseOperationError: If transaction fails.
    """
    try:
        @firestore.transactional
        def update_in_transaction(transaction, ref):
            snapshot = ref.get(transaction=transaction)
            if not snapshot.exists:
                raise ValueError(f"Room {room_id} not found")
            
            current_data = snapshot.to_dict()
            updated_data = update_func(current_data)
            transaction.update(ref, updated_data)
            return updated_data
        
        db = get_db()
        transaction = db.transaction()
        ref = get_room_ref(room_id)
        
        return update_in_transaction(transaction, ref)
    
    except Exception as e:
        raise FirebaseOperationError(
            f"Failed to perform transaction on room {room_id}: {str(e)}"
        )
