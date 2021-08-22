import json
import math
import os
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
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
companies['Year founded'] = companies['Year founded'].replace('missing', '0').astype(int)
# Create data frame with the locations (lat, lng, states).
locations = pd.read_excel(os.path.join(dirname, '../assets/long-and-lat-by-state.xlsx'), dtype={'Fip': str})

"""
Prepare data frames that will be processed to be inserted into graphics and maps.
And set configuration data for insertion in the dashboard. 
"""
# Join the two files from above by using state code (e.g. TX - Dallas Texas)
companies_locations = pd.merge(companies, locations, how='left', left_on=['State'], right_on=['Code'])
# Mapbox requires that the fip code always have two digits then add leading zeros
companies_locations['Fip'] = companies_locations['Fip'].str.zfill(2)
# Color scale to be used on the map. Specifically in the grouping of employees by companies
color_scale = (
    ((0.0, '#000000'), (1.0, '#000000')),
    ((0.0, '#0D0D0D'), (1.0, '#0D0D0D')),
    ((0.0, '#383838'), (1.0, '#383838')),
    ((0.0, '#676767'), (1.0, '#676767')),
    ((0.0, '#9A9A9A'), (1.0, '#9A9A9A')),
    ((0.0, '#D0D0D0'), (1.0, '#D0D0D0')),
    ((0.0, '#FFFFFF'), (1.0, '#FFFFFF')),
)
color_scale_bubbles = ['#fa4032', '#e0bdbb', '#8cc0de', '#2c5c8a']
# Number of employees per company groups (e.g. 1-50 employees)
employees_per_company = (
    (1, 50),
    (51, 200),
    (201, 500),
    (501, 1000),
    (1001, 5000),
    (5001, 10000),
    (10001, math.inf)
)

"""
Create graphic object like maps and bar charts.
Add the graphic object data to the Figure.
The Figure will be inserted in the layout page.
"""


def calculate_bubble(state_companies, max_state_companies):
    """
    Calculate bubble size using the number of companies by state
    :param state_companies: Total companies by state
    :param max_state_companies: Max companies found in a state
    :return: Bubble size
    """
    bubble_size = state_companies / max_state_companies * 100 * 1.7

    if bubble_size < 10:
        return 10
    elif bubble_size > 40:
        return 40

    return bubble_size


def business_foundation_chart(employees_ranges, name_states, locality_names):
    """
    Create business foundation by year chart
    :param employees_ranges: Tuple with ranges or None for all (e.g. (1, 50))
    :param name_states: Iterable with the state or None for all.
    :param locality_names: Iterable with the localities or None for all.
    :return: Figure instance with the chart
    """
    top_5 = ['Retail', 'Food and beverages', 'Restaurants', 'Food production', 'Wholesale']
    # Filter by top 5 industries
    years = companies_locations[companies_locations['Industry'].isin(top_5)]

    # Filter by employees ranges
    if employees_ranges is not None:
        years = years[years['Current employee estimate'].between(employees_ranges[0], employees_ranges[1])]
    # Filter by name states
    if name_states is not None:
        years = years[years['Name_stateuniversity'].isin(name_states)]
    # Filter by locality
    if locality_names is not None:
        years = years[years['Locality'].isin(locality_names)]

    # Count companies in founded year groups
    years_groups = years.groupby(['Year founded', 'Industry'], as_index=False).size()
    # Group by founded year
    years = years.groupby(['Year founded', 'Industry'], as_index=False).mean()
    # Select between 2000 and 2018 years lapse
    years = years[years['Year founded'].between(2000, 2018)]
    years_groups = years_groups[years_groups['Year founded'].between(2000, 2018)]
    # Merge count groups and years
    business_foundation_data = years.merge(years_groups, how='inner', on='Year founded')

    # Before create charts, rename column for best reading
    business_foundation_data = business_foundation_data.rename(columns={'size': 'Companies', 'Industry_y': 'Industry'})

    # Create chart
    fig = px.line(
        business_foundation_data,
        x='Year founded',
        y='Companies',
        color='Industry',
        title='Business foundation by year (Top 5 industries)',
    )
    fig.update_traces(mode="markers+lines")

    return fig


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
    fip = companies_locations_f['Fip']
    # Extract states
    state = companies_locations_f['State_y']
    # Extract Current employee estimate
    employee_estimate = companies_locations_f['Current employee estimate']

    # Name format to be used on the gray scale
    gte = '+' if math.isinf(employees[1]) else '-{}'.format(employees[1])
    name = '''
        <i>{}{} Employees</i> <br>
        <b>{} Companies</b> <br>
    '''.format(employees[0], gte, len(companies_locations_f))

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

# AVG employees by state
avg_employees_states = companies_locations.groupby(['State_y'], as_index=False).mean().round(0)
# Count occurrences in the group process (number of companies)
avg_employees_states_count = companies_locations.groupby(['State_y'], as_index=False).size()
# Set the max companies by state
max_companies_state = avg_employees_states_count['size'].max()

