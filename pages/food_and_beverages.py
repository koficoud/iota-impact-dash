import json
import math
import os
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from urllib.request import urlopen
from app import app
from dash.dependencies import Output, Input

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
    (1, 50, '1-50'),
    (51, 200, '51-200'),
    (201, 500, '201-500'),
    (501, 1000, '501-1000'),
    (1001, 5000, '100-5000'),
    (5001, 10000, '5001-10000'),
    (10001, math.inf, '10001+')
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

    # Allow a maximum and minimum values
    if bubble_size < 10:
        return 10
    elif bubble_size > 40:
        return 40

    return bubble_size


def filter_employees_ranges(rows, employees_ranges):
    """
    Filter rows by employees range
    :param rows: Companies rows
    :param employees_ranges: Employees ranges
    :return:
    """
    if employees_ranges is not None:
        filtered = pd.DataFrame()

        for employee_range in employees_ranges:
            filtered = filtered.append(
                rows[rows['Current employee estimate'].between(employee_range[0], employee_range[1])])

        return filtered

    return rows


def filter_company_rows(rows, industries, employees_ranges, name_states, locality_names):
    """
    Filter companies by common params
    :param rows: Company rows
    :param industries: Iterable with industries or None for all
    :param employees_ranges: Iterable with employees or None for all
    :param name_states: Iterable with state names or None for all
    :param locality_names: Iterable with localities or None for all
    :return: Filtered rows dataframe
    """
    filtered = rows

    # Filter by industries
    if industries is not None:
        filtered = filtered[filtered['Industry'].isin(industries)]

    # Filter by employees ranges
    filtered = filter_employees_ranges(rows, employees_ranges)

    # Filter by name states
    if name_states is not None:
        filtered = filtered[filtered['Name_stateuniversity'].isin(name_states)]

    # Filter by locality name
    if locality_names is not None:
        filtered = filtered[filtered['Locality'].isin(locality_names)]

    return filtered


def business_foundation_chart(employees_ranges, name_states, locality_names):
    """
    Create business foundation by year chart (top 5)
    :param employees_ranges: Tuple with ranges or None for all (e.g. (1, 50))
    :param name_states: Iterable with the state or None for all.
    :param locality_names: Iterable with the localities or None for all.
    :return: Figure instance with the chart
    """
    top_5 = ['Retail', 'Food and beverages', 'Restaurants', 'Food production', 'Wholesale']
    # Filter by top 5 industries
    years = companies_locations[companies_locations['Industry'].isin(top_5)]

    # Filter by employees ranges
    years = filter_employees_ranges(years, employees_ranges)

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


def get_top10_biggest_companies(industries, employees_ranges, name_states, locality_names):
    """
    GEt top 10 for biggest companies
    :param industries: Iterable with industries or None for all
    :param employees_ranges: Iterable with employees or None for all
    :param name_states: Iterable with state names or None for all
    :param locality_names: Iterable with localities or None for all
    :return:
    """
    biggest_companies = companies_locations

    # Filter rows
    biggest_companies = filter_company_rows(biggest_companies, industries, employees_ranges, name_states, locality_names)
    # Sort by current employee estimate
    biggest_companies = biggest_companies.sort_values(by=['Current employee estimate'], ascending=False).head(10)

    return biggest_companies


def biggest_companies_chart(industries, employees_ranges, name_states, locality_names):
    """
    Create biggest companies chart (top 10)
    :param industries: Iterable with industries or None for all
    :param employees_ranges: Tuple with ranges or None for all (e.g. (1, 50))
    :param name_states: Iterable with the state or None for all
    :param locality_names: Iterable with the localities or None for all
    :return: Figure instance with the chart
    """
    # Fetch companies data
    biggest_companies = get_top10_biggest_companies(industries, employees_ranges, name_states, locality_names) \
        .sort_values(by=['Current employee estimate'], ascending=True)

    # Create chart
    fig = go.Figure(go.Bar(
        x=biggest_companies['Current employee estimate'],
        y=biggest_companies['Name'],
        orientation='h'))

    return fig


