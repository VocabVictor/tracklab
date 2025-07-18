"""W&B Public API for Project objects.

This module provides classes for interacting with W&B projects and their
associated data.

Example:
```python
from tracklab.apis.public import Api

# Get all projects for an entity
projects = Api().projects("entity")

# Access project data
for project in projects:
    print(f"Project: {project.name}")
    print(f"URL: {project.url}")

    # Get artifact types
    # for artifact_type in project.artifacts_types(): # Artifact/Automation functionality removed
        print(f"Artifact Type: {artifact_type.name}")

    # Get sweeps
    for sweep in project.sweeps():
        print(f"Sweep ID: {sweep.id}")
        print(f"State: {sweep.state}")
```

Note:
    This module is part of the W&B Public API and provides methods to access
    and manage projects. For creating new projects, use tracklab.init()
    with a new project name.
"""

from contextlib import suppress

from requests import HTTPError
from tracklab.sdk.internal.internal_api import gql

from tracklab.apis import public
from tracklab.apis.attrs import Attrs
from tracklab.apis.normalize import normalize_exceptions
from tracklab.apis.paginator import Paginator
from tracklab.apis.public.api import RetryingClient
from tracklab.sdk.lib import ipython

PROJECT_FRAGMENT = """fragment ProjectFragment on Project {
    id
    name
    entityName
    createdAt
    isBenchmark
}"""


class Projects(Paginator["Project"]):
    """An iterable collection of `Project` objects.

    An iterable interface to access projects created and saved by the entity.

    Args:
        client (`tracklab.apis.internal.Api`): The API client instance to use.
        entity (str): The entity name (username or team) to fetch projects for.
        per_page (int): Number of projects to fetch per request (default is 50).

    Example:
    ```python
    from tracklab.apis.public.api import Api

    # Find projects that belong to this entity
    projects = Api().projects(entity="entity")

    # Iterate over files
    for project in projects:
        print(f"Project: {project.name}")
        print(f"- URL: {project.url}")
        print(f"- Created at: {project.created_at}")
        print(f"- Is benchmark: {project.is_benchmark}")
    ```
    """

    QUERY = gql(
        """
        query Projects($entity: String, $cursor: String, $perPage: Int = 50) {{
            models(entityName: $entity, after: $cursor, first: $perPage) {{
                edges {{
                    node {{
                        ...ProjectFragment
                    }}
                    cursor
                }}
                pageInfo {{
                    endCursor
                    hasNextPage
                }}
            }}
        }}
        {}
        """.format(PROJECT_FRAGMENT)
    )

    def __init__(
        self,
        client: RetryingClient,
        entity: str,
        per_page: int = 50,
    ) -> "Projects":
        """An iterable collection of `Project` objects.

        Args:
            client: The API client used to query W&B.
            entity: The entity which owns the projects.
            per_page: The number of projects to fetch per request to the API.
        """
        self.client = client
        self.entity = entity
        variables = {
            "entity": self.entity,
        }
        super().__init__(client, variables, per_page)

    @property
    def length(self) -> None:
        """Returns the total number of projects.

        Note: This property is not available for projects.

        <!-- lazydoc-ignore: internal -->
        """
        # For backwards compatibility, even though this isn't a SizedPaginator
        return None

    @property
    def more(self):
        """Returns `True` if there are more projects to fetch. Returns
        `False` if there are no more projects to fetch.

        <!-- lazydoc-ignore: internal -->
        """
        if self.last_response:
            return self.last_response["models"]["pageInfo"]["hasNextPage"]
        else:
            return True

    @property
    def cursor(self):
        """Returns the cursor position for pagination of project results.

        <!-- lazydoc-ignore: internal -->
        """
        if self.last_response:
            return self.last_response["models"]["edges"][-1]["cursor"]
        else:
            return None

    def convert_objects(self):
        """Converts GraphQL edges to File objects.

        <!-- lazydoc-ignore: internal -->
        """
        return [
            Project(self.client, self.entity, p["node"]["name"], p["node"])
            for p in self.last_response["models"]["edges"]
        ]

    def __repr__(self):
        return f"<Projects {self.entity}>"


