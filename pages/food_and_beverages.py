import json
import os
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
from urllib.request import urlopen

"""
Get the initial files to extract the data.
The data will be used in the dashboard.
"""
dirname = os.path.dirname(__file__)
# Fetch and set US states geojson.
with urlopen(
        'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json') as response:
    states = json.load(response)
# Create data frame with the companies
companies = pd.read_excel(os.path.join(dirname, '../assets/food-and-beverage.xlsx'))
# Create data frame with the locations (lat, lng, states).
locations = pd.read_excel(os.path.join(dirname, '../assets/long-and-lat-by-state.xlsx'), dtype={'Fip': str})

"""
Prepare data frames that will be processed to be inserted into graphics and maps.
And set configuration data for insertion in the dashboard. 
"""
# Join the two files from above by using state code (e.g. TX - Dallas Texas)
companies_locations = pd.merge(companies, locations, how='inner', left_on=['State'], right_on=['Code'])
# Mapbox requires that the fip code always have two digits then add leading zeros
companies_locations['Fip'] = companies_locations['Fip'].str.zfill(2)
# Color scale to be used on the map. Specifically in the grouping of employees by companies
color_scale = (((0.0, '#6b6b6b'), (1.0, '#6b6b6b')), ((0.0, '#989898'), (1.0, '#989898')),
               ((0.0, '#c4c4c4'), (1.0, '#c4c4c4')), ((0.0, '#f1f1f1'), (1.0, '#f1f1f1')))
# Number of employees per company groups (e.g. 1-50 employees)
employees_per_company = ((1, 50), (51, 200), (201, 500), (1001, 5000))

"""
Create graphic object like maps and bar charts.
Add the graphic object data to the Figure.
The Figure will be inserted in the layout page.
"""
# Graphic objects
data = []
# Iterator count
i = 0
for employees in employees_per_company:
    # Filter companies by employees (e.g. between 1 and 50)
    companies_locations_f = companies_locations[
        companies_locations['Current employee estimate'].between(employees[0], employees[1])
    ]

    # Extract fip codes
    fip = companies_locations_f[companies_locations_f['Fip'].notna()]['Fip']
    # Extract states
    state = companies_locations_f[companies_locations_f['Fip'].notna()]['State_y']
    # Extract Current employee estimate
    employee_estimate = companies_locations_f[companies_locations_f['Fip'].notna()]['Current employee estimate']

    # Name format to be used on the gray scale
    name = '''
        <i>{}-{} Employees</i> <br>
        <b>{} Companies</b> <br>
    '''.format(employees[0], employees[1], len(companies_locations_f))

    # Create grey scale values grouping by employees range
    data.append(go.Choroplethmapbox(
        geojson=states,
        locations=fip,
        z=employee_estimate,
        showlegend=True,
        name=name,
        colorscale=color_scale[i],
        showscale=False,
        hovertemplate=state,
    ))

    # Update iterator count
    i = i + 1

# Create figure element
map_figure = go.Figure(data)
# Update Mapbox settings
map_figure.update_layout(
    mapbox_style='carto-positron',
    mapbox_zoom=3,
    height=600,
    mapbox_center={'lat': 37.0902, 'lon': -95.7129},
    margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
)

"""
The layout page.
All the information tha will be rendered on the browser
"""
page = html.Div(className='row', children=[
    html.Div(className='col s12 card', children=[
        html.Div(className='card-content', children=[
            html.Span(className='card-title', children='Food and beverages'),
            # Insert map on the HTML page
            dcc.Graph(id="map", figure=map_figure),
        ]),
    ]),
])
