import dash
import json
import os
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
from urllib.request import urlopen


dirname = os.path.dirname(__file__)

# Fetch JSON states
with urlopen(
        'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json') as response:
    states = json.load(response)

# Fetch companies
companies = pd.read_excel(os.path.join(dirname, '../assets/food-and-beverage.xlsx'))
# Fetch locations
locations = pd.read_excel(os.path.join(dirname, '../assets/long-and-lat-by-state.xlsx'), dtype={'Fip': str})
# Join files by state code
companies_locations = pd.merge(companies, locations, how='inner', left_on=['State'],
                               right_on=['Code'])
# Add leading zeros to Fip
companies_locations['Fip'] = companies_locations['Fip'].str.zfill(2)
# Color scale
color_scale = (
    ((0.0, '#6b6b6b'), (1.0, '#6b6b6b')),
    ((0.0, '#989898'), (1.0, '#989898')),
    ((0.0, '#c4c4c4'), (1.0, '#c4c4c4')),
    ((0.0, '#f1f1f1'), (1.0, '#f1f1f1')),
)
# Number of employees per company groups
employees_per_company = (
    (1, 50),
    (51, 200),
    (201, 500),
    (1001, 5000),
)

# Add data to the map
data = []
i = 0  # Iterator count
for employees in employees_per_company:
    # Filter companies by employees
    companies_locations_f = companies_locations[
        companies_locations['Current employee estimate'].between(employees[0], employees[1])
    ]
    # Extract fip codes
    fip = companies_locations_f[companies_locations_f['Fip'].notna()]['Fip']
    # Extract state
    state = companies_locations_f[companies_locations_f['Fip'].notna()]['State_y']
    # Extract Current employee estimate
    employee_estimate = companies_locations_f[companies_locations_f['Fip'].notna()]['Current employee estimate']

    # Name format
    name = '''
        <i>{}-{} Employees</i> <br>
        <b>{} Companies</b> <br>
    '''.format(employees[0], employees[1], len(companies_locations_f))

    data.append(
        go.Choroplethmapbox(
            geojson=states,
            locations=fip,
            z=employee_estimate,
            showlegend=True,
            name=name,
            colorscale=color_scale[i],
            showscale=False,
            hovertemplate=state,
        )
    )

    i = i + 1  # Update iterator count

fig = go.Figure(data)

# Update Mapbox settings
fig.update_layout(
    mapbox_style='carto-positron',
    mapbox_zoom=3,
    height=600,
    mapbox_center={'lat': 37.0902, 'lon': -95.7129},
)
# Remove margin from Mapbox
fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})

# Layout page.
page = html.Div(className='row', children=[
    html.Div(className='col s12 card', children=[
        html.Div(className='card-content', children=[
            html.Span(className='card-title', children='Food and beverages'),
            dcc.Graph(id="map", figure=fig),
        ]),
    ]),
])
