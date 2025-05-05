from typing import Any, Dict, Optional
from .endpoints.agent_datasources import AgentDatasourcesClient
from .endpoints.agents import AgentsClient
from .endpoints.analytics import AnalyticsClient
from .endpoints.authentication import AuthenticationClient
from .endpoints.chats import ChatsClient
from .endpoints.datasources import DatasourcesClient
from .endpoints.documents import DocumentsClient
from .endpoints.embeddings import EmbeddingsClient
from .endpoints.feedback import FeedbackClient
from .endpoints.foundation_models import FoundationModelsClient
from .endpoints.indices import IndicesClient
from .endpoints.jobs import JobsClient
from .endpoints.listen import ListenClient
from .endpoints.messages import MessagesClient
from .endpoints.search import SearchClient
from .endpoints.system import SystemClient
from .endpoints.tenants import TenantsClient
from .endpoints.users import UsersClient
from .endpoints.vector_databases import VectorDatabasesClient
from .output.business_client.core.config import ClientConfig
from .output.business_client.core.http_transport import HttpTransport, HttpxTransport


class APIClient:
    """
Mainio Platform BusinessAPI (version 0.1.0)

# Introduction
Welcome to the Mainio API documentation. This API follows REST principles and provides endpoints for managing tenants, agents, data sources, and more.

## Authentication
All API endpoints require authentication. For user authentication, users must be authenticated via session.

## Authorization
The API implements role-based access control:
- System users can access all tenants and resources
- Internal users (the other servers and services in system) can access all tenants and resources from their origin address
- Regular users can only access their own tenant's resources
- Some endpoints require specific roles (e.g., system) and some only available for internal use

## Common Patterns

### Search Conventions
List endpoints support consistent search parameters for filtering by name:
- Use `startsWith` parameter to find items where the name begins with the given value
- Use `contains` parameter to find items where the name contains the given value anywhere
- Both parameters can be used together to create an AND condition
- Search is case-sensitive
- If no search parameters are provided, returns all items

Examples:
```
GET /api/resource?startsWith=test      # Finds "test-1", "test-index" but not "mytest"
GET /api/resource?contains=test        # Finds "test-1", "mytest", "testing"
GET /api/resource?startsWith=test&contains=index  # Finds "test-index" but not "test-1"
```

### Resource Inclusion
Many endpoints support including related resources via the `include` query parameter:
```
GET /api/tenants/123?include=users,agents,datasources
```

### Response Format
All responses follow a consistent format:
```json
{
  "data": {}, // Response data
  "error": "Error message if any"
}
```

### Error Handling
Common HTTP status codes:
- 200: Success
- 201: Resource created
- 400: Validation error
- 401: Authentication required
- 403: Insufficient permissions
- 404: Resource not found
- 500: Internal server error

### Resource Hierarchy
Resources follow a hierarchical structure:
- /tenants
  - /{tenantId}/agents
    - /{agentId}/chats
      - /{chatId}/messages
  - /{tenantId}/datasources
    - /{dataSourceId}/documents

## Versioning
The API version is included in the response headers.
Breaking changes will be communicated through the version number.


Async API client with pluggable transport, tag-specific clients, and client-level
headers.

Args:
    config (ClientConfig)    : Client configuration object.
    transport (Optional[HttpTransport])
                             : Custom HTTP transport (optional).
    agent_datasources (AgentDatasourcesClient)
                             : Client for 'Agent Datasources' endpoints.
    agents (AgentsClient)    : Client for 'Agents' endpoints.
    analytics (AnalyticsClient)
                             : Client for 'Analytics' endpoints.
    authentication (AuthenticationClient)
                             : Client for 'Authentication' endpoints.
    chats (ChatsClient)      : Client for 'Chats' endpoints.
    datasources (DatasourcesClient)
                             : Client for 'Datasources' endpoints.
    documents (DocumentsClient)
                             : Client for 'Documents' endpoints.
    embeddings (EmbeddingsClient)
                             : Client for 'Embeddings' endpoints.
    feedback (FeedbackClient): Client for 'Feedback' endpoints.
    foundation_models (FoundationModelsClient)
                             : Client for 'Foundation Models' endpoints.
    indices (IndicesClient)  : Client for 'Indices' endpoints.
    jobs (JobsClient)        : Client for 'Jobs' endpoints.
    listen (ListenClient)    : Client for 'Listen' endpoints.
    messages (MessagesClient): Client for 'Messages' endpoints.
    search (SearchClient)    : Client for 'Search' endpoints.
    system (SystemClient)    : Client for 'System' endpoints.
    tenants (TenantsClient)  : Client for 'Tenants' endpoints.
    users (UsersClient)      : Client for 'Users' endpoints.
    vector_databases (VectorDatabasesClient)
                             : Client for 'Vector Databases' endpoints.

    """
    def __init__(self, config: ClientConfig, transport: Optional[HttpTransport] = None) -> None:
        self.config = config
        self.transport = transport if transport is not None else HttpxTransport(str(config.base_url), config.timeout)
        self._base_url: str = str(self.config.base_url)
        self._agent_datasources: Optional[AgentDatasourcesClient] = None
        self._agents: Optional[AgentsClient] = None
        self._analytics: Optional[AnalyticsClient] = None
        self._authentication: Optional[AuthenticationClient] = None
        self._chats: Optional[ChatsClient] = None
        self._datasources: Optional[DatasourcesClient] = None
        self._documents: Optional[DocumentsClient] = None
        self._embeddings: Optional[EmbeddingsClient] = None
        self._feedback: Optional[FeedbackClient] = None
        self._foundation_models: Optional[FoundationModelsClient] = None
        self._indices: Optional[IndicesClient] = None
        self._jobs: Optional[JobsClient] = None
        self._listen: Optional[ListenClient] = None
        self._messages: Optional[MessagesClient] = None
        self._search: Optional[SearchClient] = None
        self._system: Optional[SystemClient] = None
        self._tenants: Optional[TenantsClient] = None
        self._users: Optional[UsersClient] = None
        self._vector_databases: Optional[VectorDatabasesClient] = None
    
    @property
    def agent_datasources(self) -> AgentDatasourcesClient:
        """Client for 'Agent Datasources' endpoints."""
        if self._agent_datasources is None:
            self._agent_datasources = AgentDatasourcesClient(self.transport, self._base_url)
        return self._agent_datasources
    
    @property
    def agents(self) -> AgentsClient:
        """Client for 'Agents' endpoints."""
        if self._agents is None:
            self._agents = AgentsClient(self.transport, self._base_url)
        return self._agents
    
    @property
    def analytics(self) -> AnalyticsClient:
        """Client for 'Analytics' endpoints."""
        if self._analytics is None:
            self._analytics = AnalyticsClient(self.transport, self._base_url)
        return self._analytics
    
    @property
    def authentication(self) -> AuthenticationClient:
        """Client for 'Authentication' endpoints."""
        if self._authentication is None:
            self._authentication = AuthenticationClient(self.transport, self._base_url)
        return self._authentication
    
    @property
    def chats(self) -> ChatsClient:
        """Client for 'Chats' endpoints."""
        if self._chats is None:
            self._chats = ChatsClient(self.transport, self._base_url)
        return self._chats
    
    @property
    def datasources(self) -> DatasourcesClient:
        """Client for 'Datasources' endpoints."""
        if self._datasources is None:
            self._datasources = DatasourcesClient(self.transport, self._base_url)
        return self._datasources
    
    @property
    def documents(self) -> DocumentsClient:
        """Client for 'Documents' endpoints."""
        if self._documents is None:
            self._documents = DocumentsClient(self.transport, self._base_url)
        return self._documents
    
    @property
    def embeddings(self) -> EmbeddingsClient:
        """Client for 'Embeddings' endpoints."""
        if self._embeddings is None:
            self._embeddings = EmbeddingsClient(self.transport, self._base_url)
        return self._embeddings
    
    @property
    def feedback(self) -> FeedbackClient:
        """Client for 'Feedback' endpoints."""
        if self._feedback is None:
            self._feedback = FeedbackClient(self.transport, self._base_url)
        return self._feedback
    
    @property
    def foundation_models(self) -> FoundationModelsClient:
        """Client for 'Foundation Models' endpoints."""
        if self._foundation_models is None:
            self._foundation_models = FoundationModelsClient(self.transport, self._base_url)
        return self._foundation_models
    
    @property
    def indices(self) -> IndicesClient:
        """Client for 'Indices' endpoints."""
        if self._indices is None:
            self._indices = IndicesClient(self.transport, self._base_url)
        return self._indices
    
    @property
    def jobs(self) -> JobsClient:
        """Client for 'Jobs' endpoints."""
        if self._jobs is None:
            self._jobs = JobsClient(self.transport, self._base_url)
        return self._jobs
    
    @property
    def listen(self) -> ListenClient:
        """Client for 'Listen' endpoints."""
        if self._listen is None:
            self._listen = ListenClient(self.transport, self._base_url)
        return self._listen
    
    @property
    def messages(self) -> MessagesClient:
        """Client for 'Messages' endpoints."""
        if self._messages is None:
            self._messages = MessagesClient(self.transport, self._base_url)
        return self._messages
    
    @property
    def search(self) -> SearchClient:
        """Client for 'Search' endpoints."""
        if self._search is None:
            self._search = SearchClient(self.transport, self._base_url)
        return self._search
    
    @property
    def system(self) -> SystemClient:
        """Client for 'System' endpoints."""
        if self._system is None:
            self._system = SystemClient(self.transport, self._base_url)
        return self._system
    
    @property
    def tenants(self) -> TenantsClient:
        """Client for 'Tenants' endpoints."""
        if self._tenants is None:
            self._tenants = TenantsClient(self.transport, self._base_url)
        return self._tenants
    
    @property
    def users(self) -> UsersClient:
        """Client for 'Users' endpoints."""
        if self._users is None:
            self._users = UsersClient(self.transport, self._base_url)
        return self._users
    
    @property
    def vector_databases(self) -> VectorDatabasesClient:
        """Client for 'Vector Databases' endpoints."""
        if self._vector_databases is None:
            self._vector_databases = VectorDatabasesClient(self.transport, self._base_url)
        return self._vector_databases
    
    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Send an HTTP request via the transport."""
        return await self.transport.request(method, url, **kwargs)
    
    async def close(self) -> None:
        """Close the underlying transport if supported."""
        if hasattr(self.transport, 'close'):
            await self.transport.close()
    
    async def __aenter__(self) -> 'APIClient':
        """Enter the async context manager. Returns self."""
        if hasattr(self.transport, '__aenter__'):
            await self.transport.__aenter__()
        return self
    
    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object | None) -> None:
        """Exit the async context manager. Calls close()."""
        if hasattr(self.transport, '__aexit__'):
            await self.transport.__aexit__(exc_type, exc_val, exc_tb)
        else:
            await self.close()
    