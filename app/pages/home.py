import base64
import itertools
import re
import tempfile
from datetime import datetime
from operator import attrgetter, itemgetter
from typing import Iterable

import dash
import dash_mantine_components as dmc
import plotly.express as px
from backend.api import gglapi_parse, num_highlighter
from dash import ALL, MATCH, Input, Output, State, callback, ctx, dcc, html
from dash_iconify import DashIconify
from pdf2image import convert_from_bytes, pdfinfo_from_bytes
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.platypus.doctemplate import inch
from reportlab.rl_config import defaultPageSize
from utils.classes import RubricItem
from utils.grading import marks_by_question

dash.register_page(__name__, path="/")

STUDENT_NUM_REGEX = ".*([a-zA-Z][0-9]{7}[a-zA-Z]).*"

GRADING_SUBMIT_MODAL_DEFAULT_CHILDREN = [
    dmc.Space(h=20),
    dmc.Group(
        children=[
            dmc.Button("Submit", id="grading-modal-submit-btn"),
            dmc.Button(
                "Close",
                color="red",
                variant="outline",
                id="grading-modal-close-btn",
            ),
        ],
        position="right",
    ),
]

RUBRIC_MATCH_MODAL_DEFAULT_CHILDREN = [
    dmc.Group(
        [
            dmc.Button(
                "Apply to all questions",
                color="blue",
                variant="outline",
                id="rubric-match-modal-all-qns-btn",
            ),
            dmc.Button(
                "Apply to current question only",
                color="blue",
                variant="outline",
                id="rubric-match-modal-current-qns-btn",
            ),
            dmc.Button(
                "Apply current edit only",
                color="blue",
                variant="filled",
                id="rubric-match-modal-current-btn",
            ),
        ],
        position="right",
    ),
]


