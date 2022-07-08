__author__ = 'idzni shabrina & suami'
# VERSI JUNI 2022
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
    excel_data = ExcelFile(io.BytesIO(f.stream.read()))
    data = excel_data.parse(excel_data.sheet_names[0])

    # Mendeklarasikan variabel
    hasilSimulasi = pd.DataFrame(columns = ['RH1','RH2','Td1','Td2','I','AH1','AH2','deltaAH','durasiFogging','durasiOff'])
    durasiFullSiklus = 240 #sekon [Durasi siklus pengoperasian fcs] (Hasil percobaan pendahuluan)
    massaUdaraKering = 341.04 #kg, didapat dari volume greenhouse * masa jenis udara
#   # Hitung debit nozzle # 12 nozzle, masing masing 0.00125 m3 / sekon
    debitNozzle = 12 * 0.00125 

        # Iterasi untuk menghitung ts dan tf masing-masing siklus
    for index,row in data.iterrows() :
        Td1 = row [3]
        RH1 = row [1] * (1 / 100) # dibagi 100 supaya jadi persentase

        #pyschrolib digunakan untuk mendapatkan data TWI  TWO dan XSI
        AH1 = psychrolib.GetHumRatioFromRelHum(Td1,RH1,101300)
        AH2 = psychrolib.GetHumRatioFromRelHum(Td2,RH2,101300)

#     # 4. Cari selisih kelembapan mutlak dari HOBO Dan Target
        deltaAH = abs(AH2 - AH1)
#     # 2. Hitung massa air = selisih kelembapan mutlak x massa udara kering / RH2
        massaAir = deltaAH * massaUdaraKering / RH2
#     # 3.durasi = massa air / debit nozzle
        durasiFogging = massaAir / debitNozzle 
        # print(index, RH1, RH2, Td1, AH1, AH2, deltaAH, durasiFogging, massaAir)
        if(durasiFogging > durasiFullSiklus):
            durasiFogging = durasiFullSiklus

        durasiOff = durasiFullSiklus - durasiFogging

#         tf0=tf0+tf
#         dataX.append(tf0)
#         dataY.append(1)

#         dataX.append(tf0)
#         dataY.append(0)

#         tf0= tf0+ts
#         dataX.append(tf0)
#         dataY.append(0)

#         dataX.append(tf0)
#         dataY.append(1)
        RH1 = round(RH1,2)
        RH2 = round(RH2,2)
        Td1 = round(Td1,1)
        AH1 = round(AH1,4)
        AH2 = round(AH2,4)
        deltaAH = round(deltaAH,4)
        durasiFogging = round(durasiFogging,0)
        hasilSimulasi = hasilSimulasi.append({'RH1': RH1, 'RH2': RH2, 'Td1': Td1, 'Td2': Td2, 'I': 0, 'AH1': AH1, 'AH2':AH2, 'deltaAH':deltaAH, 'durasiFogging':durasiFogging, 'durasiOff':durasiOff }, ignore_index = True)
        print(hasilSimulasi)

    # dataX = [0]
    # dataY = [1]
#     # dataTF = []
#     # dataTS = []
#     tf0=0

#     # Iterasi untuk menghitung ts dan tf masing-masing siklus
#     for index,row in data.iterrows() :
#         Tdi = row [2]
#         RHi = row [3]

#         AH1 = psychrolib.GetHumRatioFromRelHum(Tdi,RHi,101300)
#         AH2 = psychrolib.GetHumRatioFromRelHum(Tdo,rh2,101300)
        
#         # Urutan Formula
#         # Si = So*T*(1) #karena gabutuh Si jadi diabaikan
#         estwi = 0.61078*(exp**((17.2693882*Twi)/(Twi+237.3)))
#         estwo = 0.61078*(exp**((17.2693882*Two)/(Two+237.3)))
#         ei = estwi - 0.000662*Po*(Tdi-Twi)
#         eo = estwo - 0.000662*Po*(Tdo-Two)
#         estdi = 0.61078*(exp**((17.2693882*Tdi)/(Tdi+237.3)))
#         estdo = 0.61078*(exp**((17.2693882*Tdo)/(Tdo+237.3)))
    
#         Xi = E*(ei/(Po-ei))
#         Xo = E*(eo/(Po-eo))
#         Ii = Ca*Tdi+(l+(Cv*Tdi))*Xi*1000
#         Io = Ca*Tdo+(l+(Cv*Tdo))*Xo

#         #pyschrolib digunakan untuk mendapatkan data TWI  TWO dan XSI
#         Xsi = psychrolib.GetHumRatioFromEnthalpyAndTDryBulb(Ii,Tdi)
#         DX = abs(Xsi - Xi)
#         mf = DX * Vsp / 60
#         tf = round(tfs*mf/mr)
#         ts = round(tfs - tf)
        


#         #dataTF dan data TS adalah array yang akan dijadikan dataframe durasi hasil untuk di save di excel atau dalam bentuk tabel
#         # dataTF.append(tf)
#         # dataTS.append(ts)
        
#         diti[str(index)] = {'Fogging': tf, 'Standby': ts, 'Keterangan': 'siklus #'+str(index)}
    
#     # print(diti)
#     # Dibuat dataframe durasi_df
#     dataX.pop()
#     dataY.pop()
#     durasi_on_off_df = pd.DataFrame( {'status':dataY,'time': dataX})
#     # print(durasi_on_off_df)
    
#     trace1 = go.Scatter(x=durasi_on_off_df["time"], y=durasi_on_off_df["status"])
#     layout = go.Layout(title="Timelincone Fogging", xaxis=dict(title="Time (detik)"),
#                        yaxis=dict(title="Status on/off"), )

#     fig = go.Figure(data=[trace1], layout=layout)
#     fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#     return render_template('result.html', plot=fig_json, diti=diti)
    return render_template('halaman_hasil.html', data = hasilSimulasi)
    

# # Function untuk menampilkan halaman
# def show_page():
#     return("processed")

# # function untuk menerima data json hasil perhitungan dan menampilkannya dalam bentuk tabel.
# def build_table():
#     return()

# # function untuk menerima data json hasil perhitungan dan menampilkannya dalam bentuk grafik
def build_chart():
    return()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)