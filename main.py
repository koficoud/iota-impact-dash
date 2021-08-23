import dash
import dash_core_components as dcc
import dash_html_components as html
import pages
from app import app, server

# Main wrapper
app.layout = html.Div(className='container', children=[
    # URL bar
    dcc.Location(id='url', refresh=False),
    # Navigation page
    html.Nav(className='blue darken-4', children=[
        html.Div(className='nav-wrapper', children=[
            dcc.Link(className='brand-logo', href='/', children=[
                html.Img(
                    style={'margin': '9px', 'width': '160px'},
                    src='https://iotaimpact.com/wp-content/uploads/2020/10/logo-1.png'),
            ]),
            html.Ul(className='right', children=[
                html.Li(id='home', children=[
                    dcc.Link('Home', href='/'),
                ]),
                html.Li(id='food-and-beverages', children=[
                    dcc.Link('Food and beverages', href='/food-and-beverages'),
                ]),
            ]),
        ]),
    ]),
    # Content container
    html.Div(id='page-content')
])


@app.callback(
    [
        dash.dependencies.Output('home', 'className'),
        dash.dependencies.Output('food-and-beverages', 'className')
    ],
    [dash.dependencies.Input('url', 'pathname')]
)
def add_active_class(pathname: object) -> object:
    """
    Add active class to the <li> element that has active href
    :param pathname: current path name
    :return: class names
    """
    home = ''
    food_and_beverages = ''

    if pathname == '/':
        home = 'active'
    if pathname == '/food-and-beverages':
        food_and_beverages = 'active'

    return home, food_and_beverages


# Update current page
@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/food-and-beverages':
        return pages.food_and_beverages.page
    if pathname == '/':
        return pages.index.page


# Star app running
if __name__ == '__main__':
    app.run_server(debug=True)