layout = html.Div(
    children=[
        dmc.Alert(
            id="top-alert",
            title="Error occurred!",
            color="red",
            duration=5000,
            hide=True,
            style={"margin-top": "16px"},
        ),
        dmc.Group(
            children=[
                dcc.Loading(
                    dcc.Upload(
                        className="upload-button",
                        id="upload-section",
                        children=html.Div(["Drag and Drop or ", html.A("Select PDF")]),
                        style={
                            "width": "1000px",
                            "height": "60px",
                            "lineHeight": "60px",
                            "borderWidth": "1px",
                            "borderStyle": "dashed",
                            "borderRadius": "5px",
                            "textAlign": "center",
                            "margin": "10px",
                        },
                        multiple=True,
                    ),
                    fullscreen=True,
                ),
                dmc.TextInput(
                    id="student-number-input",
                    label="Student Number",
                    placeholder="e.g. A0000000X",
                    radius="md",
                    required=True,
                    size="xl",
                    style={
                        "margin": "16px",
                        "width": "300px",
                    },
                ),
                html.Div(
                    [
                        dmc.Button(
                            "Export grading to PDF",
                            id="export-grading-pdf-btn",
                            variant="light",
                            style={"height": "60px", "margin-top": "31px"},
                        ),
                        dcc.Download(id="grading-pdf-download"),
                    ]
                ),
            ],
        ),
        html.Hr(),
        dmc.Grid(
            children=[
                dmc.Col(
                    children=[
                        dmc.Navbar(
                            children=[
                                dmc.ScrollArea(
                                    id="files-scrollarea",
                                    offsetScrollbars=True,
                                    type="hover",
                                    scrollbarSize=10,
                                )
                            ],
                            id="files-navbar",
                            fixed=True,
                            height="100vh",
                            width={"base": 300},
                        )
                    ],
                    span=3,
                ),
                # COLUMN 2
                dmc.Col(
                    html.Div(
                        children=[
                            dmc.Group(
                                [
                                    html.Div(
                                        [
                                            html.H2(id="annotate-name"),
                                            html.H2(id="annotate-datetime"),
                                        ],
                                    ),
                                    dmc.LoadingOverlay(
                                        html.Div(
                                            dmc.Select(
                                                label="Type of parser",
                                                id="parser-select",
                                                disabled=True,
                                                value="0",
                                                data=[
                                                    {
                                                        "value": "0",
                                                        "label": "No parser",
                                                    },
                                                    {
                                                        "value": "1",
                                                        "label": "Google Solver",
                                                    },
                                                    {
                                                        "value": "2",
                                                        "label": "Number Highlighter",
                                                    },
                                                ],
                                                size="md",
                                                style={
                                                    "margin-left": "16px",
                                                    "width": 200,
                                                },
                                            ),
                                            id="loading-parser",
                                        ),
                                        loaderProps={
                                            "variant": "dots",
                                            "color": "blue",
                                            "size": "xl",
                                        },
                                    ),
                                ],
                            ),
                            dmc.LoadingOverlay(
                                dcc.Graph(
                                    id="annotate-active",
                                    config={
                                        "modeBarButtonsToAdd": [
                                            "drawopenpath",
                                            "drawrect",
                                            "eraseshape",
                                        ]
                                    },
                                    figure={
                                        "layout": {
                                            "template": None,
                                            "xaxis": {
                                                "showgrid": False,
                                                "showticklabels": False,
                                                "zeroline": False,
                                            },
                                            "yaxis": {
                                                "showgrid": False,
                                                "showticklabels": False,
                                                "zeroline": False,
                                            },
                                        }
                                    },
                                    style={"width": "100%", "height": "100%"},
                                ),
                                loaderProps={
                                    "variant": "dots",
                                    "color": "blue",
                                    "size": "xl",
                                },
                                style={"width": "100%", "height": "100%"},
                            ),
                            dmc.Col(
                                dmc.Group(
                                    children=[
                                        dmc.Group(
                                            children=[
                                                dmc.Button(
                                                    "Previous",
                                                    id="prev-button",
                                                    variant="outline",
                                                ),
                                                dmc.Button("Next", id="next-button"),
                                            ]
                                        ),
                                        dmc.Button(
                                            "Submit final grading",
                                            id="submit-grading-btn",
                                            color="green",
                                        ),
                                    ],
                                    position="apart",
                                ),
                            ),
                        ],
                        id="annotate-section",
                        style={"width": "100%", "height": "150vh"},
                    ),
                    span=17,
                ),
                # COLUMN 3
                dmc.Col(
                    dmc.Navbar(
                        id="grading-navbar",
                        children=[
                            dmc.Group(
                                children=[
                                    dmc.Text(
                                        "Question number: ",
                                        size="xl",
                                        weight=800,
                                    ),
                                    dmc.TextInput(
                                        id="page-question-number",
                                        placeholder="Enter question number",
                                        type="number",
                                        required=True,
                                    ),
                                ],
                                direction="column",
                                position="apart",
                                style={"padding": "8px 0px 8px 0px"},
                            ),
                            dmc.Group(
                                children=[
                                    dmc.Text(
                                        "Total score:",
                                        size="xl",
                                        weight=800,
                                    ),
                                    dmc.Group(
                                        children=[
                                            dmc.Text(
                                                "0",
                                                id="page-current-score",
                                                size="xl",
                                                weight=800,
                                                underline=True,
                                            ),
                                            dmc.Text("of", size="xl", weight=800),
                                            dmc.TextInput(
                                                id="page-max-score",
                                                placeholder="Enter max score",
                                                type="number",
                                                required=True,
                                                style={"width": 160},
                                            ),
                                        ],
                                        noWrap=True,
                                    ),
                                ],
                                direction="column",
                                position="apart",
                                style={"padding": "8px 0px 8px 0px"},
                            ),
                            dmc.Stack(
                                id="rubric-items-list",
                                style={"padding": "8px 0px 8px 0px"},
                            ),
                            dmc.Group(
                                id="add-rubric-input",
                                children=[
                                    dmc.TextInput(
                                        id="add-rubric-marks",
                                        label="Enter marks",
                                        placeholder="e.g. (-) 1",
                                        type="number",
                                        required=True,
                                    ),
                                    dmc.TextInput(
                                        id="add-rubric-description",
                                        label="Enter rubric description",
                                        placeholder="e.g. wrong sign used",
                                        required=True,
                                    ),
                                    dmc.Button(
                                        "Add rubric item",
                                        id="add-rubric-button",
                                        variant="light",
                                    ),
                                ],
                                direction="column",
                                position="apart",
                                style={"padding": "0px 0px 16px 0px"},
                            ),
                        ],
                        style={
                            "background-color": "rgb(246, 246 ,246)",
                            "border-radius": "10px",
                            "margin-right": "16px",
                            "padding": "16px 0px 0px 24px",
                        },
                        fixed=True,
                        position={"right": 0},
                        width={"base": 450},
                    ),
                    span=4,
                ),
            ],
            gutter="xl",
            justify="space-between",
            style={"width": "100%"},
            columns=24,
        ),
        dmc.Modal(
            title="Confirm grading submission",
            id="grading-submit-modal",
            children=GRADING_SUBMIT_MODAL_DEFAULT_CHILDREN,
            centered=True,
            closeOnClickOutside=True,
            closeOnEscape=True,
        ),
        dmc.Modal(
            title="Matching rubric items found",
            id="rubric-match-modal",
            children=RUBRIC_MATCH_MODAL_DEFAULT_CHILDREN,
            centered=True,
            overflow="inside",
            padding="md",
            size="lg",
        ),
    ]
)


def annotate_figure_default_layout() -> dict:
    return {
        "dragmode": "drawrect",
        "hovermode": False,
        "newshape": {"line": {"color": "red"}},
        "xaxis": {"showticklabels": False},
        "yaxis": {"showticklabels": False},
    }


def rubric_item_component(marks, desc, item_idx):
    marks_positive = int(marks) >= 0

    return html.Div(
        children=[
            dmc.Group(
                children=[
                    dmc.Title(
                        "+" + marks if marks_positive else marks,
                        order=3,
                        style={
                            "color": "rgb(27, 127, 124)"
                            if marks_positive
                            else "rgb(192, 33, 33)"
                        },
                        id={"type": "rubric-marks", "index": item_idx},
                    ),
                    dmc.Group(
                        children=[
                            dmc.ActionIcon(
                                DashIconify(icon="bytesize:edit", width=20),
                                class_name="rubric-edit-button",
                                id={"type": "rubric-edit", "index": item_idx},
                                radius="sm",
                                variant="hover",
                            ),
                            dmc.ActionIcon(
                                DashIconify(
                                    icon="entypo:squared-cross",
                                    width=20,
                                ),
                                class_name="rubric-delete-button",
                                id={
                                    "type": "rubric-delete",
                                    "index": item_idx,
                                },
                                radius="sm",
                                variant="hover",
                            ),
                        ],
                        align="flex-end",
                        position="right",
                        spacing="xs",
                    ),
                ],
                position="apart",
            ),
            dmc.Text(
                desc,
                id={"type": "rubric-desc", "index": item_idx},
            ),
        ],
        id={"type": "rubric-item", "index": item_idx},
        style={"margin": "0px 0px 16px 8px"},
    )


