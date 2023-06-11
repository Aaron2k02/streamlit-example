import ipyleaflet as L
from ipywidgets import HTML
from ipyleaflet import Popup
from htmltools import css
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, reactive_read, register_widget
import ipywidgets as widgets
import pandas as pd
from keras.models import load_model
# Normalizing Dataset
from sklearn.preprocessing import MinMaxScaler
import os
import numpy as np


app_ui = ui.page_fluid(
    ui.panel_well(
    #ui.input_selectize("x1", "Select a level", filtered_choices),
    ui.row(
        ui.column(1),
        ui.column(2,
         {"style": "background-color: rgba(0, 128, 255, 0.1)"},
         ui.row("Good",{"style": "font-weight: bold; margin-left: 50px;"}),
         ui.row("0-50", {"style": "margin-left: 55px;"}),
        ),
         ui.column(2,
         {"style": "background-color: rgba(0,255,0,0.5)"},
         ui.row("Moderate",{"style": "font-weight: bold; margin-left: 32px;"}),
         ui.row("51-100", {"style": "margin-left: 43px;"}),
        ),
         ui.column(2,
          {"style": "background-color: rgba(255,255,0,0.5)"},          
         ui.row("Unhealthy",{"style": "font-weight: bold; margin-left: 32px;"}),
         ui.row("101-200",{"style": "margin-left: 40px;"}),
        ),
         ui.column(2,
        {"style": "background-color:  rgb(255,165,0) "},
         ui.row("Very Unhealthy",{"style": "font-weight: bold; margin-left: 10px;"}),
         ui.row("201-300",{"style": "margin-left: 40px;"}),
        ),
         ui.column(2,
         {"style": "background-color: rgb(255,0,0)"},
         ui.row("Hazardous",{"style": "font-weight: bold; margin-left: 32px;"}),
         ui.row("Above 300",{"style": "margin-left: 32px;"}),
        ),
       #alignment ='center'  # Align the legend elements in the center   
    ),
        style = "margin-bottom:10px; max-width:1000px; margin-left:210px;"
    ),
    output_widget("map"),
)

