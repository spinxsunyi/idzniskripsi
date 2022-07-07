

__author__ = 'idzni shabrina & suami'
from urllib.request import AbstractDigestAuthHandler
from flask import Flask, make_response, request, render_template
import io
from markupsafe import escape
# Declare import library psichrometrics
import psychrolib
psychrolib.SetUnitSystem(psychrolib.SI)
# Declare import library Pandas json and data
from pandas import ExcelFile
import json
import pandas as pd
# Declare import library plotly for graphical chart rendering
import plotly
import plotly.offline as plt
import plotly.graph_objs as go


app = Flask(__name__)


# Function Home Page, penjelasan fungsi aplikasi, dan kolom input data dari HOBO untuk dihitung waktunya
@app.route('/')
def form():
    return render_template('index2.html')

# Function untuk menerima data input menjadi data frame kemudian menghitung ts dan tf dan menghasilkan output json untuk ditampilkan
@app.route('/process', methods=["POST"])
def index():
# Terima data
    f = request.files['data_file']
    if not f:
        return render_template('nodata.html')
    excel_data = ExcelFile(io.BytesIO(f.stream.read()))
    data = excel_data.parse(excel_data.sheet_names[-2])
    print(data)

# Hitung TS dan TF
    # Deklarasi variabel
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

    dataT = [] # array untuk ditampilkan di diagram
    dataX = [0]
    dataY = [1]
    diti = {} # dictionary untuk ditampilkan di window table
    # dataTF = []
    # dataTS = []
    tf0=0

    # Iterasi untuk menghitung ts dan tf masing-masing siklus
    for index,row in data.iterrows() :
        Tdi = row [2]
        RHi = row [3]
        So = row [4]
        # Twi = row [5] #data TWi diabaikan, yang diabil adalah hasil perhitungan
        Tdo = row [6]
        RHo = row [7]
        # Two = row [8] #data TWo diabaikan, yang diabil adalah hasil perhitungan
        #pyschrolib digunakan untuk mendapatkan data TWI  TWO dan XSI
        Twi = psychrolib.GetTWetBulbFromRelHum(Tdi,RHi,101300)
        Two = psychrolib.GetTWetBulbFromRelHum(Tdo,RHo,101300)
        
        # Urutan Formula
        # Si = So*T*(1) #karena gabutuh Si jadi diabaikan
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

        #pyschrolib digunakan untuk mendapatkan data TWI  TWO dan XSI
        Xsi = psychrolib.GetHumRatioFromEnthalpyAndTDryBulb(Ii,Tdi)
        DX = abs(Xsi - Xi)
        mf = DX * Vsp / 60
        tf = round(tfs*mf/mr)
        ts = round(tfs - tf)
        
        #dataT adalah array hasil durasi untuk ditampilkan pada Grafik
        dataT.append(tf)
        dataT.append(ts)

        tf0=tf0+tf
        dataX.append(tf0)
        dataY.append(1)

        dataX.append(tf0)
        dataY.append(0)

        tf0= tf0+ts
        dataX.append(tf0)
        dataY.append(0)

        dataX.append(tf0)
        dataY.append(1)


        #dataTF dan data TS adalah array yang akan dijadikan dataframe durasi hasil untuk di save di excel atau dalam bentuk tabel
        # dataTF.append(tf)
        # dataTS.append(ts)
        
        diti[str(index)] = {'Fogging': tf, 'Standby': ts, 'Keterangan': 'siklus #'+str(index)}
    
    # print(diti)
    # Dibuat dataframe durasi_df
    dataX.pop()
    dataY.pop()
    durasi_on_off_df = pd.DataFrame( {'status':dataY,'time': dataX})
    # print(durasi_on_off_df)
    
    trace1 = go.Scatter(x=durasi_on_off_df["time"], y=durasi_on_off_df["status"])
    layout = go.Layout(title="Timelincone Fogging", xaxis=dict(title="Time (detik)"),
                       yaxis=dict(title="Status on/off"), )

    fig = go.Figure(data=[trace1], layout=layout)
    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('result.html', plot=fig_json, diti=diti)
    

# # Function untuk menampilkan halaman
# def show_page():
#     return("processed")

# # function untuk menerima data json hasil perhitungan dan menampilkannya dalam bentuk tabel.
# def build_table():
#     return()

# # function untuk menerima data json hasil perhitungan dan menampilkannya dalam bentuk grafik
# def build_chart():
#     return()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)