def render_page_fig(pages, page_idx, parser):
    img = convert_from_bytes(
        # Page indexes in PDF form start from 1
        pages,
        first_page=page_idx + 1,
        last_page=page_idx + 1,
    )[0]

    if int(parser) == 1:
        img = gglapi_parse(img, True)
    elif int(parser) == 2:
        img = num_highlighter(img)

    fig = px.imshow(img)
    fig.update_layout(annotate_figure_default_layout())

    return fig


def get_file_render_info(files, file_idx, page_idx=0, parser=0):
    file_idx = str(file_idx)
    name, upload_datetime, contents = itemgetter("name", "date", "contents")(
        files[file_idx]
    )
    decoded = base64.b64decode(contents)
    fig = render_page_fig(decoded, page_idx, parser)

    return f"Name: {name}", f"Uploaded on {upload_datetime}", fig


def process_pdf_upload(file_contents, names, dates):
    uploaded = {}
    if file_contents and names and dates:
        for idx, (contents, name, date) in enumerate(zip(file_contents, names, dates)):
            idx = str(idx)
            _, content_string = contents.split(",")

            uploaded[idx] = {}
            uploaded[idx]["name"] = name
            uploaded[idx]["contents"] = content_string
            uploaded[idx]["date"] = datetime.fromtimestamp(date).strftime(
                "%Y-%m-%d %H:%I:%S"
            )

    return uploaded


@callback(
    Output("parser-select", "disabled"),
    [Input("upload-store", "data"), Input("_pages_location", "pathname")],
)
def enable_parser_select(files, path):
    if path == dash.page_registry["pages.home"]["path"] and files:
        return False

    return dash.no_update


@callback(
    Output("upload-store", "data"),
    Input("upload-section", "contents"),
    [
        State("upload-section", "filename"),
        State("upload-section", "last_modified"),
    ],
    prevent_initial_call=True,
)
def upload_files(contents, names, dates):
    if contents and names and dates:
        return process_pdf_upload(contents, names, dates)

    return dash.no_update


@callback(
    [
        Output("annotate-name", "children"),
        Output("annotate-datetime", "children"),
        Output("annotate-active", "figure"),
        Output("loading-parser", "children"),
    ],
    [
        Input("upload-store", "data"),
        Input("page-index", "data"),
        Input("file-index", "data"),
        Input("parser-select", "value"),
    ],
    [
        State("upload-store", "data"),
        State("parser-select", "value"),
    ],
    prevent_initial_call=True,
)
def render_file(initial, page_idx, file_idx, parser_change, files, parser_current):
    if ctx.triggered_id == "upload-store" and initial:
        # File gets uploaded initially -- render first of uploaded files
        return *get_file_render_info(initial, 0), dash.no_update
    elif ctx.triggered_id == "page-index" and page_idx is not None and files:
        # Page changes
        return (
            *get_file_render_info(files, file_idx, page_idx, parser=parser_current),
            dash.no_update,
        )
    elif ctx.triggered_id == "file-index" and file_idx is not None and files:
        # File changes
        return (
            *get_file_render_info(files, file_idx, parser=parser_current),
            dash.no_update,
        )
    elif ctx.triggered_id == "parser-select":
        return (
            *get_file_render_info(files, file_idx, page_idx or 0, parser_change),
            dash.no_update,
        )

    return dash.no_update


@callback(
    Output("page-index", "data"),
    [
        Input("prev-button", "n_clicks"),
        Input("next-button", "n_clicks"),
        Input("file-index", "data"),
    ],
    [
        State("page-index", "data"),
        State("file-index", "data"),
        State("upload-store", "data"),
    ],
    prevent_initial_call=True,
)
def change_page_index(
    _prev_btn_clicks,
    _next_btn_clicks,
    _file_idx_changed,
    current_page_idx,
    current_file_idx,
    files,
):
    # Initial load
    if current_page_idx is None:
        return 0

    # Change files -- reset to first page
    if ctx.triggered_id == "file-index":
        return 0

    if current_file_idx is None:
        return dash.no_update

    # TODO: this is super slow, shouldn't have to decode everytime?
    current_page_idx = int(current_page_idx)
    current_file_idx = str(current_file_idx)

    pages = base64.b64decode(files[current_file_idx]["contents"])
    max_pages = pdfinfo_from_bytes(pages)["Pages"]

    # Check if page index will be out of range with this button trigger
    # If so, no updates needed to be performed
    if (ctx.triggered_id == "prev-button" and current_page_idx - 1 < 0) or (
        ctx.triggered_id == "next-button" and current_page_idx + 1 >= max_pages
    ):
        return dash.no_update

    new_page_idx = (
        current_page_idx - 1
        if ctx.triggered_id == "prev-button"
        else current_page_idx + 1
    )

    return new_page_idx


