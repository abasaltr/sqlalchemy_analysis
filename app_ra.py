# import dependencies and setup
import numpy as np
import datetime as dt
import os

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

# import Flask
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///data/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

# assign the measurement class to a variable called Measurement
Measurement = Base.classes.measurement

# assign the station class to a variable called Station
Station = Base.classes.station

#################################################
# Function Setup
#################################################

# Function defined to retrieve the last date 12 months ago
def getLastDate():
    # open a communication session with the database
    session = Session(engine)

    # query for the last date in the measurement table
    date_ml = session.query(Measurement.date).order_by(
        Measurement.date.desc()).first()

    # close the session to end the communication with the database
    session.close()

    # convert result type to string
    date_ml = str(date_ml)

    # parse string index for month, year, and day to assign as date type
    date_ml = dt.date(int(date_ml[2:6]), int(
        date_ml[7:9]), int(date_ml[10:12]))

    # define date for 1 year prior to date_ml
    query_date = date_ml - dt.timedelta(days=365)

    return query_date

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Define what to do when a user hits the index route

@app.route("/")
def home():
    print("Server received request for 'Climate API' page...")
    return (
        f"<!DOCTYPE html>"
        f"<html lang='en-us'>"
        f"<meta charset='UTF-8'><title>Climate API</title>"
        f"<p style='color:blue'>Welcome to the Climate API!</p><br/>"
        f"<u>Available Routes:</u><br/>"
        f"<a href='/api/v1.0/precipitation' target='_blank'>/api/v1.0/precipitation</a><br/>"
        f"<a href='/api/v1.0/stations' target='_blank'>/api/v1.0/stations</a><br/>"
        f"<a href='/api/v1.0/tobs' target='_blank'>/api/v1.0/tobs</a><br/>"
        f"<a href='/api/v1.0/<start>' target='_blank'>/api/v1.0/<start></a><br/>"
        f"<a href='/api/v1.0/<start>/<end>' target='_blank'>/api/v1.0/<start>/<end></a><br/>"
    )

# Define what to do when a user clicks each of the routes below

@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for 'Precipitation' page...")

    # call function and assign to query_date the date 12 months ago
    query_date = getLastDate()

    # open a communication session with the database
    session = Session(engine)

    # retrieve the last 12 months of precipitation data (select date and prcp values)
    precip = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= query_date).all()

    # close the session to end the communication with the database
    session.close

    # Create a dictionary from the row data and append to a list of dict_precip
    all_precip = []
    for prcp in precip:
        prcp_dict = {}
        prcp_dict[f'{prcp.date}'] = prcp.prcp
        all_precip.append(prcp_dict)

    # return JOSN representation of dict_precip
    return jsonify(all_precip)

@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'Stations' page...")

    # open a communication session with the database
    session = Session(engine)

    # query all stations
    stations = session.query(Station.name).all()

    # close the session to end the communication with the database
    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(stations))
    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for 'Temperature' page...")

    # call function and assign to query_date the date 12 months ago
    query_date = getLastDate()

    # open a communication session with the database
    session = Session(engine)

    # query all stations for the most active stations using func.count in descending order
    stations_qry2 = session.query(Measurement.station, func.count(Measurement.tobs).label("count")).\
                                group_by(Measurement.station).order_by(
                                    func.count(Measurement.tobs).desc()).all()

    # assign st_h as the most active station using the first row at index 0 in the query retrieved
    st_h = stations_qry2[0][0]

    # query the dates and temperature observations of the most active station for the last year of data.
    stations_qry3 = session.query(Measurement.date, Measurement.tobs).\
                                filter(Measurement.station == st_h,
                                       Measurement.date >= query_date).all()

    # close the session to end the communication with the database
    session.close()

    # Create a dictionary from the row data and append to a list of all_tobs in the last 12 months
    all_tobs = []
    for stations in stations_qry3:
        tobs_dict = {}
        tobs_dict[f"{stations.date}"] = stations.tobs
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)


@app.route("/api/v1.0/<start>")
def start(start):

    print("Server received request for 'Start' page...")

    # open a communication session with the database
    session = Session(engine)

    # query temperature stats of dates greater than start using func.min, func.max, and func.avg
    tobs_qry = session.query(
                        func.count(Measurement.tobs).label('Count'),
                        func.min(Measurement.tobs).label('Min'),
                        func.max(Measurement.tobs).label('Max'),
                        func.avg(Measurement.tobs).label('Mean')).\
                        filter(Measurement.date >= start).all()

    # close the session to end the communication with the database
    session.close()

    # Create a dictionary from the row data in the last 12 months
    for tobs in tobs_qry:
        tobs_dict = {}    
        tobs_dict["Count"] = tobs.Count
        tobs_dict["Min"] = tobs.Min
        tobs_dict["Max"] = tobs.Max
        if tobs.Mean != None:
            tobs_dict["Mean"] = round(tobs.Mean,1)
        else:
            tobs_dict["Mean"] = tobs.Mean

    return jsonify(tobs_dict)


@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
    print("Server received request for 'Start-End' page...")

    # open a communication session with the database
    session = Session(engine)

    # query temperature stats of dates greater than start using func.min, func.max, and func.avg
    tobs_qry2 = session.query(
                        func.count(Measurement.tobs).label('Count'),
                        func.min(Measurement.tobs).label('Min'),
                        func.max(Measurement.tobs).label('Max'),
                        func.avg(Measurement.tobs).label('Mean')).\
                        filter(Measurement.date >= start, Measurement.date <= end).all()

    # close the session to end the communication with the database
    session.close()

    # Create a dictionary from the row data in the last 12 months
    for tobs in tobs_qry2:
        tobs_dict = {}    
        tobs_dict["Count"] = tobs.Count
        tobs_dict["Min"] = tobs.Min
        tobs_dict["Max"] = tobs.Max
        if tobs.Mean != None:
            tobs_dict["Mean"] = round(tobs.Mean,1)
        else:
            tobs_dict["Mean"] = tobs.Mean

    return jsonify(tobs_dict)


# This final if statement simply allows us to run in "Development" mode, which 
# means that we can make changes to our files and then save them to see the results of 
# the change without restarting the server.
if __name__ == "__main__":
    app.run(debug=True)
