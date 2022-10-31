import statistics

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import Input, Output, State, callback, dash_table, dcc, html
from utils.classes import RubricItem
from utils.grading import marks_by_question, student_total_marks

dash.register_page(__name__)

QUESTION_COLUMNS = ["Question", "Total", "Lowest", "Mean", "Highest"]
OVERALL_COLUMNS = [
    "Lowest",
    "Median",
    "Mean",
    "Highest",
    "25th Percentile",
    "75th Percentile",
]


def default_table_style_options(n_columns):
    return {
        "css": [
            {
                "selector": "table",
                "rule": "table-layout: fixed",
            }
        ],
        "style_cell": {
            "width": f"{n_columns}%",
            "textOverflow": "ellipsis",
            "overflow": "hidden",
        },
        "style_header": {
            "backgroundColor": "white",
            "fontWeight": "bold",
        },
        "style_data_conditional": [
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgba(200, 200, 200, 0.5)",
            }
        ],
    }


def generate_statistics_table_children(id, title, columns):
    return [
        dmc.Title(
            title,
            order=2,
            align="left",
            style={"margin-bottom": "10px"},
        ),
        dash_table.DataTable(
            id=id,
            columns=[{"name": i, "id": i} for i in columns],
            **default_table_style_options(len(columns)),
        ),
    ]


layout = html.Div(
    [
        html.H1("Statistics"),
        dmc.Grid(
            [
                dmc.Col(
                    [
                        dmc.Title(
                            "Score Distribution",
                            order=2,
                            align="left",
                            style={
                                "margin-bottom": "10px",
                                "padding-left": "30px",
                            },
                        ),
                        dcc.Graph(id="grades-histogram"),
                    ],
                    span=12,
                ),
                dmc.Col(
                    dmc.Group(
                        generate_statistics_table_children(
                            "question-data-table",
                            "Question Statistics",
                            QUESTION_COLUMNS,
                        ),
                        direction="column",
                    ),
                    span=6,
                    style={"padding": "0px 40px"},
                ),
                dmc.Col(
                    dmc.Group(
                        generate_statistics_table_children(
                            "overall-data-table",
                            "Overall Statistics",
                            OVERALL_COLUMNS,
                        ),
                        direction="column",
                    ),
                    span=6,
                    style={"padding": "0px 40px"},
                ),
            ],
            justify="center",
            style={"padding": "0px 40px"},
        ),
    ],
)


@callback(
    Output("question-data-table", "data"),
    [
        Input("page-rubric-data", "data"),
        Input("page-grading-data", "data"),
        Input("_pages_location", "pathname"),
    ],
    # State("completed-data", "data"),
)
def update_question_statistics(
    rubric_data,
    grading_data,
    _path,
):
    if not rubric_data or not grading_data:
        return dash.no_update

    records = []
    # Populate question and total scores
    for pages in grading_data.values():
        # Student number not needed
        del pages["student_num"]

        for page in sorted(pages.values(), key=lambda x: int(x["question_num"])):
            if "question_num" not in page or "total_score" not in page:
                continue

            records.append(
                {"Question": page["question_num"], "Total": page["total_score"]}
            )

        # Just need grading data from first script -- assuming all the same
        break

    questions_marks = marks_by_question(rubric_data, grading_data)
    for question, marks in questions_marks.items():
        idx = int(question) - 1
        total_mark = sum(marks)
        stats = {
            "Total": total_mark,
            "Lowest": min(marks),
            "Mean": statistics.mean(marks),
            "Highest": max(marks),
        }

        records[idx] |= stats
    records.append({"Total": sum(int(r["Total"]) for r in records)})

    return records


@callback(
    Output("overall-data-table", "data"),
    [
        Input("page-rubric-data", "data"),
        Input("_pages_location", "pathname"),
    ],
    # State("completed-data", "data"),
)
def update_overall_statistics(rubric_data, _path):
    if not rubric_data:
        return dash.no_update

    all_marks = student_total_marks(rubric_data)

    if len(all_marks) > 1:
        quantiles = statistics.quantiles(all_marks, method="inclusive")
        q25, q75 = (
            quantiles[0],
            quantiles[2],
        )
    else:
        q25, q75 = all_marks[0], all_marks[0]

    return [
        {
            "Lowest": min(all_marks),
            "Median": statistics.median(all_marks),
            "Mean": statistics.mean(all_marks),
            "Highest": max(all_marks),
            "25th Percentile": q25,
            "75th Percentile": q75,
        }
    ]


@callback(
    Output("grades-histogram", "figure"),
    [
        Input("page-rubric-data", "data"),
        Input("page-grading-data", "data"),
        Input("_pages_location", "pathname"),
    ],
)
def update_histogram(rubric_data, grading_data, _path):
    if not rubric_data or not grading_data:
        return dash.no_update

    all_marks = student_total_marks(rubric_data)
    fig = px.histogram(
        all_marks,
        opacity=0.8,
        # This cuts off last value
        # range_x=[0, max(all_marks)],
        labels={"value": "Marks"},
        text_auto=True,
        nbins=len(set(all_marks)),
    )
    fig.update_layout(
        {
            "xaxis": {"tickmode": "linear", "tick0": 0, "dtick": 1},
            "yaxis": {"tickmode": "linear", "tick0": 0, "dtick": 1},
        },
        bargap=0.2,
        showlegend=False,
    )

    return fig