@callback(
    Output("file-index", "data"),
    Input({"type": "file-link", "index": ALL}, "n_clicks"),
    State("upload-store", "data"),
    prevent_initial_call=True,
)
def change_file_index(_clicks, files):
    if not ctx.triggered_id:
        return dash.no_update

    new_file_idx = str(ctx.triggered_id.index)

    if new_file_idx not in files:
        return dash.no_update

    return new_file_idx


@callback(
    Output("files-scrollarea", "children"),
    [
        Input("upload-store", "data"),
        Input("completed-data", "data"),
        Input("_pages_location", "pathname"),
    ],
)
def update_navbar(files_data, completed_data, path):
    if path != dash.page_registry["pages.home"]["path"]:
        return dash.no_update

    if not files_data:
        return dash.no_update

    file_links = []
    for idx, file in enumerate(files_data.values()):
        link = html.A(
            file["name"],
            className="navbar-link",
            id={"type": "file-link", "index": idx},
            style={"color": "blue"},
        )

        if completed_data and str(idx) in completed_data:
            link = dmc.Group(
                children=[
                    link,
                    dmc.ThemeIcon(
                        DashIconify(icon="ic:round-check-box", width=16),
                        color="green",
                        variant="filled",
                        class_name="completed-btn",
                        size=20,
                    ),
                ],
                position="apart",
            )

        file_links.append(link)

    children = [
        dmc.Group(
            children=file_links,
            grow=True,
            position="left",
            spacing="sm",
            direction="column",
            style={
                "margin-bottom": 20,
                "margin-top": 20,
                "padding-left": 30,
                "padding-right": 20,
            },
        )
    ]

    return children


@callback(
    [
        Output("page-rubric-data", "data"),
        Output("add-rubric-marks", "value"),
        Output("add-rubric-description", "value"),
        Output("add-rubric-marks", "error"),
        Output("add-rubric-description", "error"),
        Output("page-question-number", "error"),
        Output("page-max-score", "error"),
    ],
    [
        Input("add-rubric-button", "n_clicks"),
        Input({"type": "rubric-delete", "index": ALL}, "n_clicks"),
        Input("rubric-item-edit-final-data", "data"),
    ],
    [
        State("add-rubric-marks", "value"),
        State("add-rubric-description", "value"),
        State("page-rubric-data", "data"),
        State("page-index", "data"),
        State("file-index", "data"),
        State("page-question-number", "value"),
        State("page-max-score", "value"),
    ],
    prevent_initial_call=True,
)
def update_rubric_items(
    add_n_clicks,
    delete_n_clicks,
    edit_data,
    marks,
    description,
    rubric_data,
    page_idx,
    file_idx,
    question_num,
    total_score,
):
    if ctx.triggered_id == "add-rubric-button" and add_n_clicks:
        marks_err, description_err, question_num_err, total_score_err = (
            "",
            "",
            "",
            "",
        )

        if not marks:
            marks_err = "Marks cannot be 0"

        if not description:
            description_err = "Rubric description cannot be empty"

        if not question_num:
            question_num_err = "Question number required"

        if not total_score:
            total_score_err = "Total score required"

        if any((marks_err, description_err, question_num_err, total_score_err)):
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                marks_err,
                description_err,
                question_num_err,
                total_score_err,
            )

        return (
            add_rubric_item(
                rubric_data, page_idx, file_idx, add_n_clicks, marks, description
            ),
            "",
            "",
            "",
            "",
            "",
            "",
        )
    elif (
        isinstance(ctx.triggered_id, dict) and ctx.triggered_id.type == "rubric-delete"
    ):
        # NOTE: workaround to prevent accidental deletion of rubric items when changing
        # pages
        # This happens when changing pages and the Dash components representing the
        # rubric items are re-introduced into the layout
        # This triggers "rubric-delete" again, which we don't want
        # See https://dash.plotly.com/advanced-callbacks#when-dash-components-are-added-to-the-layout
        # for this caveat
        if not delete_n_clicks or (
            isinstance(delete_n_clicks, Iterable) and not any(delete_n_clicks)
        ):
            return dash.no_update

        return (
            delete_rubric_item(rubric_data, page_idx, file_idx, ctx.triggered_id.index),
            dash.no_update,
            dash.no_update,
            "",
            "",
            "",
            "",
        )
    elif ctx.triggered_id == "rubric-item-edit-final-data":
        if not edit_data or (isinstance(edit_data, Iterable) and not any(edit_data)):
            return dash.no_update

        for edit in edit_data["new"]:
            new_rubric_item = RubricItem.from_dict(edit)
            for item in rubric_data[str(new_rubric_item.file_idx)][
                str(new_rubric_item.page_idx)
            ]:
                if item["item_idx"] == new_rubric_item.item_idx:
                    item["marks"] = new_rubric_item.marks
                    item["description"] = new_rubric_item.description
                    break

        return (
            rubric_data,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )
    else:
        return dash.no_update


