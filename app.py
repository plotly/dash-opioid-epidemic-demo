# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_colorscales
import pandas as pd
import cufflinks as cf
import numpy as np
import feather

app = dash.Dash(__name__)
server = app.server

df_lat_lon = pd.read_csv('lat_lon_counties.csv')
df_lat_lon['FIPS '] = df_lat_lon['FIPS '].apply(lambda x: str(x).zfill(5))

df_full_data = pd.read_csv('age_adjusted_death_rate.csv')
df_full_data['"County Code"'] = df_full_data['"County Code"'].apply(lambda x: str(x).zfill(5))

#df_full_data = feather.read_dataframe('df.feather')

YEARS = [2003, 2004, 2005, 2006, 2007, \
		2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015]

BINS = ['0-2', '2.1-4', '4.1-6', '6.1-8', '8.1-10', '10.1-12', '12.1-14', \
		'14.1-16', '16.1-18', '18.1-20', '20.1-22', '22.1-24',  '24.1-26', \
		'26.1-28', '28.1-30', '>30']

DEFAULT_COLORSCALE = ["#2a4858", "#265465", "#1e6172", "#106e7c", "#007b84", \
	"#00898a", "#00968e", "#19a390", "#31b08f", "#4abd8c", "#64c988", \
	"#80d482", "#9cdf7c", "#bae976", "#d9f271", "#fafa6e"]

#DEFAULT_COLORSCALE = reversed(DEFAULT_COLORSCALE)

mapbox_access_token = "pk.eyJ1IjoiamFja3AiLCJhIjoidGpzN0lXVSJ9.7YK6eRwUNFwd3ODZff6JvA"

'''
~~~~~~~~~~~~~~~~
~~ APP LAYOUT ~~
~~~~~~~~~~~~~~~~
'''

app.layout = html.Div(children=[

	html.Div([
		html.H2(children='Age-Adjusted Rate of Poison-Induced Deaths'),
		html.P('Drag the slider to change the year. Click-drag on the map to select a group of counties'),
	]),

	html.Div([
		dcc.Slider(
			id='years-slider',
			min=min(YEARS),
			max=max(YEARS),
			value=min(YEARS),
			marks={str(year): str(year) for year in YEARS},
		),
	], style={'width':800, 'margin':20}),

	html.Div([
		dash_colorscales.DashColorscales(
			id='colorscale-picker',
			colorscale=DEFAULT_COLORSCALE,
			nSwatches=16,
			fixSwatches=True
		)
	]),

	dcc.Graph(
		id = 'county-choropleth',
		figure = dict(
			data=dict(
				lat = df_lat_lon['Latitude '],
				lon = df_lat_lon['Longitude'],
				text = df_lat_lon['Hover'],
				type = 'scattermapbox'
			)
		)
	),

	dcc.Graph(
		id = 'selected-data',
		figure = dict()
	),

	html.Div([
		html.P('† Deaths are classified using the International Classification of Diseases, \
			Tenth Revision (ICD–10). Drug-poisoning deaths are defined as having ICD–10 underlying \
			cause-of-death codes X40–X44 (unintentional), X60–X64 (suicide), X85 (homicide), or Y10–Y14 \
			(undetermined intent).'
		)
	])
])

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

@app.callback(
		dash.dependencies.Output('county-choropleth', 'figure'),
		[dash.dependencies.Input('years-slider', 'value'),
		dash.dependencies.Input('colorscale-picker', 'colorscale')])
def display_map(year, colorscale):

	cm = dict(zip(BINS, colorscale))

	data = [dict(
		lat = df_lat_lon['Latitude '],
		lon = df_lat_lon['Longitude'],
		text = df_lat_lon['Hover'],
		type = 'scattermapbox',
		#selected = dict(marker = dict(opacity=1)),
		#unselected = dict(marker = dict(opacity = 0)),
		marker = dict(size=5, color='white', opacity=1)
	)]

	annotations = [dict(
		showarrow = False,
		align = 'right',
		text = '<b>Age-adjusted death rate<br>per county per year</b>',
		x = 0.95,
		y = 0.95,
	)]

	for i, bin in enumerate(reversed(BINS)):
		color = cm[bin]
		annotations.append(
			dict(
				arrowcolor = color,
				text = bin,
				x = 0.95,
				y = 0.85-(i/20),
				ax = -60,
				ay = 0,
				arrowwidth = 5,
				arrowhead = 0
			)
		)

	layout = dict(
		mapbox = dict(
			layers = [],
			accesstoken = mapbox_access_token,
			style = 'light',
			center=dict(
				lat=38.72490,
				lon=-95.61446,
			),
			pitch=0,
			zoom=3.2,
		),
		hovermode = 'closest',
		margin = dict(r=0, l=0, t=0, b=0),
		annotations = annotations,
		dragmode = 'lasso'
	)

	base_url = 'https://raw.githubusercontent.com/jackparmer/mapbox-counties/master/'
	for bin in BINS:
		geo_layer = dict(
			sourcetype = 'geojson',
			source = base_url + str(year) + '/' + bin + '.geojson',
			type = 'fill',
			color = cm[bin],
			opacity = 0.8
		)
		layout['mapbox']['layers'].append(geo_layer)

	fig = dict(data=data, layout=layout)
	return fig

@app.callback(
	dash.dependencies.Output('selected-data', 'figure'),
	[dash.dependencies.Input('county-choropleth', 'selectedData')])
def display_selected_data(selectedData):
	print('FIRE SELECTION')
	if selectedData is None:
		print('SelectedData is None')
		return {}
	pts = selectedData['points']
	fips = [str(pt['text'].split('<br>')[-1]) for pt in pts]
	for i in range(len(fips)):
		if len(fips[i]) == 4:
			fips[i] = '0' + fips[i]
	print('FIPS', '\n', fips)
	dff = df_full_data[df_full_data['"County Code"'].isin(fips)]
	dff = dff.sort_values('"Year"')
	dff['Age Adjusted Rate'] = dff['Age Adjusted Rate'].str.strip('(Unreliable)')
	print('DFF', '\n', dff.head()['Age Adjusted Rate'])
	fig = dff.iplot(
		kind = 'area',
		x = '"Year"',
		y = 'Age Adjusted Rate',
		text = '"County"',
		categories = '"County Code"',
		asFigure=True)

	for i, trace in enumerate(fig['data']):
		trace['mode'] = 'lines+markers'
		trace['marker']['size'] = 2
		trace['marker']['line']['width'] = 0.5
		trace['type']='scatter'
		if 'textformat' in fig['data'][i]:
			del fig['data'][i]['textformat']
		if 'textfont' in fig['data'][i]:
			del fig['data'][i]['textfont']
		fig['data'][i] = trace

	# Only show first 500 lines
	fig['data'] = fig['data'][0:500]

	fig['layout']['yaxis']['title'] = 'Age-adjusted death rate per county per year'
	fig['layout']['xaxis']['title'] = 'Year'
	fig['layout']['yaxis']['fixedrange'] = True
	fig['layout']['xaxis']['fixedrange'] = True
	fig['layout']['yaxis']
	fig['layout']['margin'] = dict(t=50, r=150, b=40, l=80)
	fig['layout']['hovermode'] = 'closest'
	fig['layout']['title'] = '<b>{0}</b> counties selected'.format(len(fips))

	if len(fips) > 500:
		fig['layout']['title'] = fig['layout']['title'] + '<br>(only 1st 500 shown)'

	return fig

if __name__ == '__main__':
	app.run_server(debug=True)
