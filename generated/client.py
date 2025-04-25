from typing import Any, Optional

from pyopenapi_gen.http_transport import HttpTransport, HttpxTransport

from .config import ClientConfig


from typing import Optional, Any

from .endpoints.agent_datasources import AgentDatasourcesClient

from .endpoints.agents import AgentsClient

from .endpoints.analytics import AnalyticsClient

from .endpoints.authentication import AuthenticationClient

from .endpoints.chats import ChatsClient

from .endpoints.datasources import DataSourcesClient

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

from .endpoints.tenants import TenantsClient

from pyopenapi_gen.http_transport import HttpTransport, HttpxTransport

class APIClient:
    """Async API client with pluggable transport and tag-specific clients."""

    def __init__(
        self,
        config: ClientConfig,
        transport: Optional[HttpTransport] = None,
    ) -> None:
        self.config = config
        # Use provided transport or default to HttpxTransport (concrete class)
        self.transport = transport if transport is not None else HttpxTransport(
            config.base_url, config.timeout  # type: ignore[arg-type]
        )
        # Initialize tag clients for code completion and typing

        self.agent_datasources = AgentDatasourcesClient(
            self.transport, self.config.base_url
        )

        self.agents = AgentsClient(
            self.transport, self.config.base_url
        )

        self.analytics = AnalyticsClient(
            self.transport, self.config.base_url
        )

        self.authentication = AuthenticationClient(
            self.transport, self.config.base_url
        )

        self.chats = ChatsClient(
            self.transport, self.config.base_url
        )

        self.datasources = DataSourcesClient(
            self.transport, self.config.base_url
        )

        self.datasources = DatasourcesClient(
            self.transport, self.config.base_url
        )

        self.documents = DocumentsClient(
            self.transport, self.config.base_url
        )

        self.embeddings = EmbeddingsClient(
            self.transport, self.config.base_url
        )

        self.feedback = FeedbackClient(
            self.transport, self.config.base_url
        )

        self.foundation_models = FoundationModelsClient(
            self.transport, self.config.base_url
        )

        self.indices = IndicesClient(
            self.transport, self.config.base_url
        )

        self.jobs = JobsClient(
            self.transport, self.config.base_url
        )

        self.listen = ListenClient(
            self.transport, self.config.base_url
        )

        self.messages = MessagesClient(
            self.transport, self.config.base_url
        )

        self.search = SearchClient(
            self.transport, self.config.base_url
        )

        self.system = SystemClient(
            self.transport, self.config.base_url
        )

        self.tenants = TenantsClient(
            self.transport, self.config.base_url
        )

        self.users = UsersClient(
            self.transport, self.config.base_url
        )

        self.vector_databases = VectorDatabasesClient(
            self.transport, self.config.base_url
        )

        self.tenants = TenantsClient(
            self.transport, self.config.base_url
        )


    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Send an HTTP request via the transport."""
        return await self.transport.request(method, url, **kwargs)

    async def close(self) -> None:
        """Close the underlying transport if supported."""
        if hasattr(self.transport, "close"):
            await self.transport.close()