@callback(
    Output({"type": "rubric-item", "index": MATCH}, "children"),
    Input({"type": "rubric-edit", "index": MATCH}, "n_clicks"),
    [
        State({"type": "rubric-marks", "index": MATCH}, "children"),
        State({"type": "rubric-desc", "index": MATCH}, "children"),
    ],
    prevent_initial_call=True,
)
def edit_rubric_item(edit_n_clicks, rubric_marks, rubric_desc):
    if not edit_n_clicks or (
        isinstance(edit_n_clicks, Iterable) and not any(edit_n_clicks)
    ):
        return dash.no_update

    item_idx = ctx.triggered_id.index
    children = [
        dmc.Group(
            children=[
                dmc.TextInput(
                    value=rubric_marks.strip("+"),
                    placeholder=rubric_marks.strip("+"),
                    style={"width": 60, "margin": "0px 0px 5px"},
                    type="number",
                    id={"type": "rubric-marks-edit", "index": item_idx},
                ),
                dmc.ActionIcon(
                    DashIconify(icon="bi:check-square", width=20),
                    class_name="rubric-edit-done-button",
                    id={"type": "rubric-edit-done", "index": item_idx},
                    radius="sm",
                    variant="hover",
                ),
            ],
            position="apart",
        ),
        dmc.TextInput(
            value=rubric_desc,
            # Store original value in placeholder
            placeholder=rubric_desc,
            style={"width": 200},
            id={"type": "rubric-desc-edit", "index": item_idx},
        ),
        # rubric-item-edit-data is an intermediate store for processing
        # matched rubric items, if any, based on the edited rubric data.
        # rubric-item-edit-final-data will be the final store that contains
        # all the updates we want to apply.
        # TODO: Slightly hacky/confusing, but for now used to implement the
        # indirection due to the modal popup when matched rubric items found
        dcc.Store(id={"type": "rubric-item-edit-data", "index": item_idx}),
    ]

    return children


@callback(
    Output({"type": "rubric-item-edit-data", "index": MATCH}, "data"),
    Input({"type": "rubric-edit-done", "index": MATCH}, "n_clicks"),
    [
        State({"type": "rubric-marks-edit", "index": MATCH}, "value"),
        State({"type": "rubric-marks-edit", "index": MATCH}, "placeholder"),
        State({"type": "rubric-desc-edit", "index": MATCH}, "value"),
        State({"type": "rubric-desc-edit", "index": MATCH}, "placeholder"),
        State("page-rubric-data", "data"),
        State("file-index", "data"),
        State("page-index", "data"),
    ],
    prevent_initial_call=True,
)
def finish_edit_rubric_item(
    done_n_clicks,
    rubric_marks_edited,
    rubric_marks_original,
    rubric_desc_edited,
    rubric_desc_original,
    rubric_data,
    file_idx,
    page_idx,
):
    if not done_n_clicks or (
        isinstance(done_n_clicks, Iterable) and not any(done_n_clicks)
    ):
        return dash.no_update

    edits = {
        "new": [
            RubricItem(
                rubric_marks_edited,
                rubric_desc_edited,
                ctx.triggered_id.index,
                file_idx,
                page_idx,
            )
        ]
    }

    if (
        rubric_marks_edited == rubric_marks_original
        and rubric_desc_edited == rubric_desc_original
    ):
        return edits

    file_idx = str(file_idx)
    page_idx = str(page_idx)
    # Find matching rubric items across all files and pages
    matched_rubric_items = []
    for f_idx, pages in rubric_data.items():
        for p_idx, rubric_items in pages.items():
            for item in rubric_items:
                item = RubricItem.from_dict(item)
                # We stored the original value of the edited description in the
                # placeholder in `edit_rubric_item`
                if (
                    item.description == rubric_desc_original
                    and item.marks == rubric_marks_original
                    and not (str(f_idx) == file_idx and str(p_idx) == page_idx)
                ):
                    matched_rubric_items.append(item)

    if not matched_rubric_items:
        return edits

    edits["original_marks"] = rubric_marks_original
    edits["matched_rubric_items"] = matched_rubric_items

    return edits


