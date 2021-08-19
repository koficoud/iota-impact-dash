import dash
import dash_core_components as dcc
import dash_html_components as html

page = html.Div([
    # Page title
    html.H1('Food and beverages'),
    html.Br(),
    # The page content
    html.Div(id='food-and-beverages-content')
])