class Project(Attrs):
    """A project is a namespace for runs.

    Args:
        client: W&B API client instance.
        name (str): The name of the project.
        entity (str): The entity name that owns the project.
    """

    QUERY = gql(
        """
        query Project($project: String!, $entity: String!) {
            project(name: $project, entityName: $entity) {
                id
            }
        }
        """
    )

    def __init__(
        self,
        client: RetryingClient,
        entity: str,
        project: str,
        attrs: dict,
    ) -> "Project":
        """A single project associated with an entity.

        Args:
            client: The API client used to query W&B.
            entity: The entity which owns the project.
            project: The name of the project to query.
            attrs: The attributes of the project.
        """
        super().__init__(dict(attrs))
        self.client = client
        self.name = project
        self.entity = entity

    @property
    def path(self):
        """Returns the path of the project. The path is a list containing the
        entity and project name."""
        return [self.entity, self.name]

    @property
    def url(self):
        """Returns the URL of the project."""
        return self.client.app_url + "/".join(self.path + ["workspace"])

    def to_html(self, height=420, hidden=False):
        """Generate HTML containing an iframe displaying this project.

        <!-- lazydoc-ignore: internal -->
        """
        url = self.url + "?jupyter=true"
        style = f"border:none;width:100%;height:{height}px;"
        prefix = ""
        if hidden:
            style += "display:none;"
            prefix = ipython.toggle_button("project")
        return prefix + f"<iframe src={url!r} style={style!r}></iframe>"

    def _repr_html_(self) -> str:
        return self.to_html()

    def __repr__(self):
        return "<Project {}>".format("/".join(self.path))

    @normalize_exceptions
#         """Returns all artifact types associated with this project."""

    @normalize_exceptions
    def sweeps(self):
        """Fetches all sweeps associated with the project."""
        query = gql(
            """
            query GetSweeps($project: String!, $entity: String!) {{
                project(name: $project, entityName: $entity) {{
                    totalSweeps
                    sweeps {{
                        edges {{
                            node {{
                                ...SweepFragment
                            }}
                            cursor
                        }}
                        pageInfo {{
                            endCursor
                            hasNextPage
                        }}
                    }}
                }}
            }}
            {}
            """.format(public.SWEEP_FRAGMENT)
        )
        variable_values = {"project": self.name, "entity": self.entity}
        ret = self.client.execute(query, variable_values)
        if not ret.get("project") or ret["project"]["totalSweeps"] < 1:
            return []

        return [
            # match format of existing public sweep apis
            public.Sweep(
                self.client,
                self.entity,
                self.name,
                e["node"]["name"],
            )
            for e in ret["project"]["sweeps"]["edges"]
        ]

    _PROJECT_ID = gql(
        """
        query ProjectID($projectName: String!, $entityName: String!) {
            project(name: $projectName, entityName: $entityName) {
                id
            }
        }
        """
    )

    @property
    def id(self) -> str:
        # This is a workaround to ensure that the project ID can be retrieved
        # on demand, as it generally is not set or fetched on instantiation.
        # This is necessary if using this project as the scope of a new Automation.
        with suppress(LookupError):
            return self._attrs["id"]

        variable_values = {"projectName": self.name, "entityName": self.entity}
        try:
            data = self.client.execute(self._PROJECT_ID, variable_values)

            if not data.get("project") or not data["project"].get("id"):
                raise ValueError(f"Project {self.name} not found")

            self._attrs["id"] = data["project"]["id"]
            return self._attrs["id"]
        except (HTTPError, LookupError, TypeError) as e:
            raise ValueError(f"Unable to fetch project ID: {variable_values!r}") from e