@callback(
    [
        Output("rubric-match-modal", "children"),
        Output("rubric-match-modal", "opened"),
        Output("rubric-item-edit-final-data", "data"),
    ],
    [
        Input("rubric-match-modal-all-qns-btn", "n_clicks"),
        Input("rubric-match-modal-current-qns-btn", "n_clicks"),
        Input("rubric-match-modal-current-btn", "n_clicks"),
        Input({"type": "rubric-item-edit-data", "index": ALL}, "data"),
    ],
    [State("page-grading-data", "data")],
    prevent_initial_call=True,
)
def handle_matching_rubric_items_modal(
    all_btn, current_qns_btn, current_btn, edit_data, grading_data
):
    # Property of pattern matching callback: since we match on ALL indexes,
    # Dash automatically assumes that we have more than one trigger source
    # and converts our data to a list.
    # The invariant we maintain is that we can only perform one edit process
    # at a time (i.e. the whole finish edit -> check for matching rubric items
    # -> finalize edits flow), hence can just take first element of this list
    if edit_data:
        edit_data = edit_data[0]

    # No matching items found -- no need to open modal
    if not edit_data or (edit_data and "matched_rubric_items" not in edit_data):
        return dash.no_update, False, edit_data

    if ctx.triggered_id == "rubric-match-modal-current-btn" and current_btn:
        return dash.no_update, False, edit_data
    elif ctx.triggered_id == "rubric-match-modal-all-qns-btn" and all_btn:
        new_marks = edit_data["new"][0]["marks"]

        for item in edit_data["matched_rubric_items"]:
            rubric_item = RubricItem.from_dict(item)
            edit_data["new"].append(
                RubricItem(
                    new_marks,
                    *attrgetter("description", "item_idx", "file_idx", "page_idx")(
                        rubric_item
                    ),
                )
            )

        return dash.no_update, False, edit_data
    elif ctx.triggered_id == "rubric-match-modal-current-qns-btn" and current_qns_btn:
        new_marks = edit_data["new"][0]["marks"]
        current_question_num = grading_data[str(edit_data["new"][0]["file_idx"])][
            str(edit_data["new"][0]["page_idx"])
        ]["question_num"]

        for item in edit_data["matched_rubric_items"]:
            rubric_item = RubricItem.from_dict(item)
            if (
                grading_data[str(rubric_item.file_idx)][str(rubric_item.page_idx)][
                    "question_num"
                ]
                != current_question_num
            ):
                continue

            edit_data["new"].append(
                RubricItem(
                    new_marks,
                    *attrgetter("description", "item_idx", "file_idx", "page_idx")(
                        rubric_item
                    ),
                )
            )

        return dash.no_update, False, edit_data

    return (
        generate_rubric_match_modal_children(edit_data, grading_data),
        True,
        dash.no_update,
    )


@callback(
    Output("rubric-items-list", "children"),
    [
        Input("page-rubric-data", "data"),
        Input("page-index", "data"),
        Input("file-index", "data"),
    ],
    prevent_initial_call=True,
)
def render_rubric_items(rubric_data, page_idx, file_idx):
    # Note: dcc.Store data are JSON-serialized, and Python converts integer
    # keys to strings
    # To avoid surprises, just using string keys throughout
    page_idx = str(page_idx)
    file_idx = str(file_idx)

    items = []
    if rubric_data and file_idx in rubric_data and page_idx in rubric_data[file_idx]:
        for item in rubric_data[file_idx][page_idx]:
            item = RubricItem.from_dict(item)
            items.append(
                rubric_item_component(item.marks, item.description, item.item_idx)
            )

    return items


@callback(
    [Output("page-current-score", "children"), Output("page-current-score", "color")],
    [Input("rubric-items-list", "children")],
    prevent_initial_call=True,
)
def update_current_score(rubric_items):
    scores = [
        int(
            item["props"]["children"][0]["props"]["children"][0]["props"][
                "children"
            ].strip("+")
        )
        for item in rubric_items
    ]
    score = sum(scores)

    return score, "dark" if score >= 0 else "red"


@callback(
    [
        Output("page-question-number", "value"),
        Output("page-max-score", "value"),
    ],
    [
        Input("page-index", "data"),
        Input("file-index", "data"),
    ],
    State("page-grading-data", "data"),
)
def render_grading_fields(page_idx, file_idx, grading_data):
    if not grading_data or file_idx is None or page_idx is None:
        return dash.no_update

    file_idx = str(file_idx)
    page_idx = str(page_idx)
    if file_idx not in grading_data or page_idx not in grading_data[file_idx]:
        return "", ""

    return (
        grading_data[file_idx][page_idx]["question_num"] or "",
        grading_data[file_idx][page_idx]["total_score"] or "",
    )


@callback(
    Output("page-grading-data", "data"),
    [
        Input("student-number-input", "value"),
        Input("page-question-number", "value"),
        Input("page-max-score", "value"),
        Input("upload-store", "data"),
    ],
    [
        State("page-grading-data", "data"),
        State("page-index", "data"),
        State("file-index", "data"),
    ],
    prevent_initial_call=True,
)
def update_grading_data(
    student_num, question_num, total_score, files, grading_data, page_idx, file_idx
):
    # Perform one-time population of student number, if can be extracted from
    # uploaded filenames
    if ctx.triggered_id == "upload-store":
        data = {}

        for file_idx, file in files.items():
            sn_match = re.search(STUDENT_NUM_REGEX, file["name"])
            if sn_match:
                data[file_idx] = {}
                data[file_idx]["student_num"] = sn_match.group(1).upper()

        return data

    if not any((student_num, question_num, total_score)):
        return dash.no_update

    file_idx = str(file_idx)
    page_idx = str(page_idx)

    if grading_data:
        if file_idx in grading_data:
            grading_data[file_idx]["student_num"] = student_num

            if page_idx in grading_data[file_idx]:
                grading_data[file_idx][page_idx]["question_num"] = question_num
                grading_data[file_idx][page_idx]["total_score"] = total_score
            else:
                grading_data[file_idx][page_idx] = {
                    "question_num": question_num,
                    "total_score": total_score,
                }
        else:
            grading_data |= {
                file_idx: {
                    "student_num": student_num,
                    page_idx: {
                        "question_num": question_num,
                        "total_score": total_score,
                    },
                }
            }
    else:
        grading_data = {
            file_idx: {
                "student_num": student_num,
                page_idx: {"question_num": question_num, "total_score": total_score},
            }
        }

    return grading_data