def server(input, output, session):
    # Initialize and display when the session starts (1)
    map = L.Map(center=(3.139003, 101.686852), zoom=12, scroll_wheel_zoom=True)
    # Add a distance scale
    map.add_control(L.leaflet.ScaleControl(position="bottomright"))
    register_widget("map", map)
    
    # Create a slider widget for zoom control
    zoom_slider = widgets.IntSlider(description='Zoom', min=1, max=18, value=13)

    # Create a callback function that updates the map's zoom level
    def update_zoom(change):
        map.zoom = change['new']

    # Link the slider's value to the map's zoom level
    zoom_slider.observe(update_zoom, 'value')

    # Create a widget control for the slider
    zoom_control = L.WidgetControl(widget=zoom_slider, position='bottomleft')

    # Add the widget control to the map
    map.add_control(zoom_control)
    
    # Create a DataFrame with city data
  
    # Get the directory path of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the file path for the CSV file
    csv_file_path_map_location = os.path.join(script_dir, "map_location.csv")

    # Create a DataFrame with city data
    city_data = pd.read_csv(csv_file_path_map_location)
    #print(city_data.head())
    
    # Construct the file path for the CSV file
    csv_file_path_air_df = os.path.join(script_dir, "air_df.csv")

    # Read data from file
    air_df = pd.read_csv(csv_file_path_air_df)
    
    # Indexing modification
    air_df.Time = pd.to_datetime(air_df.Time)
    air_df = air_df.set_index('Time')
    
    #To load model
    model_file_path = os.path.join(script_dir,"lstm_model5.h5")
    model = load_model(model_file_path)
    model.summary()
    
    # Define the function to convert air quality category to color
    def get_color(air_quality):
        colors = {
            "Good": "blue",
            "Moderate": "green",
            "Unhealthy": "yellow",
            "Very Unhealthy": "orange",
            "Hazardous": "red"
        }
        return colors.get(air_quality)
    
    # Create a function to convert air pollution index to air quality index
    def convert_air_quality(air_pollution_index):
        if air_pollution_index <= 50:
            return "Good"
        elif air_pollution_index <= 100:
            return "Moderate"
        elif air_pollution_index <= 150:
            return "Unhealthy"
        elif air_pollution_index <= 200:
            return "Very Unhealthy"
        else:
            return "Hazardous"
        
    # function to create marker layers for each city with different colors based on air quality
    def create_marker_layers(city_data, should_plot):
        marker_layers = {}
        for _, city in city_data.iterrows():
            location = (city["Latitude"], city["Longitude"])
            air_quality = city["Category"]
            color = get_color(air_quality)
            
            #message = HTML(value="%s : %d"%(city["Address"], city["API"]))
            
            marker = L.CircleMarker(
                location=location,
                radius=5,
                color=color,
                fill_color=color,
                draggable=False
            )
            
            marker_layers[city["Address"]] = L.LayerGroup(layers=(marker,))
            
            if should_plot:
                map.add_layer(marker_layers[city["Address"]])
        
        return marker_layers
    
    create_marker_layers(city_data, should_plot=True)

    # When the slider changes, update the map's zoom attribute (2)
    @reactive.Effect
    def _():
        map.zoom = input.zoom()

    # When zooming directly on the map, update the slider's value (2 and 3)
    @reactive.Effect
    def _():
        ui.update_slider("zoom", value=reactive_read(map, "zoom"))

    # Everytime the map's bounds change, update the output message (3)
    @output
    @render.ui
    def map_bounds():
        center = reactive_read(map, "center")
        if len(center) == 0:
            return

        lat = round(center[0], 4)
        lon = (center[1] + 180) % 360 - 180
        lon = round(lon, 4)

        return ui.p(f"Latitude: {lat}", ui.br(), f"Longitude: {lon}")
    
    # create a function that clears all markers from the map
    def clear_markers():
        for layer in map.layers: # iterate over each layer of the map
            if isinstance(layer, L.Marker): # check if the layer is a marker
                map.remove_layer(layer) # remove the layer from the map
                
    # create ipywidgets for the user to choose the year, month, date and hour of the data
    year_picker = widgets.IntSlider(description="Year", min=2018, max=2022, value=2020) # a slider for the year
    month_picker = widgets.IntSlider(description="Month", min=1, max=12, value=1) # a slider for the month
    date_picker = widgets.IntSlider(description="Date", min=1, max=31, value=1) # a date picker for the date
    hour_picker = widgets.IntSlider(description="Hour", min=0, max=23, value=12) # a slider for the hour
    submit_button = widgets.Button(description="Submit") # a button for submitting the selection
    
    # create a widget control that contains the ipywidgets
    widget_control = L.WidgetControl(widget=widgets.VBox([year_picker, month_picker, date_picker, hour_picker, submit_button]), position="topright")
    
    # add the widget control to the map
    map.add_control(widget_control)
    
    # create a callback function that will update the map when the user clicks the submit button
    def on_submit_clicked(button):
        clear_markers() # clear all markers from the map
        year = str(year_picker.value) # get the selected year as a string
        month = str(month_picker.value).zfill(2) # get the selected month as a string with leading zeros
        date = str(date_picker.value).zfill(2) # get the selected date as a string with leading zeros
        hour = str(hour_picker.value).zfill(2) + ':00:00' # get the selected hour as a string with leading zeros and add the remaining time components

        start_date  = f'{year}-{month}-{date}' # combine the date and time components
        start_hour = f'{hour}'
        
        start_datetime = pd.to_datetime(start_date + ' ' + start_hour)
        end_datetime = start_datetime - pd.DateOffset(hours=4)
        
        selected_data = air_df.loc[end_datetime:start_datetime]
        
        #Normalising data
        values = selected_data.values
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_dataset = scaler.fit_transform(values)
        
        #Transform 
        def to_supervised(train):
            window_size = 4
            X = []
            Y = []
            for i in range(window_size, len(train)):
                X.append(train[i-window_size:i, :])  # Input sequence of previous data
                targets = train[i, 0:train.shape[1]]  # get target variable
                Y.append(targets) 
            
            return X, Y
        
        X, Y = to_supervised(scaled_dataset)
        # X will have the previous 4 hour of data 
        X = np.array(X)
        # Y will have the hour to be predicted data
        Y = np.array(Y)
        
        #Taking predictions
        prediction = model.predict(X)
        
        #Scaling back to original values
        d = scaled_dataset[:X.shape[0],scaled_dataset.shape[1]:]
        Y_predicted = np.concatenate((prediction,d[:X.shape[0],scaled_dataset.shape[1]:]), axis =1)
        Y_tested = np.concatenate((Y, d[:X.shape[0],scaled_dataset.shape[1]:]), axis = 1)
        
        #Take inverse transform
        Y_predicted = scaler.inverse_transform(Y_predicted)
        Y_tested = scaler.inverse_transform(Y_tested)
        Y_predicted = Y_predicted[:,0:scaled_dataset.shape[1]]
        Y_tested = Y_tested[:,0:scaled_dataset.shape[1]]
        
        print(Y_predicted.round(decimals=3))
        print('################################')
        print(Y_tested.round(decimals=3))
        # Update 'API' column with values from 'Y_predicted'
        city_data['API'] = np.array(Y_predicted).flatten()
        #print(city_data['API'])
        # Update 'Category' column based on 'API' values
        city_data['Category'] = city_data['API'].apply(convert_air_quality)
        #print(city_data['Category'])
        
        create_marker_layers(city_data, should_plot=True)
                
        
    # add the callback function to the submit button
    submit_button.on_click(on_submit_clicked)
    
    # Create a legend widget using ipywidgets
    legend_widget = widgets.VBox([
        widgets.HTML(value='<div><span style="color:blue;font-size:20px">&#9679;</span> Good</div>'),
        widgets.HTML(value='<div><span style="color:green;font-size:20px">&#9679;</span> Moderate</div>'),
        widgets.HTML(value='<div><span style="color:yellow;font-size:20px">&#9679;</span> Unhealthy</div>'),
        widgets.HTML(value='<div><span style="color:orange;font-size:20px">&#9679;</span> Very Unhealthy</div>'),
        widgets.HTML(value='<div><span style="color:red;font-size:20px">&#9679;</span> Hazardous</div>')
    ])

    # Create an ipyleaflet control widget for the legend
    legend_control = L.WidgetControl(widget=legend_widget, position="bottomright")
    
    # Add the legend control to the map
    #map.add_control(legend_control)

app = App(app_ui, server)
