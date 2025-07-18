"""W&B Public API for Report objects.

This module provides classes for interacting with W&B reports and
managing report-related data.
"""

import ast
import json
import re
import urllib

from tracklab.sdk.internal.internal_api import gql

import tracklab
from tracklab.apis import public
from tracklab.apis.attrs import Attrs
from tracklab.apis.paginator import SizedPaginator
from tracklab.sdk.lib import ipython


class Reports(SizedPaginator["BetaReport"]):
    """Reports is an iterable collection of `BetaReport` objects.

    Args:
        client (`tracklab.apis.internal.Api`): The API client instance to use.
        project (`tracklab.sdk.internal.Project`): The project to fetch reports from.
        name (str, optional): The name of the report to filter by. If `None`,
            fetches all reports.
        entity (str, optional): The entity name for the project. Defaults to
            the project entity.
        per_page (int): Number of reports to fetch per page (default is 50).
    """

    QUERY = gql(
        """
        query ProjectViews($project: String!, $entity: String!, $reportCursor: String,
            $reportLimit: Int!, $viewType: String = "runs", $viewName: String) {
            project(name: $project, entityName: $entity) {
                allViews(viewType: $viewType, viewName: $viewName, first:
                    $reportLimit, after: $reportCursor) {
                    edges {
                        node {
                            id
                            name
                            displayName
                            description
                            user {
                                username
                                photoUrl
                                email
                            }
                            spec
                            updatedAt
                            createdAt
                        }
                        cursor
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }

                }
            }
        }
        """
    )

    def __init__(self, client, project, name=None, entity=None, per_page=50):
        self.project = project
        self.name = name
        variables = {
            "project": project.name,
            "entity": project.entity,
            "viewName": self.name,
        }
        super().__init__(client, variables, per_page)

    @property
    def _length(self):
        """The number of reports in the project.

        <!-- lazydoc-ignore: internal -->
        """
        # TODO: Add the count the backend
        if self.last_response:
            return len(self.objects)
        else:
            return None

    @property
    def more(self) -> bool:
        """Returns whether there are more files to fetch.

        <!-- lazydoc-ignore: internal -->
        """
        if self.last_response:
            return bool(
                self.last_response["project"]["allViews"]["pageInfo"]["hasNextPage"]
            )
        else:
            return True

    @property
    def cursor(self):
        """Returns the cursor position for pagination of file results.

        <!-- lazydoc-ignore: internal -->
        """
        if self.last_response:
            return self.last_response["project"]["allViews"]["edges"][-1]["cursor"]
        else:
            return None

    def update_variables(self):
        """Updates the GraphQL query variables for pagination."""
        self.variables.update(
            {"reportCursor": self.cursor, "reportLimit": self.per_page}
        )

    def convert_objects(self):
        """Converts GraphQL edges to File objects."""
        if self.last_response["project"] is None:
            raise ValueError(
                f"Project {self.variables['project']} does not exist under entity {self.variables['entity']}"
            )
        return [
            BetaReport(
                self.client,
                r["node"],
                entity=self.project.entity,
                project=self.project.name,
            )
            for r in self.last_response["project"]["allViews"]["edges"]
        ]

    def __repr__(self):
        return "<Reports {}>".format("/".join(self.project.path))