@callback(
    [
        Output("student-number-input", "error"),
        Output("student-number-input", "value"),
        Output("grading-submit-modal", "children"),
        Output("grading-submit-modal", "opened"),
        Output("completed-data", "data"),
    ],
    [
        Input("submit-grading-btn", "n_clicks"),
        Input("grading-modal-submit-btn", "n_clicks"),
        Input("grading-modal-close-btn", "n_clicks"),
        Input("file-index", "data"),
    ],
    [
        State("upload-store", "data"),
        State("student-number-input", "value"),
        State("page-grading-data", "data"),
        State("completed-data", "data"),
    ],
    prevent_initial_call=True,
)
def modify_grading_fields(
    submit_btn_clicks,
    _modal_submit_btn,
    _modal_close_btn,
    file_idx,
    files,
    student_num,
    grading_data,
    completed_data,
):
    # TODO: cleanup input/output arguments
    if ctx.triggered_id == "grading-modal-submit-btn":
        return (
            "",
            student_num,
            GRADING_SUBMIT_MODAL_DEFAULT_CHILDREN,
            False,
            mark_file_as_completed(completed_data, file_idx),
        )
    elif ctx.triggered_id == "grading-modal-close-btn":
        return (
            "",
            student_num,
            GRADING_SUBMIT_MODAL_DEFAULT_CHILDREN,
            False,
            dash.no_update,
        )
    elif ctx.triggered_id == "file-index":
        return (
            "",
            retrieve_file_student_num(grading_data, file_idx),
            dash.no_update,
            False,
            dash.no_update,
        )
    elif ctx.triggered_id == "upload-store":
        # Process first population of student number for first file
        for file_idx, file in files.items():
            sn_match = re.search(STUDENT_NUM_REGEX, file["name"])
            return (
                "",
                sn_match.group(1).upper() if sn_match else dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )
    # TODO: add case to populate fields when coming from page change
    elif ctx.triggered_id == "submit-grading-btn" and submit_btn_clicks:
        # "Submit final grading" flow after button click
        if not student_num:
            return (
                "Student number required",
                dash.no_update,
                dash.no_update,
                False,
                dash.no_update,
            )

        children = [
            dmc.Text(f"Confirm submission for student {student_num}?")
        ] + GRADING_SUBMIT_MODAL_DEFAULT_CHILDREN

        return (
            "",
            student_num,
            children,
            True,
            dash.no_update,
        )

    return dash.no_update


@callback(
    [
        Output("grading-pdf-download", "data"),
        Output("top-alert", "hide"),
        Output("top-alert", "children"),
    ],
    Input("export-grading-pdf-btn", "n_clicks"),
    [
        State("page-grading-data", "data"),
        State("page-rubric-data", "data"),
        State("file-index", "data"),
        State("page-index", "data"),
    ],
    prevent_initial_call=True,
)
def export_grading_to_pdf(
    export_btn_clicks, grading_data, rubric_data, file_idx, page_idx
):
    file_idx = str(file_idx)
    page_idx = str(page_idx)

    err = (
        not grading_data
        or (file_idx is not None and file_idx not in grading_data)
        or (page_idx is not None and page_idx not in grading_data[file_idx])
    ) or (
        not rubric_data
        or (file_idx is not None and file_idx not in rubric_data)
        or (page_idx is not None and page_idx not in rubric_data[file_idx])
    )

    if err:
        return (
            dash.no_update,
            False,
            "No grading data found, upload a file or start grading first.",
        )

    if not export_btn_clicks:
        return dash.no_update

    # Compute score breakdown
    student_num = grading_data[file_idx]["student_num"]
    questions_marks = marks_by_question(rubric_data, grading_data, student_num)

    def _main_page(canvas, doc):
        PAGE_WIDTH, PAGE_HEIGHT = defaultPageSize[0:2]

        canvas.saveState()
        canvas.setFont("Times-Bold", 16)
        canvas.drawCentredString(
            PAGE_WIDTH / 2.0, PAGE_HEIGHT - 2.0 * inch, "Grade Report"
        )
        canvas.setFont("Times-Roman", 14)
        if student_num:
            canvas.drawCentredString(
                PAGE_WIDTH / 2.0, PAGE_HEIGHT - 2.4 * inch, student_num
            )
        canvas.restoreState()

    with tempfile.NamedTemporaryFile() as f:
        doc = SimpleDocTemplate(f)
        flowables = [Spacer(1, 2 * inch)]
        stylesheet = getSampleStyleSheet()
        style = stylesheet["Normal"]
        heading = stylesheet["Heading3"]
        flowables.append(
            Paragraph(
                f"Total marks: {sum(itertools.chain.from_iterable(questions_marks.values()))}",
                heading,
            )
        )
        flowables.append(Spacer(1, 0.1 * inch))
        flowables.append(Paragraph("Breakdown:", heading))
        flowables.append(Spacer(1, 0.05 * inch))

        for question, marks in questions_marks.items():
            list_items = [
                Paragraph(f"Question {question}: {sum(marks)}", style),
            ]

            comments = [Paragraph("Comments:", style)]
            comments_sub = []
            for page_idx, rubric_items in rubric_data[file_idx].items():
                page = int(page_idx) + 1
                if page != question:
                    continue

                comments_sub.append(
                    f"Page {page}: {', '.join(item['description'] for item in rubric_items)}"
                )

            comments.append(
                ListFlowable(
                    [ListItem(Paragraph(c, style)) for c in comments_sub],
                    bulletFontSize=5,
                    bulletType="bullet",
                    leftIndent=9,
                    start="square",
                )
            )

            list_items.append(comments)
            flowables.append(
                ListFlowable(list_items, bulletType="bullet", leftIndent=9)
            )
            flowables.append(Spacer(1, 0.1 * inch))

        doc.build(flowables, onFirstPage=_main_page)

        # `seek` necessary else PDF will be blank
        # Since we are in the same context manager and the canvas functions
        # above probably advance the IO cursor, need to seek to
        # start so that `send_file` reads bytes from the beginning
        f.seek(0)
        return (
            dcc.send_file(f.name, f"{student_num}.pdf" if student_num else "grade.pdf"),
            dash.no_update,
            dash.no_update,
        )


