__author__ = 'idzni shabrina'
# VERSI JANUARY 2023
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
def index():
    return render_template('halaman_utama.html')

@app.route('/hasil')
def form():
    return render_template('halaman_hasil.html')

# # Function untuk menerima data input menjadi data frame kemudian menghitung ts dan tf dan menghasilkan output json untuk ditampilkan
@app.route('/process', methods=["POST"])
def process():
# Terima data
    f = request.files['data_file']
    if not f:
        return render_template('nodata.html')
    RH2 = request.form['RH2']
    RH2 = int(RH2) / 100
    Td2 = request.form['Td2']
    Td2 = float(Td2)
    persenPenguapan = request.form['persenPenguapan']
    persenPenguapan = int(persenPenguapan) / 100
    persenDebit = request.form['persenDebit']
    persenDebit = int(persenDebit) / 100
    durasiFullSiklus = int(request.form['durasiFullSiklus']) #240 sekon [Durasi siklus pengoperasian fcs] (Hasil percobaan pendahuluan)

    excel_data = ExcelFile(io.BytesIO(f.stream.read()))
    data = excel_data.parse(excel_data.sheet_names[0])

    # Mendeklarasikan variabel untuk menampung data hasil simulasi
    hasilSimulasi = pd.DataFrame(columns = ['RH1','RH2','Td1','Td2','I','AH1','AH2','deltaAH','durasiFogging','durasiOff'])
    
    massaUdaraKering = 341.04 #kg, didapat dari volume greenhouse * masa jenis udara
#   # Hitung debit nozzle # 12 nozzle, masing masing 0.00125 m3 / sekon
    debitNozzle = 12 * 0.00125 * persenDebit  # debit nozzle * %debit. Ideally 100%

        # Iterasi untuk menghitung ts dan tf masing-masing siklus
    for index,row in data.iterrows() :
        Td1 = row [3]
        RH1 = row [1] * (1 / 100) # dibagi 100 supaya jadi persentase
        I = row[4]

        #pyschrolib digunakan untuk mendapatkan data TWI  TWO dan XSI
        AH1 = psychrolib.GetHumRatioFromRelHum(Td1,RH1,101300)
        AH2 = psychrolib.GetHumRatioFromRelHum(Td2,RH2,101300)

#     # 4. Cari selisih kelembapan mutlak dari HOBO Dan Target
        deltaAH = abs(AH2 - AH1)
#     # 2. Hitung massa air = selisih kelembapan mutlak x massa udara kering / RH2
        massaAir = deltaAH * massaUdaraKering / RH2 
        massaAir = massaAir / persenPenguapan
        # massa air / %penguapan
#     # 3.durasi = massa air / debit nozzle
        durasiFogging = massaAir / debitNozzle 
        # print(index, RH1, RH2, Td1, AH1, AH2, deltaAH, durasiFogging, massaAir)
        if(durasiFogging > durasiFullSiklus):
            durasiFogging = durasiFullSiklus

        durasiOff = durasiFullSiklus - durasiFogging
        
        RH1 = round(RH1,2)
        RH2 = round(RH2,2)
        Td1 = round(Td1,1)
        AH1 = round(AH1,4)
        AH2 = round(AH2,4)
        deltaAH = round(deltaAH,4)
        durasiFogging = round(durasiFogging,0)
        durasiOff = round(durasiOff,0)
        hasilSimulasi = hasilSimulasi.append({'RH1': RH1, 'RH2': RH2, 'Td1': Td1, 'Td2': Td2, 'I': I, 'AH1': AH1, 'AH2':AH2, 'deltaAH':deltaAH, 'durasiFogging':durasiFogging, 'durasiOff':durasiOff }, ignore_index = True)

    dataGrafik = build_chart(hasilSimulasi)
    dataGrafikSuhu = build_chart_suhu(hasilSimulasi, durasiFullSiklus)
    dataGrafikHumidity = build_chart_humidity(hasilSimulasi, durasiFullSiklus)
    jsonHasil = hasilSimulasi.to_json(orient="values")

    return render_template('halaman_hasil.html', plot=dataGrafik, plot2=dataGrafikSuhu, plot3=dataGrafikHumidity, data=hasilSimulasi,parsed=jsonHasil, durasiFullSiklus = durasiFullSiklus)
    

# # function untuk menerima data json hasil perhitungan dan menampilkannya dalam bentuk grafik
def build_chart(dfsimulasi):
    dataX = [0]
    dataY = [1]
    tf0 = 0

    for index, row in dfsimulasi.iterrows():
        tf0=tf0+ row.durasiFogging
        dataX.append(tf0)
        dataY.append(1)

        dataX.append(tf0)
        dataY.append(0)

        tf0= tf0+row.durasiOff
        dataX.append(tf0)
        dataY.append(0)

        dataX.append(tf0)
        dataY.append(1)

    dataX.pop()
    dataY.pop()

    durasi_on_off_df = pd.DataFrame( {'status':dataY,'time': dataX})

    trace1 = go.Scatter(x=durasi_on_off_df["time"], y=durasi_on_off_df["status"])
    layout = go.Layout(title="Timeline status on-off pompa pengabutan", xaxis=dict(title="waktu (detik)"), yaxis=dict(title="Status on/off"), )
    fig = go.Figure(data=[trace1], layout=layout)
    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return(fig_json)

def build_chart_suhu(dfsimulasi, durasiFullSiklus):
    dataY = []
    tf0 = -durasiFullSiklus
    dataX = []

    for index, row in dfsimulasi.iterrows():
        tf0 = tf0 + durasiFullSiklus
        dataX.append(tf0)
        dataY.append(row.Td1)

    dataGrSuhu = pd.DataFrame( {'suhu':dataY,'time': dataX})
    trace2 = go.Scatter(x=dataGrSuhu["time"], y=dataGrSuhu["suhu"])
    layout2 = go.Layout(title="Timeline suhu dalam rumah kaca", xaxis=dict(title="waktu (detik)"), yaxis=dict(title="suhu (celcius)"), )
    fig2 = go.Figure(data=[trace2], layout=layout2)
    fig_json2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    return(fig_json2)

def build_chart_humidity(dfsimulasi, durasiFullSiklus):
    dataY = []
    tf0 = - durasiFullSiklus
    dataX = []

    for index, row in dfsimulasi.iterrows():
        tf0 = tf0 + durasiFullSiklus
        dataX.append(tf0)
        dataY.append(row.RH1)

    dataGrHumid = pd.DataFrame( {'humidity':dataY,'time': dataX})
    trace3 = go.Scatter(x=dataGrHumid["time"], y=dataGrHumid["humidity"])
    layout3 = go.Layout(title="Timeline humidity dalam rumah kaca", xaxis=dict(title="waktu (detik)"), yaxis=dict(title="Relative Humidity (%)"), )
    fig3 = go.Figure(data=[trace3], layout=layout3)
    fig_json3 = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    return(fig_json3)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)