class BetaReport(Attrs):
    """BetaReport is a class associated with reports created in W&B.

    WARNING: this API will likely change in a future release

    Attributes:
        id (string): unique identifier of the report
        name (string): report name
        display_name (string): display name of the report
        description (string): report description
        user (User): the user that created the report (contains username and email)
        spec (dict): the spec of the report
        url (string): the url of the report
        updated_at (string): timestamp of last update
        created_at (string): timestamp when the report was created
    """

    def __init__(self, client, attrs, entity=None, project=None):
        self.client = client
        self.project = project
        self.entity = entity
        self.query_generator = public.QueryGenerator()
        super().__init__(dict(attrs))

        if "spec" in self._attrs:
            if isinstance(self._attrs["spec"], str):
                self._attrs["spec"] = json.loads(self._attrs["spec"])
        else:
            self._attrs["spec"] = {}

    @property
    def spec(self):
        return self._attrs["spec"]

    @property
    def sections(self):
        """Get the panel sections (groups) from the report."""
        return self.spec["panelGroups"]

    def runs(self, section, per_page=50, only_selected=True):
        """Get runs associated with a section of the report."""
        run_set_idx = section.get("openRunSet", 0)
        run_set = section["runSets"][run_set_idx]
        order = self.query_generator.key_to_server_path(run_set["sort"]["key"])
        if run_set["sort"].get("ascending"):
            order = "+" + order
        else:
            order = "-" + order
        filters = self.query_generator.filter_to_mongo(run_set["filters"])
        if only_selected:
            # TODO: handle this not always existing
            filters["$or"][0]["$and"].append(
                {"name": {"$in": run_set["selections"]["tree"]}}
            )
        return public.Runs(
            self.client,
            self.entity,
            self.project,
            filters=filters,
            order=order,
            per_page=per_page,
        )

    @property
    def id(self):
        return self._attrs.get("id")

    @property
    def name(self):
        return self._attrs.get("name")

    @property
    def display_name(self):
        return self._attrs.get("displayName")

    @property
    def description(self):
        return self._attrs.get("description")

    @property
    def user(self):
        return self._attrs.get("user")

    @property
    def updated_at(self):
        return self._attrs.get("updatedAt")

    @property
    def created_at(self):
        return self._attrs.get("createdAt")

    @property
    def url(self):
        if (
            not self.client
            or not self.entity
            or not self.project
            or not self.display_name
            or not self.id
        ):
            return None
        return self.client.app_url + "/".join(
            [
                self.entity,
                self.project,
                "reports",
                "--".join(
                    [
                        # made this more closely match the url creation in the frontend (https://github.com/wandb/core/blob/76943979c8e967f7a62dae8bef0a001a2672584c/frontends/app/src/util/report/urls.ts#L19)
                        urllib.parse.quote(
                            re.sub(
                                r"-+", "-", re.sub(r"\W", "-", self.display_name)
                            ).strip("-")
                        ),
                        self.id.replace("=", ""),
                    ]
                ),
            ]
        )

    def to_html(self, height=1024, hidden=False):
        """Generate HTML containing an iframe displaying this report."""
        url = self.url
        if url is None:
            return "<div>Report URL not available</div>"
        url = url + "?jupyter=true"
        style = f"border:none;width:100%;height:{height}px;"
        prefix = ""
        if hidden:
            style += "display:none;"
            prefix = ipython.toggle_button("report")
        return prefix + f"<iframe src={url!r} style={style!r}></iframe>"

    def _repr_html_(self) -> str:
        return self.to_html()