def add_rubric_item(rubric_data, page_idx, file_idx, item_idx, marks, description):
    new_item = RubricItem(
        marks.strip(), description.strip(), item_idx, file_idx, page_idx
    )

    # Note: dcc.Store data are JSON-serialized, and Python converts integer
    # keys to strings
    # To avoid surprises, just using string keys throughout
    file_idx = str(file_idx)
    page_idx = str(page_idx)
    if rubric_data:
        if file_idx in rubric_data:
            if page_idx in rubric_data[file_idx]:
                rubric_data[file_idx][page_idx].append(new_item)
            else:
                rubric_data[file_idx][page_idx] = [new_item]
        else:
            rubric_data |= {file_idx: {page_idx: [new_item]}}
    else:
        rubric_data = {file_idx: {page_idx: [new_item]}}

    return rubric_data


def delete_rubric_item(rubric_data, page_idx, file_idx, item_idx):
    # Note: dcc.Store data are JSON-serialized, and Python converts integer
    # keys to strings
    # To avoid surprises, just using string keys throughout
    file_idx = str(file_idx)
    page_idx = str(page_idx)
    rubric_data[file_idx][page_idx] = [
        item
        for item in rubric_data[file_idx][page_idx]
        if RubricItem.from_dict(item).item_idx != item_idx
    ]

    return rubric_data


def retrieve_file_student_num(grading_data, file_idx):
    # Note: dcc.Store data are JSON-serialized, and Python # converts integer
    # keys to strings
    # To avoid surprises, just using string keys throughout
    file_idx = str(file_idx)

    if not grading_data or file_idx not in grading_data:
        return ""

    return (
        grading_data[file_idx]["student_num"]
        if "student_num" in grading_data[file_idx]
        else ""
    )


def mark_file_as_completed(completed_data, file_idx):
    file_idx = str(file_idx)
    if completed_data:
        completed_data[file_idx] = 1
    else:
        completed_data = {file_idx: 1}

    return completed_data


def generate_rubric_match_modal_children(edit_data, grading_data):
    rubric_desc = edit_data["new"][0]["description"]
    rubric_old_marks = edit_data["original_marks"]
    rubric_new_marks = edit_data["new"][0]["marks"]
    edit_student_num = grading_data[str(edit_data["new"][0]["file_idx"])]["student_num"]
    edit_question_num = grading_data[str(edit_data["new"][0]["file_idx"])][
        str(edit_data["new"][0]["page_idx"])
    ]["question_num"]

    list_items = []
    for item in edit_data["matched_rubric_items"]:
        rubric_item = RubricItem.from_dict(item)
        student_num = grading_data[str(rubric_item.file_idx)]["student_num"]
        question_num = grading_data[str(rubric_item.file_idx)][
            str(rubric_item.page_idx)
        ]["question_num"]

        list_items.append((student_num, question_num))

    children = (
        [
            dmc.Text(
                "There are matching rubric items found in other scripts. Apply edits to them as well?"
            ),
            dmc.Space(h=20),
            dcc.Markdown(
                f"""
                Changing rubric item **'{rubric_desc}'** marks from **{rubric_old_marks}** to **{rubric_new_marks}**:
                - Student {edit_student_num}, Question {edit_question_num} **(current edit)**
                """,
                id="current-edit-md",
            ),
            dcc.Markdown(
                "\n".join(
                    f"- Student {student_num}, Question {question_num}"
                    for student_num, question_num in list_items
                ),
                style={"margin-top": "0px"},
            ),
            dmc.Space(h=10),
            dcc.Markdown(
                f"""
                Options:
                - **Apply to all questions**: This change will be applied across all scripts for matching criteria across all questions.
                - **Apply to current question only**: This change will be applied across all scripts, only for Question {edit_question_num}
                - **Apply current edit only**: This change will only be applied for the current script, only for Question {edit_question_num}
                """
            ),
            dmc.Space(h=20),
        ]
        + RUBRIC_MATCH_MODAL_DEFAULT_CHILDREN
    )

    return children
