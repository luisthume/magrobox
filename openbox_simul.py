#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
=========================================================
OpenBox Simulador
=========================================================
"""

import numpy as np
import pandas as pd

import sys

#DEFINES
#taxa_capital = 0.01 # a. m.
#taxa_rentabilidade_media = 0.05 # a. m.
spread = 0.02 # a.m.

LUT_SCORE = np.zeros(100,dtype=float)  		

def calculate_LUT_SCORE(taxa_rentabilidade_media_local):
	for a in range(100):          
		LUT_SCORE[100 - a - 1] = taxa_rentabilidade_media_local*0.01*a + (taxa_rentabilidade_media_local - spread)
		#print(LUT_SCORE[100 - a - 1])

#calculate_LUT_SCORE(0.045)

csv_filename = '/openbox_forecast_input.csv' 

def load_csv(csv_file):
	pass

csv_filename = load_csv()

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

#print(target_operacao, taxa_rentabilidade_media)
target_desagio = target_operacao*taxa_rentabilidade_media


p1 = pd.read_csv(csvpath, engine='python', sep=',', decimal=".", error_bad_lines=False, skiprows=3)
p1 = p1.replace(np.nan,0, regex=True)

#print(p1)
#exit()

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

	#print('\n')
	#print('Desagio Total: %.3f'%desagio)		
	#print('Prazo Medio: %.3f'%(prazo_medio*30/count))		
	#print('Total_operado: %.3f'%total_operado)		
	#print('Taxa Final: %.3f'% (desagio / total_operado))

	return	(desagio / total_operado), desagio, total_operado, prazo_medio/count, desagio_liq

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


	return	(desagio / total_operado), desagio, total_operado

valor_total = 0
for a in range(len(lista_empresas)):	
	valor_total += lista_empresas[a].Valor

#print(target_operacao,valor_total)

taxa_conversao_funil = (target_operacao/valor_total)

tax = 0.01
taxa_final = desagio_liq = 0

while desagio_liq < target_desagio:
	calculate_LUT_SCORE(tax)
	taxa_final, desagio_final, valor_total_convertido, prazo_medio, desagio_liq = calculate_total_tax_full(lista_empresas, taxa_conversao_funil)
	#print(taxa_final, desagio_final, valor_total)	
	tax += 0.0001

print('\nValor do funil: %.3f'% (valor_total))
print('Deságio do funil: %.3f'% (desagio_liq/taxa_conversao_funil))

print('\nPrazo medio: %.3f'% (prazo_medio*30))
print('Desagio liq: %.3f'% (desagio_liq))

print('\nValor alvo: %.3f'% (target_operacao))
print('Deságio alvo: %.3f'% (target_desagio))
print('\nTaxa Final Desejada: %.3f'% (100*target_desagio/target_operacao))
print('Taxa de Conversao do funil: %.2f' % taxa_conversao_funil)
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
	output.write(str(empresa.Taxa))
	output.write(',')
	if use_LUT_SCORE:
		output.write(str(LUT_SCORE[lista_empresas[a].Score]))
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

print('\nValor Total: %.3f'% (valor_total))
print('Deságio Liq: %.3f'% (desagio_liq))
print('Deságio: %.3f'% (desagio))
print('\nValor Realizado: %.3f'% (valor_realizado))
print('Deságio Liq Realizado: %.3f'% (desagio_liq_realizado))
print('Deságio Realizado: %.3f'% (desagio_realizado))

print('\nDeságio Liq em Falta: %.3f'% (desagio_liq - desagio_liq_realizado))
print('Deságio em Falta: %.3f'% (desagio - desagio_realizado))

def __init__(self):
	return "Teste"