class PythonMongoishQueryGenerator:
    """Converts Python-style query expressions to MongoDB-style queries for W&B reports.

    <!-- lazydoc-ignore-class: internal -->
    """

    SPACER = "----------"
    DECIMAL_SPACER = ";;;"
    FRONTEND_NAME_MAPPING = {
        "ID": "name",
        "Name": "displayName",
        "Tags": "tags",
        "State": "state",
        "CreatedTimestamp": "createdAt",
        "Runtime": "duration",
        "User": "username",
        "Sweep": "sweep",
        "Group": "group",
        "JobType": "jobType",
        "Hostname": "host",
        "UsingArtifact": "inputArtifacts",
        "OutputtingArtifact": "outputArtifacts",
        "Step": "_step",
        "Relative Time (Wall)": "_absolute_runtime",
        "Relative Time (Process)": "_runtime",
        "Wall Time": "_timestamp",
        # "GroupedRuns": "__wb_group_by_all"
    }
    FRONTEND_NAME_MAPPING_REVERSED = {v: k for k, v in FRONTEND_NAME_MAPPING.items()}
    AST_OPERATORS = {
        ast.Lt: "$lt",
        ast.LtE: "$lte",
        ast.Gt: "$gt",
        ast.GtE: "$gte",
        ast.Eq: "=",
        ast.Is: "=",
        ast.NotEq: "$ne",
        ast.IsNot: "$ne",
        ast.In: "$in",
        ast.NotIn: "$nin",
        ast.And: "$and",
        ast.Or: "$or",
        ast.Not: "$not",
    }

    AST_FIELDS = {
        ast.Constant: "value",
        ast.Name: "id",
        ast.List: "elts",
        ast.Tuple: "elts",
    }

    def __init__(self, run_set):
        self.run_set = run_set
        self.panel_metrics_helper = PanelMetricsHelper()

    def _handle_compare(self, node):
        # only left side can be a col
        left = self.front_to_back(self._handle_fields(node.left))
        op = self._handle_ops(node.ops[0])
        right = self._handle_fields(node.comparators[0])

        # Eq has no op for some reason
        if op == "=":
            return {left: right}
        else:
            return {left: {op: right}}

    def _handle_fields(self, node):
        result = getattr(node, self.AST_FIELDS.get(type(node)))
        if isinstance(result, list):
            return [self._handle_fields(node) for node in result]
        elif isinstance(result, str):
            return self._unconvert(result)
        return result

    def _handle_ops(self, node):
        return self.AST_OPERATORS.get(type(node))

    def _replace_numeric_dots(self, s):
        numeric_dots = []
        for i, (left, mid, right) in enumerate(zip(s, s[1:], s[2:]), 1):
            if mid == ".":
                if (
                    left.isdigit()
                    and right.isdigit()  # 1.2
                    or left.isdigit()
                    and right == " "  # 1.
                    or left == " "
                    and right.isdigit()  # .2
                ):
                    numeric_dots.append(i)
        # Edge: Catch number ending in dot at end of string
        if s[-2].isdigit() and s[-1] == ".":
            numeric_dots.append(len(s) - 1)
        numeric_dots = [-1] + numeric_dots + [len(s)]

        substrs = []
        for start, stop in zip(numeric_dots, numeric_dots[1:]):
            substrs.append(s[start + 1 : stop])
            substrs.append(self.DECIMAL_SPACER)
        substrs = substrs[:-1]
        return "".join(substrs)

    def _convert(self, filterstr):
        _conversion = (
            self._replace_numeric_dots(filterstr)  # temporarily sub numeric dots
            .replace(".", self.SPACER)  # Allow dotted fields
            .replace(self.DECIMAL_SPACER, ".")  # add them back
        )
        return "(" + _conversion + ")"

    def _unconvert(self, field_name):
        return field_name.replace(self.SPACER, ".")  # Allow dotted fields

    def python_to_mongo(self, filterstr):
        """Convert Python expresion to MongoDB filter.

        <!-- lazydoc-ignore: internal -->
        """
        try:
            tree = ast.parse(self._convert(filterstr), mode="eval")
        except SyntaxError as e:
            raise ValueError(
                "Invalid python comparison expression; form something like `my_col == 123`"
            ) from e

        multiple_filters = hasattr(tree.body, "op")

        if multiple_filters:
            op = self.AST_OPERATORS.get(type(tree.body.op))
            values = [self._handle_compare(v) for v in tree.body.values]
        else:
            op = "$and"
            values = [self._handle_compare(tree.body)]
        return {"$or": [{op: values}]}

    def front_to_back(self, name):
        """Convert frontend metric names to backend field names.

        <!-- lazydoc-ignore: internal -->
        """
        name, *rest = name.split(".")
        rest = "." + ".".join(rest) if rest else ""

        if name in self.FRONTEND_NAME_MAPPING:
            return self.FRONTEND_NAME_MAPPING[name]
        elif name in self.FRONTEND_NAME_MAPPING_REVERSED:
            return name
        elif name in self.run_set._runs_config:
            return f"config.{name}.value{rest}"
        else:  # assume summary metrics
            return f"summary_metrics.{name}{rest}"

    def back_to_front(self, name):
        """Convert backend field names to frontend metric names.

        <!-- lazydoc-ignore: internal -->
        """
        if name in self.FRONTEND_NAME_MAPPING_REVERSED:
            return self.FRONTEND_NAME_MAPPING_REVERSED[name]
        elif name in self.FRONTEND_NAME_MAPPING:
            return name
        elif (
            name.startswith("config.") and ".value" in name
        ):  # may be brittle: originally "endswith", but that doesn't work with nested keys...
            # strip is weird sometimes (??)
            return name.replace("config.", "").replace(".value", "")
        elif name.startswith("summary_metrics."):
            return name.replace("summary_metrics.", "")
        tracklab.termerror(f"Unknown token: {name}")
        return name

    # These are only used for ParallelCoordinatesPlot because it has weird backend names...
    def pc_front_to_back(self, name):
        """Convert ParallelCoordinatesPlot to backend field names.

        <!-- lazydoc-ignore: internal -->
        """
        name, *rest = name.split(".")
        rest = "." + ".".join(rest) if rest else ""
        if name is None:
            return None
        elif name in self.panel_metrics_helper.FRONTEND_NAME_MAPPING:
            return "summary:" + self.panel_metrics_helper.FRONTEND_NAME_MAPPING[name]
        elif name in self.FRONTEND_NAME_MAPPING:
            return self.FRONTEND_NAME_MAPPING[name]
        elif name in self.FRONTEND_NAME_MAPPING_REVERSED:
            return name
        elif name in self.run_set._runs_config:
            return f"config:{name}.value{rest}"
        else:  # assume summary metrics
            return f"summary:{name}{rest}"

    def pc_back_to_front(self, name):
        """Convert backend backend field names to ParallelCoordinatesPlot names.

        <!-- lazydoc-ignore: internal -->
        """
        if name is None:
            return None
        elif "summary:" in name:
            name = name.replace("summary:", "")
            return self.panel_metrics_helper.FRONTEND_NAME_MAPPING_REVERSED.get(
                name, name
            )
        elif name in self.FRONTEND_NAME_MAPPING_REVERSED:
            return self.FRONTEND_NAME_MAPPING_REVERSED[name]
        elif name in self.FRONTEND_NAME_MAPPING:
            return name
        elif name.startswith("config:") and ".value" in name:
            return name.replace("config:", "").replace(".value", "")
        elif name.startswith("summary_metrics."):
            return name.replace("summary_metrics.", "")
        return name


