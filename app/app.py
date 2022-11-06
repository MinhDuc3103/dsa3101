import dash
import dash_bootstrap_components as dbc
from backend.api import setup_env
from dash import Dash, dcc, html

external_stylesheets = ["https://rsms.me/inter/inter.css", dbc.themes.BOOTSTRAP]


app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    use_pages=True,
    suppress_callback_exceptions=True,
)

nav = html.Div(
    [
        dbc.Nav(
            [
                dbc.NavItem(
                    dbc.NavLink(
                        f"{page['name']}",
                        href=page["relative_path"],
                        active="exact",
                    )
                )
                for page in dash.page_registry.values()
            ],
            pills=True,
            style={"margin": "10px"},
        )
    ]
)


app.layout = html.Div(
    [
        nav,
        dash.page_container,
        # Stores uploaded data as a base64-encoded binary string
        dcc.Store(id="upload-store"),
        dcc.Store(id="file-index"),
        dcc.Store(id="page-index"),
        # Store rubric data per page (assuming that one page = one question)
        dcc.Store(id="page-rubric-data"),
        # Store question/score data per page
        dcc.Store(id="student-num-file-data"),
        # Set of IDs for files that have been marked as completed
        dcc.Store(id="completed-data"),
        dcc.Store(id="rubric-item-edit-final-data"),
        dcc.Store(id="rubric-scheme-data"),
    ]
)


if __name__ == "__main__":
    setup_env()
    app.run(host="0.0.0.0", port=3000, debug=True)
