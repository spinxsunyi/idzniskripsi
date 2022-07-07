# from flask import Flask
# from flask import render_template
# from markupsafe import escape
# app = Flask(__name__)

# @app.route("/")
# def index():
#     return render_template('home.html')

# @app.route("/name/<name>")
# def a(name):
#     return f"Hello, {escape(name)}!"
    
# @app.route('/hello/')
# @app.route('/hello/<name>')
# def hello(name=None):
#     return render_template('hello.html', name=name)

# @app.route('/process')
# def process():
#     return("processed")

# app.logger.warning('A warning occurred (%d apples)', 42)
# app.logger.error('An error occurred')


__author__ = 'idzni shabrina & suami'
from urllib.request import AbstractDigestAuthHandler
from flask import Flask, make_response, request, render_template
import io
from markupsafe import escape

import plotly.graph_objs as go
import plotly.offline as plt
import plotly

# import csv
import psychrolib
psychrolib.SetUnitSystem(psychrolib.SI)

import pandas as pd
import json
from pandas import ExcelFile

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('inputPage.html')

@app.route("/bar_chart")
def bar_chart_plot():
    df = pd.read_csv("countries.csv")
    trace1 = go.Bar(x=df["Country"][0:20], y=df["GDP ($ per capita)"])
    layout = go.Layout(title="GDP of the Country", xaxis=dict(title="Country"),
                       yaxis=dict(title="GDP Per Capita"), )
    data = [trace1]
    fig = go.Figure(data=data, layout=layout)
    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('charts.html', plot=fig_json)


@app.route('/transform', methods=["POST"])
def transform_view():
    f = request.files['data_file']
    if not f:
        return "No file"

    # stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
    # stream = io.StringIO(f.stream.read(), newline=None)
    # stream.seek(0)
    # data = pd.read_excel(stream, sheet_name='Variabel Input')

    excel_data = ExcelFile(io.BytesIO(f.stream.read()))
    data = excel_data.parse(excel_data.sheet_names[-2])
    # data = pd.read_csv(stream, header=0, sep=';',dtype=float, converters={'Date Time, GMT+07:00':str})
    # print(type(data))
    # data.info()
    print(data)

    # csv_input = csv.reader(stream)
    # print("file contents: ", stream)
    # print(type(stream))
    # # print(csv_input)
    # for row in csv_input:
    #     print(row)

    #Deklarasi Varibel Input

    Po = 101.3 #kPa [Tekanan atmosfer]
    E = 0.622 #ratio [Rasio berat molekul udara kering/uap air]
    l = 2500.9 #kj/kg [Kalor penguapan air pada 0 derajat celsius] (https://www.engineeringtoolbox.com/water-properties-d_1573.html)
    Ca = 1.006 #kj/kg derajat celcius [Kalor spesifik udara kering pada tekanan konstan] (https://www.engineeringtoolbox.com/air-specific-heat-capacity-d_705.html)
    Cv = 1.86 #kj/kg derajat celcius [Kalor spesifik uap air pada tekanan konstan] (Engineering Thermodynamics, Gupta S.K. 2013) 
    A = 64 # meter persegi [Luas area rumah kaca]
    k = 0.8 #W/meter persegi deraijat celcius [Perbandingan transmisi panas kaca] (http://hyperphysics.phy-astr.gsu.edu/hbase/Tables/thrcn.html) 
    w = 1.07 #Rasio permukaan kaca terhadap permukaan lantai [perhitungan manual]
    T = 0.2 #(SEMENTARA) 
    mr = 0.015 #Kg/s [Debit nozzle] (Skripsi Kingdom)
    R = 0.65 #Rasio berat air yang dievaporasikan
    tfs = 240 #sekon [Durasi siklus pengoperasian fcs] (Hasil percobaan pendahuluan)
    Vsp = 37.41 #kg Dry Air (perhitungan manual)
    exp = 2.718281828

    #RHit = 0.8 #80% (Target RH tanaman tomat)



    #formula untuk menghitung waktu fogging dan waktu stand by

    dataT = [] # array untuk ditampilkan di diagram
    diti = {} # dictionary untuk ditampilkan di window table
    dataTF = []
    dataTS = []

    #pyschrolib untuk mendapatkan data TWI  TWO dan XSI

    # Iterasi untuk menghitung ts dan tf masing-masing siklus
    for index,row in data.iterrows() :
        Tdi = row [2]
        RHi = row [3]
        So = row [4]
        # Twi = row [5]
        Tdo = row [6]
        RHo = row [7]
        # Two = row [8]
        Twi = psychrolib.GetTWetBulbFromRelHum(Tdi,RHi,101300)
        Two = psychrolib.GetTWetBulbFromRelHum(Tdo,RHo,101300)
        
    # Urutan Formula
        # Si = So*T*(1)
        estwi = 0.61078*(exp**((17.2693882*Twi)/(Twi+237.3)))
        estwo = 0.61078*(exp**((17.2693882*Two)/(Two+237.3)))
        ei = estwi - 0.000662*Po*(Tdi-Twi)
        eo = estwo - 0.000662*Po*(Tdo-Two)
        estdi = 0.61078*(exp**((17.2693882*Tdi)/(Tdi+237.3)))
        estdo = 0.61078*(exp**((17.2693882*Tdo)/(Tdo+237.3)))
    
        Xi = E*(ei/(Po-ei))
        Xo = E*(eo/(Po-eo))
        Ii = Ca*Tdi+(l+(Cv*Tdi))*Xi*1000
        Io = Ca*Tdo+(l+(Cv*Tdo))*Xo
        Xsi = psychrolib.GetHumRatioFromEnthalpyAndTDryBulb(Ii,Tdi)
        DX = abs(Xsi - Xi)
        mf = DX * Vsp / 60
        tf = tfs*mf/mr
        ts = tfs - tf
        
        #dataT adalah data hasil durasi untuk ditampilkan pada Grafik
        dataT.append(tf)
        dataT.append(ts)
        
        #dataTF dan data TS adalah array yang akan dijadikan dataframe durasi hasil untuk di save di excel
        #dataTF dan data TS ditambahkan
        dataTF.append(tf)
        dataTS.append(ts)
        
        diti[str(index)] = {'Fogging': tf, 'Stand By': ts, 'Keterangan': 'siklus'+str(index)}

    # Dibuat dictionary durasi untuk dibuat dataframe    
    durasi = {'tf': dataTF,
            'ts': dataTS
            }
    # Dibuat dataframe durasi_df
    durasi_df = pd.DataFrame(durasi, columns = ['tf','ts'])
    print(durasi_df)
    # dataframe durasi_df disave sebagai file excel
    # durasi_df.to_excel("output_durasi.xlsx")  
    # return send_file(
    #     io.BytesIO(durasi_df.to_csv(index=False, encoding='utf-8').encode()),
    #     as_attachment=True,
    #     attachment_filename='result.csv',
    #     mimetype='text/csv')
    # return "ok"

    # trace1 = go.Scatter(x=df["Country"][0:20], y=df["GDP ($ per capita)"])
    # layout = go.Layout(title="GDP of the Country", xaxis=dict(title="Country"),
    #                    yaxis=dict(title="GDP Per Capita"), )
    # data = [trace1]
    # fig = go.Figure(data=data, layout=layout)
    # fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # return render_template('charts.html', plot=fig_json)

    result = (f.stream.read())
    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=result.csv"
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)