class PanelMetricsHelper:
    """Converts Python-style query expressions to MongoDB-style queries for W&B reports.

    <!-- lazydoc-ignore-class: internal -->
    """

    FRONTEND_NAME_MAPPING = {
        "Step": "_step",
        "Relative Time (Wall)": "_absolute_runtime",
        "Relative Time (Process)": "_runtime",
        "Wall Time": "_timestamp",
    }
    FRONTEND_NAME_MAPPING_REVERSED = {v: k for k, v in FRONTEND_NAME_MAPPING.items()}

    RUN_MAPPING = {"Created Timestamp": "createdAt", "Latest Timestamp": "heartbeatAt"}
    RUN_MAPPING_REVERSED = {v: k for k, v in RUN_MAPPING.items()}

    def front_to_back(self, name):
        """Convert frontend metric names to backend field names.

        <!-- lazydoc-ignore: internal -->
        """
        if name in self.FRONTEND_NAME_MAPPING:
            return self.FRONTEND_NAME_MAPPING[name]
        return name

    def back_to_front(self, name):
        """Convert backend field names to frontend metric names.

        <!-- lazydoc-ignore: internal -->
        """
        if name in self.FRONTEND_NAME_MAPPING_REVERSED:
            return self.FRONTEND_NAME_MAPPING_REVERSED[name]
        return name

    # ScatterPlot and ParallelCoords have weird conventions
    def special_front_to_back(self, name):
        """Convert frontend metric names to backend field names.

        <!-- lazydoc-ignore: internal -->
        """
        if name is None:
            return name

        name, *rest = name.split(".")
        rest = "." + ".".join(rest) if rest else ""

        # special case for config
        if name.startswith("c::"):
            name = name[3:]
            return f"config:{name}.value{rest}"

        # special case for summary
        if name.startswith("s::"):
            name = name[3:] + rest
            return f"summary:{name}"

        name = name + rest
        if name in self.RUN_MAPPING:
            return "run:" + self.RUN_MAPPING[name]
        if name in self.FRONTEND_NAME_MAPPING:
            return "summary:" + self.FRONTEND_NAME_MAPPING[name]
        if name == "Index":
            return name
        return "summary:" + name

    def special_back_to_front(self, name):
        """Convert backend field names to frontend metric names.

        <!-- lazydoc-ignore: internal -->
        """
        if name is not None:
            kind, rest = name.split(":", 1)

            if kind == "config":
                pieces = rest.split(".")
                if len(pieces) <= 1:
                    raise ValueError(f"Invalid name: {name}")
                elif len(pieces) == 2:
                    name = pieces[0]
                elif len(pieces) >= 3:
                    name = pieces[:1] + pieces[2:]
                    name = ".".join(name)
                return f"c::{name}"

            elif kind == "summary":
                name = rest
                return f"s::{name}"

        if name is None:
            return name
        elif "summary:" in name:
            name = name.replace("summary:", "")
            return self.FRONTEND_NAME_MAPPING_REVERSED.get(name, name)
        elif "run:" in name:
            name = name.replace("run:", "")
            return self.RUN_MAPPING_REVERSED[name]
        return name
