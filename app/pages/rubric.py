import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback, html

dash.register_page(__name__, name="Add Rubric", path="/rubric")

layout = html.Div(
    [
        dmc.Title("Add Grading Scheme", order=1, style={"margin": "24px"}),
        dmc.Group(
            [
                html.Div(
                    [
                        dmc.NumberInput(
                            id="number-questions-input",
                            label="Number of questions",
                            value=1,
                            min=1,
                            size="lg",
                            step=1,
                            style={"margin-bottom": "16px", "width": 250},
                        ),
                        dmc.NumberInput(
                            id="overall-score-input",
                            label="Total score",
                            description="Total score for the assignment",
                            value=10,
                            min=1,
                            size="lg",
                            step=5,
                            style={"width": 250},
                        ),
                    ],
                    style={
                        "background-color": "rgba(230, 244, 255, 0.5)",
                        "border-radius": "10px",
                        "padding": "16px 0px 16px 24px",
                        "margin": "24px",
                        "height": "300px",
                        "width": "400px",
                    },
                ),
                html.Div(
                    [
                        dmc.Select(
                            label="Question Number",
                            id="question-select",
                            value="1",
                            data=[{"value": "1", "label": "1"}],
                            maxDropdownHeight=200,
                            size="lg",
                            style={"margin-bottom": "16px", "width": 250},
                        ),
                        dmc.NumberInput(
                            label="Question Score",
                            description="Total marks for this question",
                            id="question-score-input",
                            value=1,
                            min=1,
                            size="lg",
                            step=1,
                            style={"width": 250},
                        ),
                    ],
                    className="add-rubric-section",
                    style={
                        "background-color": "rgb(246, 246, 246)",
                        "border-radius": "10px",
                        "margin": "24px",
                        "padding": "16px 0px 16px 24px",
                        "height": "300px",
                        "width": "500px",
                    },
                ),
            ]
        ),
    ]
)


@callback(Output("question-select", "data"), Input("number-questions-input", "value"))
def update_number_of_questions(n_questions):
    return [{"value": str(i), "label": str(i)} for i in range(1, n_questions + 1)]


@callback(
    Output("question-score-input", "value"),
    Input("question-select", "value"),
    State("rubric-scheme-data", "data"),
)
def update_question_score(question_num, rubric_scheme_data):
    question_num = str(question_num)
    if not rubric_scheme_data or question_num not in rubric_scheme_data["questions"]:
        return 1

    return rubric_scheme_data["questions"][question_num]


@callback(
    [
        Output("rubric-scheme-data", "data"),
        Output("question-score-input", "error"),
    ],
    [
        Input("number-questions-input", "value"),
        Input("question-select", "value"),
        Input("question-score-input", "value"),
        Input("overall-score-input", "value"),
    ],
    State("rubric-scheme-data", "data"),
)
def update_rubric_scheme(
    n_questions, question_num, score, overall_score, rubric_scheme_data
):
    if not rubric_scheme_data:
        rubric_scheme_data = {}

    if not question_num and not score and not overall_score:
        return dash.no_update

    question_num = str(question_num)

    if overall_score:
        rubric_scheme_data["total"] = int(overall_score)

    if n_questions:
        questions = rubric_scheme_data.setdefault("questions", {})
        for i in range(1, n_questions + 1):
            i = str(i)
            if i not in questions:
                questions[i] = 1

    if question_num and score:
        questions = rubric_scheme_data.setdefault("questions", {})
        total_marks = (
            sum(i for qns, i in questions.items() if qns != question_num) + score
        )

        if "total" in rubric_scheme_data and total_marks > rubric_scheme_data["total"]:
            return (
                dash.no_update,
                "Sum of question scores exceeds total assignment score",
            )

        questions[question_num] = score

    return rubric_scheme_data, ""
