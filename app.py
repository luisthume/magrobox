import os, csv
import shutil
import sys
import pandas as pd 
import numpy as np
import operator

from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
from flask import Flask, session

basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join('uploads')

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['csv','xls'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('index.html')

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response    


@app.route('/', methods=['POST'])
def upload_file():
    # shutil.rmtree(UPLOAD_FOLDER)
    # os.mkdir(UPLOAD_FOLDER)
    disp_div = 'none'
    disp_div_tumor = 'none'

    d = request.form.to_dict()
    # print("dddd;",d)
    button_name = 'None'
    if (len(d)!=0):
        button_name = list(d.items())[-1][0]

    file = request.files['file']
    print("file:",file)
    if file.filename == '':
        flash('No file selected for uploading','red')
        # return redirect(request.url)
        return render_template('index.html', disp_div = disp_div)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        shutil.rmtree(UPLOAD_FOLDER)
        os.mkdir(UPLOAD_FOLDER)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File successfully uploaded!', 'green')
        print(UPLOAD_FOLDER)
        print("==>",os.path.join(UPLOAD_FOLDER, sorted(os.listdir(app.config['UPLOAD_FOLDER']))[0]))
        csv_file = pd.read_csv(os.path.join(UPLOAD_FOLDER, sorted(os.listdir(app.config['UPLOAD_FOLDER']))[0]))
        csv_shape = csv_file.shape

        spread = 0.02 # a.m.

        LUT_SCORE = np.zeros(100,dtype=float)       

        def calculate_LUT_SCORE(taxa_rentabilidade_media_local):
            for a in range(100):          
                LUT_SCORE[100 - a - 1] = taxa_rentabilidade_media_local*0.01*a + (taxa_rentabilidade_media_local - spread)
                #print(LUT_SCORE[100 - a - 1])

        #calculate_LUT_SCORE(0.045)

        csv_filename = os.path.join(UPLOAD_FOLDER, filename)

        csvpath = csv_filename
        print(csvpath)

        p1 = pd.read_csv(csvpath, engine='python', sep=',', decimal=".", error_bad_lines=False)

        target_operacao = 0
        for row in p1.iterrows():   
            #print(row[1][0])
            #print(row[1][1])
            target_operacao = float(row[1][0])
            taxa_rentabilidade_media = float(row[1][1])
            break

        target_desagio = target_operacao*taxa_rentabilidade_media


        p1 = pd.read_csv(csvpath, engine='python', sep=',', decimal=".", error_bad_lines=False, skiprows=3)
        p1 = p1.replace(np.nan,0, regex=True)

        class Empresa:
                def __init__(self, CNPJ, Score, Taxa, Prazo, Nome, Semana, Valor, Rebate, Exec):
                    self.CNPJ = CNPJ
                    self.Score = int(Score*100)
                    self.Taxa = float(Taxa*0.01)
                    self.Prazo = Prazo
                    self.Nome = Nome        
                    self.Valor = Valor
                    self.Semana = Semana
                    self.Desagio = 0
                    self.Rebate = Rebate
                    self.Desagio_liq = 0
                    self.Exec = Exec
                  
        lista_empresas = []
        for index, row in p1.iterrows():
            if row['SEMANA 1'] != 0:
                empresa = Empresa(row['CNPJ'],row['SCORE'],row['TAXA'],row['PRAZO'],row['NOME'][:12],'1',row['SEMANA 1'],row['REBATE'],row['EXEC'])
            if row['SEMANA 2'] != 0:
                empresa = Empresa(row['CNPJ'],row['SCORE'],row['TAXA'],row['PRAZO'],row['NOME'][:12],'2',row['SEMANA 2'],row['REBATE'],row['EXEC'])
            if row['SEMANA 3'] != 0:
                empresa = Empresa(row['CNPJ'],row['SCORE'],row['TAXA'],row['PRAZO'],row['NOME'][:12],'3',row['SEMANA 3'],row['REBATE'],row['EXEC'])
            if row['SEMANA 4'] != 0:
                empresa = Empresa(row['CNPJ'],row['SCORE'],row['TAXA'],row['PRAZO'],row['NOME'][:12],'4',row['SEMANA 4'],row['REBATE'],row['EXEC'])
            lista_empresas.append(empresa)

        lista_empresas = sorted(lista_empresas, key=operator.attrgetter('Semana'), reverse = False)

        def calculate_total_tax_full(lista_empresas, taxa_conversao_funil):
            desagio = 0
            total_operado = 0
            prazo_medio = 0
            desagio_liq = 0
            count = 0
            for a in range(len(lista_empresas)):        
                if not lista_empresas[a].Exec:
                    total_operado += lista_empresas[a].Valor*taxa_conversao_funil
                    lista_empresas[a].Desagio = LUT_SCORE[lista_empresas[a].Score]*(lista_empresas[a].Prazo/30.0)*lista_empresas[a].Valor*taxa_conversao_funil          
                    lista_empresas[a].Desagio_liq = lista_empresas[a].Desagio - lista_empresas[a].Desagio*lista_empresas[a].Rebate
                    desagio += lista_empresas[a].Desagio
                    desagio_liq += lista_empresas[a].Desagio_liq
                    prazo_medio += lista_empresas[a].Prazo/30.0
                    count += 1
                else:
                    total_operado += lista_empresas[a].Valor
                    lista_empresas[a].Desagio = lista_empresas[a].Taxa*(lista_empresas[a].Prazo/30.0)*lista_empresas[a].Valor
                    lista_empresas[a].Desagio_liq = lista_empresas[a].Desagio - lista_empresas[a].Desagio*lista_empresas[a].Rebate
                    desagio += lista_empresas[a].Desagio
                    prazo_medio += lista_empresas[a].Prazo/30.0
                    desagio_liq += lista_empresas[a].Desagio_liq
                    count += 1

            return  (desagio / total_operado), desagio, total_operado, prazo_medio/count, desagio_liq

        def calculate_total_tax_real(lista_empresas):
            desagio = 0
            total_operado = 0
            prazo_medio = 0
            count = 0
            for a in range(len(lista_empresas)):        
                if not lista_empresas[a].Exec:
                    total_operado += lista_empresas[a].Valor
                    lista_empresas[a].Desagio = LUT_SCORE[lista_empresas[a].Score]*lista_empresas[a].Valor
                    desagio += lista_empresas[a].Desagio
                    prazo_medio += lista_empresas[a].Prazo/30.0
                    count += 1
                else:
                    total_operado += lista_empresas[a].Valor
                    lista_empresas[a].Desagio = lista_empresas[a].Taxa*lista_empresas[a].Valor
                    desagio += lista_empresas[a].Desagio
                    prazo_medio += lista_empresas[a].Prazo/30.0
                    count += 1


            return  (desagio / total_operado), desagio, total_operado

        valor_total = 0
        for a in range(len(lista_empresas)):    
            valor_total += lista_empresas[a].Valor

        taxa_conversao_funil = (target_operacao/valor_total)

        tax = 0.01
        taxa_final = desagio_liq = 0

        while desagio_liq < target_desagio:
            calculate_LUT_SCORE(tax)
            taxa_final, desagio_final, valor_total_convertido, prazo_medio, desagio_liq = calculate_total_tax_full(lista_empresas, taxa_conversao_funil)
            #print(taxa_final, desagio_final, valor_total)  
            tax += 0.0001

        #print('Taxa de Conversao: %.3f'% (target_operacao/valor_total))

        print('\nCNPJ','\t\t\tTaxa','\tNova Taxa','\tNome','\tSemana','\tValor','\t\tDesagio(*)', '\tRebate','\tDesagio_Liq(*)','\tPrazo','\tExec')

        desagio = valor_total = valor_realizado = desagio_realizado = 0
        desagio_liq = desagio_liq_realizado = 0


        csv_filename_output = csv_filename.replace('_input.csv', '_output.csv')
        output = open(csv_filename_output, 'w')    

        output.write('CNPJ,Taxa,Nova Taxa,Nome,Semana,Valor,Desagio(*),Rebate,Desagio_Liq(*),Prazo,Exec')
        output.write('\n')

        def write_csv_row(empresa, use_LUT_SCORE):
            output.write(str(empresa.CNPJ))
            output.write(',')
            output.write('\t %.4f' %(empresa.Taxa))
            output.write(',')
            if use_LUT_SCORE:
                output.write('\t %.4f' % (LUT_SCORE[lista_empresas[a].Score]))
            else:
                output.write('X.XX')
            output.write(',')
            output.write(str(empresa.Nome))
            output.write(',')
            output.write(str(empresa.Semana))
            output.write(',')
            output.write(str(empresa.Valor))
            output.write(',')
            output.write(str(empresa.Desagio))
            output.write(',')
            output.write(str(empresa.Rebate))
            output.write(',')
            output.write(str(empresa.Desagio_liq))
            output.write(',')
            output.write(str(empresa.Prazo))
            output.write(',')
            output.write(str(empresa.Exec))
            output.write(',')
            output.write('\n')
            

        for a in range(len(lista_empresas)):        
            if lista_empresas[a].Exec:
                print(lista_empresas[a].CNPJ,'\t %.2f' % (lista_empresas[a].Taxa*100),'\t X.XX' ,'\t',lista_empresas[a].Nome,'\t',lista_empresas[a].Semana,'\t',lista_empresas[a].Valor,'\t %.2f' % lista_empresas[a].Desagio,'\t %.2f' % lista_empresas[a].Rebate, '\t %.2f' % lista_empresas[a].Desagio_liq,'\t',lista_empresas[a].Prazo,'\t',lista_empresas[a].Exec)
                desagio_liq += lista_empresas[a].Desagio_liq
                desagio += lista_empresas[a].Desagio
                valor_total += lista_empresas[a].Valor
                valor_realizado += lista_empresas[a].Valor
                desagio_liq_realizado += lista_empresas[a].Desagio_liq
                desagio_realizado += lista_empresas[a].Desagio
                write_csv_row(lista_empresas[a], False)
            else:
                print(lista_empresas[a].CNPJ,'\t %.2f' % (lista_empresas[a].Taxa*100),'\t %.2f' % (LUT_SCORE[lista_empresas[a].Score]*100),'\t',lista_empresas[a].Nome,'\t',lista_empresas[a].Semana,'\t',lista_empresas[a].Valor,'\t %.2f' % lista_empresas[a].Desagio,'\t %.2f' % lista_empresas[a].Rebate,'\t %.2f' % lista_empresas[a].Desagio_liq, '\t',lista_empresas[a].Prazo,'\t',lista_empresas[a].Exec)
                desagio_liq += lista_empresas[a].Desagio_liq
                desagio += lista_empresas[a].Desagio
                valor_total += lista_empresas[a].Valor*taxa_conversao_funil
                write_csv_row(lista_empresas[a], True)

        output.close()

        with open(csv_filename_output, encoding="utf8") as csvFile:
            reader = csv.DictReader(csvFile, delimiter=',')
            table = '<table><tr>{}</tr>'.format(''.join(['<td><td>{}</td></td>'.format(header) for header in reader.fieldnames]))
            for row in reader:
                table_row = '<tr>'
                for fn in reader.fieldnames:
                    table_row += '<td><td>{}</td></td>'.format(row[fn])
                table_row += '</tr>'
                table += table_row
        table += '</table><br>{}</br><br>{}</br><br>{}</br><br>{}</br><br>{}</br><br>{}</br><br>{}</br><br>{}</br>'.format('Valor Total: %.3f'% (valor_total), 'Deságio Liq: %.3f'% (desagio_liq), 'Deságio: %.3f'% (desagio), '\nValor Realizado: %.3f'% (valor_realizado), 'Deságio Liq Realizado: %.3f'% (desagio_liq_realizado), 'Deságio Realizado: %.3f'% (desagio_realizado), 'Deságio Liq em Falta: %.3f'% (desagio_liq - desagio_liq_realizado), ('Deságio em Falta: %.3f'% (desagio - desagio_realizado)))

        return table
        # return redirect('/')
    else:
        flash('Allowed file types are csv')
        # return redirect(request.url)
        return render_template('index.html') 

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.debug = True
    app.run(host='0.0.0.0')