# Add bubble indicators to the map
data.append(go.Scattermapbox(
    lat=avg_employees_states['Latitude'],
    lon=avg_employees_states['Longitud'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=avg_employees_states_count['size'].apply(
            lambda state_companies: calculate_bubble(state_companies, max_companies_state)),
        color=avg_employees_states['Current employee estimate'],
        colorscale=color_scale_bubbles,
        symbol='circle',
        showscale=True,
        colorbar=go.scattermapbox.marker.ColorBar(
            x=-0.1,
            title=go.scattermapbox.marker.colorbar.Title(
                text='Number of employees per company',
                side='right',
            ),
        ),
    ),
    name='',
    text='Name of state: <b>' + avg_employees_states['State_y'] + '</b><br>' +
         'Employees per company: <b>' + avg_employees_states['Current employee estimate'].astype(str) + '</b><br>' +
         'Number of companies: <b>' + avg_employees_states_count['size'].astype(str),
    showlegend=False,
))

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


def category_employees(current_employees):
    """
    Get category label by current employees amount
    :param current_employees: Number of current employees
    :return: e.g. 1-50, 1001-500, etc.
    """
    for employees_range in employees_per_company:
        if employees_range[0] <= current_employees <= employees_range[1]:
            lte = '+' if math.isinf(employees_range[1]) else '-{}'.format(employees_range[1])
            return '{}{}'.format(employees_range[0], lte)


def company_domain(company_name, domain):
    """
    Format company URL based on company name and bing search URL or simple return the domain
    :param company_name: The company name
    :param domain: The company URL
    :return:
    """
    if domain == 'missing':
        return 'https://www.bing.com/news/search?q={}&FORM=HDRSC6'.format(company_name)
    else:
        return 'https://{}'.format(domain)


def top_10_companies_tabs(industry):
    """
    Create the HTML structure (tabs) with the top 10 companies, based on the industry type
    :param industry: Industry type, can be all
    :return: HTML elements
    """
    filtered_companies = pd.DataFrame()
    tabs = []
    tabs_content = []

    # All industries
    if industry == 'all':
        filtered_companies = companies.nlargest(10, 'Current employee estimate')

    # Generate tabs and content
    for index, row in filtered_companies.iterrows():
        tabs.append(
            html.Li(className='tab', children=[
                html.A(
                    className='active' if index == 0 else '',
                    href='#{}'.format(row['Domain']),
                    children=row['Name'],
                )
            ])
        )

        tabs_content.append(
            html.Div(id=row['Domain'], className='col s12', children=[
                html.Ul(className='collection with-header', children=[
                    html.Li(className='collection-header', children=[
                        html.H4('{}, Founding in {}'.format(row['Name'], row['Year founded'])),
                    ]),
                    html.Li(
                        className='collection-item',
                        children='Located in {}'.format(row['Id_locality'])
                    ),
                    html.Li(
                        className='collection-item',
                        children='Linkedin: {}'.format(row['Linkedin url'])
                    ),
                    html.Li(
                        className='collection-item',
                        children='Sub-industry: {}'.format(row['Industry'])
                    ),
                    html.Li(
                        className='collection-item',
                        children='Category by current employees: {}'.format(
                            category_employees(row['Current employee estimate']))
                    ),
                    html.Li(
                        className='collection-item',
                        children='Current employees: {}'.format(row['Current employee estimate'])
                    ),
                    html.Iframe(
                        src=company_domain(row['Name'], row['Domain']),
                        **{'data-fallback': company_domain(row['Name'], 'missing')},
                        width='100%',
                        height='500px',
                    )
                ]),
            ])
        )

    return html.Div(className='row', children=[
        html.Div(className='col s12', children=[
            html.Ul(className='tabs', children=tabs)
        ]),
        html.Div(children=tabs_content),
    ])


# The food and beverages page
page = html.Div(className='row card', children=[
    html.Div(className='card-content', children=[
        html.Div(className='col s12', children=[
            html.Span(className='card-title', children='Food and beverages'),
        ]),
        html.Div(className='col s12', children=[
            # Insert map on the HTML page
            dcc.Graph(id="map", figure=map_figure),
        ]),
        html.Div(className='col s8', children=[
            html.P(
                className='descriptive-text',
                children=[
                    html.Span(
                        'The size of the circles indicates the number of companies in the state, the larger the '
                        'circle the more companies there are.'),
                    html.Br(),
                    html.Span(
                        'While the color indicates: in red a low number of employees and in dark green a high number '
                        'of employees per company.')
                ],
            ),
        ]),
        html.Div(className='col s4 center-align', children=[
            html.Button(
                id='top-companies',
                className='btn modal-trigger blue darken-4 waves-effect',
                **{'data-target': 'modal1'},
                children='Read more about Top 10 companies',
            ),
            html.Div(id='modal1', className='modal', children=[
                html.Div(className='modal-content', children=[
                    html.H4('Top 10 companies'),
                    html.Div(id='top-10-companies', children=top_10_companies_tabs('all')),
                ]),
            ]),
        ]),
        html.Div(className='col s9', children=[
            dcc.Graph(id='left-chart', figure=business_foundation_chart(None, None, None))
        ]),
    ]),
])
