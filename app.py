import dash

external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css',
    '/style.css'
]
external_scripts = [
    'https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js'
]

# Start the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    external_scripts=external_scripts,
    suppress_callback_exceptions=True,
)

server = app.server