def companies_states_map(company_names, industries, employees_ranges, name_states, locality_names):
    """
    Create companies mapbox with the data computed
    :param company_names: Iterable with company names or None for all
    :param industries: Iterable with industries or None for all
    :param employees_ranges: Tuple with ranges or None for all (e.g. (1, 50))
    :param name_states: Iterable with the state or None for all
    :param locality_names: Iterable with the localities or None for all
    :return:
    """
    # Set companies with locations
    companies_states = companies_locations

    # Filter by company names
    if company_names is not None:
        companies_states = companies_states[companies_states['Name'].isin(company_names)]
    # Filter rows
    companies_states = filter_company_rows(companies_states, industries, employees_ranges, name_states, locality_names)

    # Graphic objects
    data = []
    # Iterator count
    i = 0
    for employees in employees_per_company:
        # Filter companies by employees (e.g. between 1 and 50)
        companies_locations_f = companies_states[
            companies_states['Current employee estimate'].between(employees[0], employees[1])
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
    avg_employees_states = companies_states.groupby(['State_y'], as_index=False).mean().round(0)
    # Count occurrences in the group process (number of companies)
    avg_employees_states_count = companies_states.groupby(['State_y'], as_index=False).size()
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

    return map_figure


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


def top_10_companies_tabs(industries, employees_ranges, name_states, locality_names):
    """
    Create the HTML structure (tabs) with the top 10 companies, based on the industry type
    :param industries: Iterable with industries or None for all
    :param employees_ranges: Tuple with ranges or None for all (e.g. (1, 50))
    :param name_states: Iterable with the state or None for all
    :param locality_names: Iterable with the localities or None for all
    :return: Modal data with tabs elements
    """
    filtered_companies = get_top10_biggest_companies(industries, employees_ranges, name_states, locality_names)
    tabs = []
    tabs_content = []

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
                        sandbox='allow-forms allow-scripts',
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


def company_names_options(search):
    """
    Perform a search in the companies and format to options dropdown
    Create a dropdown with company names data
    :param search: Search string
    :return:
    """
    options = []

    # Catch empty string
    if search == '':
        return options

    # Perform search
    if search is not None:
        # Second find by contains
        company_names = companies[companies['Name'].str.contains(search, na=False, case=False) == True].head(100)

        # Append companies to options dropdown
        for company_name in company_names['Name']:
            options.append({
                'label': str(company_name),
                'value': str(company_name),
            })

    return options


@app.callback(
    [
        Output('company_names_dropdown', 'options'),
        Output('company_names_dropdown', 'placeholder'),
    ],
    Input('company_name_input', 'value'))
def update_company_names_dropdown(company_name):
    """
    Listen input changes on company name input
    :param company_name: The name of company
    :return:
    """
    company_names = company_names_options(company_name)
    value = 'First perform a search'
    if len(company_names) > 0:
        value = '{} and {} more found...'.format(company_names[0]['value'], len(company_names))

    return company_names, value


def industries_dropdown():
    """
    Create a dropdown element with industry options
    :return: Dropdown
    """
    # Sort by industries
    industries = companies.sort_values(by='Industry')
    # Extract unique values
    industries = industries['Industry'].unique()
    options = []

    # Append industries to options dropdown
    for industry in industries:
        options.append({
            'label': str(industry),
            'value': str(industry),
        })

    return dcc.Dropdown(
        options=options,
        id='industries_dropdown',
        placeholder='Industries',
        multi=True,
    )


def range_employees_dropdown():
    """
    Create a dropdown element with range employees options
    :return: Dropdown
    """
    options = []

    # Append ranges top options dropdown
    for employees_range in employees_per_company:
        options.append({
            'label': employees_range[2],
            'value': employees_range[2],
        })

    return dcc.Dropdown(
        options=options,
        id='range_employees_dropdown',
        placeholder='Number of employees',
        multi=True,
    )


def states_dropdown():
    """
    Create a dropdown element with state options
    :return: Dropdown
    """
    # Group by state
    state_names = companies_locations.groupby(['Name_stateuniversity'], as_index=False).mean()
    # Sort by state name
    state_names = state_names.sort_values(by='Name_stateuniversity')
    options = []

    # Append states to options dropdown
    for state_name in state_names['Name_stateuniversity']:
        options.append({
            'label': str(state_name),
            'value': str(state_name),
        })

    return dcc.Dropdown(
        options=options,
        id='states_dropdown',
        placeholder='States',
        multi=True,
    )


def localities_dropdown():
    """
    Create a dropdown element with localities options
    :return: Dropdown
    """
    # Group by state
    locality_names = companies.groupby(['Locality'], as_index=False).mean()
    # Sort by state name
    locality_names = locality_names.sort_values(by='Locality')
    options = []

    # Append states to options dropdown
    for locality_name in locality_names['Locality']:
        options.append({
            'label': str(locality_name),
            'value': str(locality_name),
        })

    return dcc.Dropdown(
        options=options,
        id='localities_dropdown',
        placeholder='Localities',
        multi=True,
    )


@app.callback(
    [
        Output('left-chart', 'figure'),
        Output('right-chart', 'figure'),
        Output('map', 'figure'),
        Output('top-10-companies', 'children'),
        Output('modal-title', 'children'),
    ],
    [
        Input('company_names_dropdown', 'value'),
        Input('industries_dropdown', 'value'),
        Input('range_employees_dropdown', 'value'),
        Input('states_dropdown', 'value'),
        Input('localities_dropdown', 'value'),
    ]
)
def update_graphs(company_names, industries, range_employees, state_names, localities):
    ranges_values = {
        '1-50': (1, 50),
        '51-200': (51, 200),
        '201-500': (201, 500),
        '501-1000': (501, 1000),
        '100-5000': (1001, 5000),
        '5001-10000': (5001, 10000),
        '10001+': (10001, math.inf),
    }

    # Prevent empty lists
    if company_names is not None and len(company_names) == 0:
        company_names = None
    if industries is not None and len(industries) == 0:
        industries = None
    if state_names is not None and len(state_names) == 0:
        state_names = None
    if localities is not None and len(localities) == 0:
        localities = None

    # Set employees ranges
    employees_ranges = []
    if range_employees is None or len(range_employees) == 0:
        employees_ranges = None
    else:
        for ranges in range_employees:
            employees_ranges.append(ranges_values[ranges])

    # Format modal title for tabs
    industries_label = 'All'
    if industries is not None:
        industries_label = ', '.join(industries)

    modal_title = 'Top 10 companies {}'.format(industries_label)

    return \
        business_foundation_chart(employees_ranges, state_names, localities), \
        biggest_companies_chart(industries, employees_ranges, state_names, localities), \
        companies_states_map(company_names, industries, employees_ranges, state_names, localities), \
        top_10_companies_tabs(industries, employees_ranges, state_names, localities), \
        modal_title


# The food and beverages page
page = html.Div(className='row card', children=[
    html.Div(className='card-content', children=[
        html.Div(className='col s12', children=[
            html.Span(className='card-title', children='Food and beverages'),
        ]),
        # Select element to filtering data
        html.Div(className='row', children=[
            html.Div(className='col s12', children=[
                dcc.Input(
                    id='company_name_input',
                    type='text',
                    placeholder='Search by name of the company',
                    autoComplete='off',
                ),
                dcc.Dropdown(
                    options=[],
                    id='company_names_dropdown',
                    placeholder='Company name results...',
                    multi=True,
                ),
            ]),
        ]),
        html.Div(className='row', children=[
            html.Div(className='col s3', children=[
                industries_dropdown(),
            ]),
            html.Div(className='col s3', children=[
                range_employees_dropdown(),
            ]),
            html.Div(className='col s3', children=[
                states_dropdown(),
            ]),
            html.Div(className='col s3', children=[
                localities_dropdown(),
            ]),
        ]),
        html.Div(className='col s12', children=[
            # Insert map on the HTML page
            dcc.Graph(id='map', figure=companies_states_map(None, None, None, None, None)),
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
                    html.H4(id='modal-title', children='Top 10 companies All'),
                    html.Div(id='top-10-companies', children=top_10_companies_tabs(None, None, None, None)),
                ]),
            ]),
        ]),
        html.Div(className='col s8', children=[
            dcc.Graph(id='left-chart', figure=business_foundation_chart(None, None, None))
        ]),
        html.Div(className='col s4', children=[
            dcc.Graph(id='right-chart', figure=biggest_companies_chart(None, None, None, None))
        ]),
    ]),
])
