#import required libraries
from datetime import datetime as dt
from dateutil.relativedelta import *
import pandas as pd
import numpy as np
from flask import Flask
from flask_caching import Cache
from collections import OrderedDict
from pandas.tseries.offsets import *
#import pyodbc
import copy
from app import app

import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_table_experiments as dte

#Multi-Dropdown options
from controls import SELLERS, FUNDERS, TXCODES


#Get initial Dataframe to work with
DF = pd.read_pickle('./static/data/Scenario_Modeling_INFO.pkl')
DF_PER = pd.read_pickle('./static/data/Funding_Fee_Percents.pkl')
DF_SPFAVG = pd.read_pickle('./static/data/SPF_AVERAGE.pkl')
DF_EXPVAL = pd.read_pickle('./static/data/ExpectedValues.pkl')

#Setup App
app.config.suppress_callback_exceptions = True
app.css.append_css({"external_url":"../static/dashboard.css"})

CACHE_CONFIG = {
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
}
cache = Cache()
cache.init_app(app.server,config=CACHE_CONFIG)

#Create controls
funder_options = [{'label': str(funder),
                   'value': FUNDERS[funder]}
                  for funder in FUNDERS]
seller_options = [{'label': str(seller),
                   'value': SELLERS[seller]}
                  for seller in SELLERS]
seller_options = sorted(seller_options)

#Calculate probability distribution
P = np.zeros((25,25))
for i in range(1,25):
    dfn = DF.loc[DF.Installments==i]
    for j in range(0,25):
        if i < j:
            pass
        else:
            A = dfn.loc[(dfn.IsCancelled==1)
                        & (dfn.PaymentsMade==j)].shape[0]
            B = dfn.loc[dfn.PaymentsMade>=j].shape[0]
            if B == 0:
                p = 0.0
            else:
                p = A*1.0/B
            P[i][j] = 1-p

layout = dict(
    autosize=True,
    height=260,
    font=dict(color='#000000'),
    titlefont=dict(color='#000000', size='14'),
    #font=dict(color='#CCCCCC'),
    #titlefont=dict(color='#CCCCCC', size='14'),
    margin=dict(
        l=35,
        r=35,
        b=45,
        t=35
    ),
    hovermode='closest',
    #plot_bgcolor='#191A1A',
    #paper_bgcolor="#020202",
    legend=dict(font=dict(size=10), orientation='v'),
    title=''
)

#application layout
layout_page = html.Div([
    dcc.Link('Home Page',href='/'),
    html.Div(
        [
            html.H1('Scenario Tables & Outputs: Admin',
                    style={'textAlign':'center'}),
        ],
    ),

    #Details allows the ability to hide selections
    html.Div([
        html.Details(
            [
                html.Summary(''),
                html.Div([
                    html.Label('Funder'),
                    dcc.Dropdown(
                        id='funder',
                        options=funder_options,
                        placeholder='Select a Funder',
                        multi=True
                    )
                ]),
            ],
            className='three columns',style={'display':'block'}
        ),

        html.Details(
            [
                html.Summary(''),
                html.Div([
                    html.Label('Seller'),
                    dcc.Dropdown(
                        id='seller',
                        options=seller_options,
                        placeholder='Select a Seller',
                        multi=True
                    )
                ]),
            ],
            className='six columns',style={'display':'block'}
        ),

        html.Div(
            [
                html.Label('Contract Fee'),
                    dcc.Input(
                        id = 'fee',
                        type='number',
                        value=50
                    ),
            ],
            className='three columns',style={'display':'block'}
        ),
    ],style={'width':'100%','display':'inline-block'}),

    #First Table
    html.Div([
        html.Div(
            [
                dte.DataTable(
                    id='cohort',
                    rows=[{}],
                    columns=['Installment Terms',
                             'Contracts Sold',
                             '% Contracts Sold',
                             'Cancel Reserve %',
                             'Discount Amt %',
                             'Net Amount',
                             'Loss Ratio'],
                    sortable=False,
                    editable=False,
                    max_rows_in_viewport=7,
                )
            ],
        ),
    ],style={'width':'100%','display':'inline-block','margin':10}),

    #Second Table
    html.Div([
        html.Div(
            [
                dte.DataTable(
                    id='cohortT2',
                    rows=[{}],
                    columns=['Installment Terms',
                             'Cancel Reserve %',
                             'Discount Amt %'],
                    sortable=False,
                    editable=True,
                    max_rows_in_viewport=7
                )
            ],
            className='seven columns'
        ),

        html.Div(
            [
                dte.DataTable(
                    id='cohortT3',
                    rows=[{}],
                    columns=['Net Amount,Contract',
                             'Expected IRR %'],
                    sortable=False,
                    editable=False,
                )
            ],
            className='five columns'
        ),
    ],style={'width':'100%','display':'inline-block'}),

    #Stat Values
    html.Div([
        html.Div(
            [
                html.Div(
                    [
                        dcc.Textarea(
                            id='total_net',
                            value='0',
                            readOnly=True,
                            wrap=True,
                            style={'textAlign': 'center',
                                   'align': 'center',
                                   'fontSize':50,
                                   'color': '#CCCCCC',
                                   'backgroundColor': '#191A1A',
                                   'width': '100%',
                                   'margin':10
                                  }
                        ),
                        html.Label('Cumulative Net Deficit/Surplus',
                            style={'fontSize':15,
                                   'textAlign':'center'}),
                    ],
                    className='four columns'
                ),

                html.Div(
                    [
                        dcc.Textarea(
                            id='total_cancel_rsv',
                            value='0',
                            readOnly=True,
                            wrap=True,
                            style={'textAlign': 'center',
                                   'align': 'center',
                                   'fontSize':50,
                                   'color': '#CCCCCC',
                                   'backgroundColor': '#191A1A',
                                   'width': '100%',
                                   'margin':10
                                  }
                        ),
                        html.Label('Cumulative Cancel Reserve',
                            style={'fontSize':15,
                                   'textAlign':'center'}),
                    ],
                    className='four columns'
                ),

                html.Div(
                    [
                        dcc.Textarea(
                            id='avg_contracts_month',
                            value='0',
                            readOnly=True,
                            wrap=True,
                            style={'textAlign': 'center',
                                   'align': 'center',
                                   'fontSize':50,
                                   'color': '#CCCCCC',
                                   'backgroundColor': '#191A1A',
                                   'width': '100%',
                                   'margin':10
                                  }
                        ),
                        html.Label('Avg. Contracts Sold, Month',
                            style={'fontSize':15,
                                   'textAlign':'center'}),
                    ],
                    className='four columns'
                ),
            ],
        ),
    ],style={'width':'100%','display':'inline-block'}),
    #Third Table
    html.Div([
        html.Div(
            [
                dte.DataTable(
                    id='cohortT4',
                    rows=[{}],
                    columns=['Installment Terms',
                             'Cancel Reserve %',
                             'Discount Amt %',
                             'Contracts,Month'],
                    sortable=False,
                    editable=True,
                    max_rows_in_viewport=7
                )
            ],
            className='seven columns'
        ),

        html.Div(
            [
                dte.DataTable(
                    id='cohortT5',
                    rows=[{}],
                    columns=['Net Amt,Contract',
                             'Accuring Net,Month',
                             'Expected IRR %'],
                    sortable=False,
                    editable=False,
                    max_rows_in_viewport=7
                )
            ],
            className='five columns'
        ),
    ],style={'width':'100%','display':'inline-block'}),
#ending of layout
],style={'margin-left':40,'margin-right':40})

#FUNCTIONS
@cache.memoize()
def getCohort(df,seller,funder):
    dataframe = []
    for vendor in seller:
        for fundee in funder:
            dataframe.append(df.loc[(df.SellerName==vendor) & (df.FundCo==fundee)])
    return pd.concat(dataframe)

def getEPRCohort(df):
    total = 0.0
    for i,row in df.iterrows():
        term = row.Installments
        amt = row.CurrentInstallmentAmount
        paymentsMade = row.PaymentsMade
        total += ExpectedValue(term,paymentsMade,amt,row)
    return round(total)

@cache.memoize()
def getCohortSPFAVG(df,cohort):
    dataframe = df.copy()
    if cohort == '1':
        dataframe = dataframe.loc[dataframe.Installments==1]
    elif cohort == '2-6':
        dataframe = dataframe.loc[(dataframe.Installments>=2) & (dataframe.Installments<=6)]
    elif cohort == '7-12':
        dataframe = dataframe.loc[(dataframe.Installments>=7) & (dataframe.Installments<=12)]
    elif cohort == '13-15':
        dataframe = dataframe.loc[(dataframe.Installments>=13) & (dataframe.Installments<=15)]
    elif cohort == '16-18':
        dataframe = dataframe.loc[(dataframe.Installments>=16) & (dataframe.Installments<=18)]
    elif cohort == '19-24':
        dataframe = dataframe.loc[(dataframe.Installments>=19) & (dataframe.Installments<=24)]
    return dataframe

@cache.memoize()
def getCohortIRR(df,cancelRsv,discountAmt):
    #select cohort installments
    cohort = df.copy()
    cashflows = [0]*24

    #identify what transaction times are and label them as time 0,1,2,3,4...etc.
    #iterrate by rows/contracts
    for i,row in cohort.iterrows():
        term = row.Installments
        paylink_fee = 4.0
        instAmt = row.CurrentInstallmentAmount
        ppAmt = term * instAmt
        paymentsMade = row.PaymentsMade
        for i in range(term):
            if i == 0:
                #initial amount @ t0
                T0 = instAmt - (paylink_fee + ppAmt - discountAmt - cancelRsv)
                cashflows[i] += round(T0,2)
            elif i < paymentsMade:
                #amt received each month from customer, if not cancelled
                T = instAmt - paylink_fee
                cashflows[i] += round(T,2)
            else:
                #if contract is cancelled, last cashflow is returned premium
                cashflows[i] += row.ReturnedPremium
                break
    cashflows = [round(x,2) for x in cashflows]
    #print cashflows
    result = filter(lambda x: x != 0, cashflows)
    return np.irr(result)

@cache.memoize()
#Monthly Sales Volume
def MonthlySales(df,output):
    months = OrderedDict()
    if output == "mean":
        #count how many contracts there are in "month year"
        for date in sorted(df['EffectiveDate']):
            key = date.strftime('%b %y')
            if key in months:
                months[key] +=1
            else:
                months[key] = 1
        return int(np.mean(months.values()).round())
    elif output == 'mean_3months':
        #count how many contracts there are in "month year"
        for date in sorted(df['EffectiveDate']):
            key = date.strftime('%b %y')
            if key in months:
                months[key] +=1
            else:
                months[key] = 1
        return int(np.mean(months.values()[-3:]).round())

#for N = Installment Term Total, j = how much has been paid currently,
#amount = current installment amount
@cache.memoize()
def ExpectedValue(N,j,amount,row):
    """
    value = 0.0
    value2 = 0.0
    n = j-1
    if n % 3 == 0:
        prev_date = (row.LastPaymentDate + BDay(25)).date()
    else:
        prev_date = (row.LastPaymentDate + BDay(20)).date()
    for i in range(j+1,N+1):
        p1 = 1.0
        p2 = 1.0
        for k in range(j+1,i+1):
            p1 = p1 * P[N][k]

            if k != i:
                p2 = p2 * P[N][k]
            elif k == i:
                p2 = p2 * (1-P[N][k])

        #value = value + amount * P[N][i]
        if n % 3 == 0:
            due_date = (prev_date + BDay(25)).date()
        else:
            due_date = (prev_date + BDay(20)).date()
        prev_date = due_date

        #calculate returned premium
        num = (row.TermDays + (row.EffectiveDate - (due_date+relativedelta(days=30))).days)
        den = row.TermDays
        RP = (num/den*row.SellerCost)-50
        #value = value + amount*p1 + RP*p2
        if N-i != 0:
            RP_i = RP*(N-i)/N
        else:
            RP_i = 0.0
        value = value + amount*p1 + RP_i*p2
        #print amount,p1,RP_i,p2, amount*p1 + RP_i*p2
        n += 1
    return value
    """
    return DF_EXPVAL.loc[DF_EXPVAl.PolicyNumber==row.PolicyNumber].ExpectedValue.values[0]
@cache.memoize()
def getTotalNetAmount(df,fee):
    dataframe = df.copy()

    #cohort terms
    term_mix = ['1','2-6','7-12','13-15','16-18','19-24']
    net_amount = 0.0
    for terms in term_mix:
        net_amount = net_amount + getCohortNetAmount(dataframe,fee,terms)
    return net_amount

@cache.memoize()
def getCohortNetAmount(df,fee,cohort):
    dataframe = df.copy()
    if cohort == '1':
        dataframe = dataframe.loc[dataframe.Installments==1]
    elif cohort == '2-6':
        dataframe = dataframe.loc[(dataframe.Installments>=2) & (dataframe.Installments<=6)]
    elif cohort == '7-12':
        dataframe = dataframe.loc[(dataframe.Installments>=7) & (dataframe.Installments<=12)]
    elif cohort == '13-15':
        dataframe = dataframe.loc[(dataframe.Installments>=13) & (dataframe.Installments<=15)]
    elif cohort == '16-18':
        dataframe = dataframe.loc[(dataframe.Installments>=16) & (dataframe.Installments<=18)]
    elif cohort == '19-24':
        dataframe = dataframe.loc[(dataframe.Installments>=19) & (dataframe.Installments<=24)]

    if not dataframe.empty:
        if dataframe.shape[0] >= 75:
            net_amt = round(calcNetHoldback(dataframe,DF_PER,fee,'amount'))
            return net_amt
        else:
            df1 = DF_SPFAVG.loc[DF_SPFAVG['Installment Terms']==cohort]
            N_contracts = dataframe.shape[0]
            net_amt_contract = df1['Net Amount,Contract'].values[0]
            net_amt = round(net_amt_contract * N_contracts)
            return net_amt
    else:
        return 0

@cache.memoize()
def calcNetHoldback(df1,df2,fee,output):
    #all completed, cancelled,open contracts
    holdback = []
    funder = []
    for i,row in df1.iterrows():
        installments = row.PaymentsMade
        funding_fee = row.DiscountAmount
        eff_date = row.EffectiveDate
        vendor = row.SellerName
        installAmt = row.CurrentInstallmentAmount
        term = row.Installments

        if row.CancelDate == None:
            cancel_date = row.LastPaymentDate
        else:
            cancel_date = row.CancelDate

        if row.IsCancelled == 1:
            rate = df2.loc[(df2['SunPathAccountingCode']==TXCODES[vendor][1])
                       & (df2['Installments']==installments)].CancelPercentage
        else:
            rate = 0.0

        day_utilized = (cancel_date-eff_date).days

        VUR = day_utilized/row.TermDays
        prorated_fee = float(rate * funding_fee)
        payment_plan_amount = installAmt * term
        cancel_reserve = row.CancelReserveAmount
        total_install_rec = installAmt * installments
        Amt_Owed_SPF = (1-VUR)*row.AdminPortionAmt-fee
        Amt_Owed_INS = (1-VUR)*row.InsReservePortionAmt
        deficit = cancel_reserve - payment_plan_amount + Amt_Owed_SPF + Amt_Owed_INS + funding_fee - prorated_fee + total_install_rec

        #if specific contract either cancelled, completed, or open
        if row.IsCancelled == 1 or row.PaymentsRemaining == 0:
            deficit = deficit + row.ReturnedPremium
        elif row.IsCancelled == 0 and row.PaymentsRemaining != 0:
            deficit = deficit + ExpectedValue(term,installments,installAmt,row)
        holdback.append(deficit)

    if output=='amount':
        return np.sum(holdback).round()

@cache.memoize()
def calcNetHoldbackPerContract(df1,df2,fee,output,cancel_reserve,discount_amt):
    #all completed, cancelled contracts
    #Find Owed To Funder = Gross Capital + HldbckRsv + Porated Funding Fee - Total Installs Received
    holdback = []
    funder = []
    print df1.shape
    count = 0
    for i,row in df1.iterrows():
        installments = row.PaymentsMade
        eff_date = row.EffectiveDate
        vendor = row.SellerName
        installAmt = row.CurrentInstallmentAmount
        term = row.Installments
        if row.CancelDate == None:
            cancel_date = row.LastPaymentDate
        else:
            cancel_date = row.CancelDate

        if row.IsCancelled == 1:
            rate = df2.loc[(df2['SunPathAccountingCode']==TXCODES[vendor][1])
                        & (df2['Installments']==installments)].CancelPercentage
        else:
            rate = 0.0

        day_utilized = (cancel_date-eff_date).days

        VUR = day_utilized/row.TermDays
        prorated_fee = float(rate * discount_amt)
        payment_plan_amount = installAmt * term
        total_install_rec = installAmt * installments
        Amt_Owed_SPF = (1-VUR)*row.AdminPortionAmt-fee
        Amt_Owed_INS = (1-VUR)*row.InsReservePortionAmt
        deficit = cancel_reserve - payment_plan_amount + Amt_Owed_SPF + Amt_Owed_INS + discount_amt - prorated_fee +total_install_rec

        #if specific contract either cancelled, completed, or open
        if row.IsCancelled == 1 or row.PaymentsRemaining == 0:
            deficit = deficit + row.ReturnedPremium
        elif row.IsCancelled == 0 and row.PaymentsRemaining != 0:
            deficit = deficit + ExpectedValue(term,installments,installAmt,row)
        holdback.append(deficit)

    if output=='amount':
        return np.sum(holdback).round()

@cache.memoize()
def buildCohortTable(df,fee):
    dataframe = df.copy()

    #cohort terms
    term_mix = ['1','2-6','7-12','13-15','16-18','19-24']
    table = []
    for terms in term_mix:
        table.append(getCohortRowStats(dataframe,fee,terms))
    columns = ['Installment Terms','Contracts Sold',
               '% Contracts Sold','Cancel Reserve %',
               'Discount Amt %','Net Amount','Loss Ratio']
    total_holdback = dataframe.CancelReserveAmount.sum()
    openDF = dataframe.loc[(dataframe.PaymentsRemaining!=0) & (dataframe.IsCancelled==0)]
    epr = getEPRCohort(openDF)
    apr = (dataframe.CurrentInstallmentAmount * dataframe.PaymentsMade).sum().round()
    loss_ratio = (apr+epr)/total_holdback
    result = pd.DataFrame(table,columns=columns)
    totals = pd.DataFrame([('Total',result['Contracts Sold'].sum(),result['% Contracts Sold'].sum(),
    round(result['Cancel Reserve %'].mean(),2),round(result['Discount Amt %'].mean(),2),
    round(result['Net Amount'].sum()),round(loss_ratio,2))],columns=columns)
    final_result = result.append(totals)
    return final_result

@cache.memoize()
def buildCohortTable2(df,fee):
    dataframe = df.copy()

    #cohort terms
    term_mix = ['1','2-6','7-12','13-15','16-18','19-24']
    table = []
    for terms in term_mix:
        table.append(getCohortRowStats2(dataframe,fee,terms))
    columns = ['Installment Terms','Cancel Reserve %','Discount Amt %']
    result = pd.DataFrame(table,columns=columns)
    return result

@cache.memoize()
def getCohortRowStats(df,fee,cohort):
    dataframe = df.copy()
    if cohort == '1':
        dataframe = dataframe.loc[dataframe.Installments==1]
    elif cohort == '2-6':
        dataframe = dataframe.loc[(dataframe.Installments>=2) & (dataframe.Installments<=6)]
    elif cohort == '7-12':
        dataframe = dataframe.loc[(dataframe.Installments>=7) & (dataframe.Installments<=12)]
    elif cohort == '13-15':
        dataframe = dataframe.loc[(dataframe.Installments>=13) & (dataframe.Installments<=15)]
    elif cohort == '16-18':
        dataframe = dataframe.loc[(dataframe.Installments>=16) & (dataframe.Installments<=18)]
    elif cohort == '19-24':
        dataframe = dataframe.loc[(dataframe.Installments>=19) & (dataframe.Installments<=24)]

    #print dataframe.shape[0]
    if not dataframe.empty:
        D = dataframe.DiscountAmount.mean()
        S = dataframe.SellerAdvanceAmount.mean()
        total_holdback = dataframe.CancelReserveAmount.sum()
        openDF = dataframe.loc[(dataframe.PaymentsRemaining!=0) & (dataframe.IsCancelled==0)]
        epr = getEPRCohort(openDF)
        apr = (dataframe.CurrentInstallmentAmount * dataframe.PaymentsMade).sum().round()
        loss_ratio = round((apr+epr)/total_holdback,2)
        if dataframe.shape[0] >= 75:
            H = dataframe.CancelReserveAmount.mean()
            Z1 = (D/(H+S))*100
            Z2 = (H/(H+S))*100

            #values for row
            total = df.shape[0]
            N_contracts = dataframe.shape[0]
            contract_percent_sold = round(N_contracts*1.0/total*100,3)
            cancel_rsv = round(Z2,2)
            discount_amt = round(Z1,2)
            net_amt = calcNetHoldback(dataframe,DF_PER,fee,'amount')
            row = (cohort,N_contracts,contract_percent_sold,cancel_rsv,discount_amt,net_amt,loss_ratio)
            return row
        else:
            df1 = DF_SPFAVG.loc[DF_SPFAVG['Installment Terms']==cohort]
            H = df1['Cancel Reserve'].values[0]
            #values for rows
            total = df.shape[0]
            N_contracts = dataframe.shape[0]
            contract_percent_sold = round(N_contracts*1.0/total*100,3)
            cancel_rsv = df1['Cancel Reserve %'].values[0]
            discount_amt =  round((D/(H+S))*100,2)
            net_amt_contract = df1['Net Amount,Contract'].values[0]
            net_amt = round(net_amt_contract * N_contracts)
            row = (cohort,N_contracts,contract_percent_sold,cancel_rsv,discount_amt,net_amt,loss_ratio)
            return row
    else:
        return (cohort,0,0,0,0,0)

@cache.memoize()
def getCohortRowStats2(df,fee,cohort):
    dataframe = df.copy()
    if cohort == '1':
        dataframe = dataframe.loc[dataframe.Installments==1]
    elif cohort == '2-6':
        dataframe = dataframe.loc[(dataframe.Installments>=2) & (dataframe.Installments<=6)]
    elif cohort == '7-12':
        dataframe = dataframe.loc[(dataframe.Installments>=7) & (dataframe.Installments<=12)]
    elif cohort == '13-15':
        dataframe = dataframe.loc[(dataframe.Installments>=13) & (dataframe.Installments<=15)]
    elif cohort == '16-18':
        dataframe = dataframe.loc[(dataframe.Installments>=16) & (dataframe.Installments<=18)]
    elif cohort == '19-24':
        dataframe = dataframe.loc[(dataframe.Installments>=19) & (dataframe.Installments<=24)]

    if not dataframe.empty:
        D = dataframe.DiscountAmount.mean()
        S = dataframe.SellerAdvanceAmount.mean()
        if dataframe.shape[0] >= 75:
            H = dataframe.CancelReserveAmount.mean()
            Z1 = (D/(H+S))*100
            Z2 = (H/(H+S))*100

            #values for row
            cancel_rsv = round(Z2,2)
            discount_amt = round(Z1,2)
            row = (cohort,cancel_rsv,discount_amt)
            return row
        else:
            df1 = DF_SPFAVG.loc[DF_SPFAVG['Installment Terms']==cohort]
            H = df1['Cancel Reserve'].values[0]
            #values for rows
            cancel_rsv = df1['Cancel Reserve %'].values[0]
            discount_amt = round((D/(H+S))*100,2)
            row = (cohort,cancel_rsv,discount_amt)
            return row
    else:
        return (cohort,0.0,0.0)

@cache.memoize()
def getContracts(df,fee,cohort):
    dataframe = df.copy()
    if cohort == '1':
        dataframe = dataframe.loc[dataframe.Installments==1]
    elif cohort == '2-6':
        dataframe = dataframe.loc[(dataframe.Installments>=2) & (dataframe.Installments<=6)]
    elif cohort == '7-12':
        dataframe = dataframe.loc[(dataframe.Installments>=7) & (dataframe.Installments<=12)]
    elif cohort == '13-15':
        dataframe = dataframe.loc[(dataframe.Installments>=13) & (dataframe.Installments<=15)]
    elif cohort == '16-18':
        dataframe = dataframe.loc[(dataframe.Installments>=16) & (dataframe.Installments<=18)]
    elif cohort == '19-24':
        dataframe = dataframe.loc[(dataframe.Installments>=19) & (dataframe.Installments<=24)]


    if not dataframe.empty:
        AF = dataframe.AmountFinanced.mean()
        D = dataframe.DiscountAmount.mean()
        S = dataframe.SellerAdvanceAmount.mean()
        if dataframe.shape[0] >= 75:
            H = dataframe.CancelReserveAmount.mean()
            Z1 = (H/(H+S))
            Z2 = (D/(H+S))
            Z = Z1/AF*(H+S) + Z2/AF*(H+S)
            net_amt = calcNetHoldback(dataframe,DF_PER,fee,'amount')
            #print net_amt, Z*AF
            N = (abs(net_amt)/(Z*AF)/12).round()

            #values for row
            cancel_rsv = round(Z1*100.0,2)
            discount_amt = round(Z2*100.0,2)
            row = (cohort,cancel_rsv,discount_amt,N)
            return row
        else:
            df1 = DF_SPFAVG.loc[DF_SPFAVG['Installment Terms']==cohort]

            #values for rows
            total = df.shape[0]
            N_contracts = dataframe.shape[0]
            contract_percent_sold = round(N_contracts*1.0/total*100,3)
            H = df1['Cancel Reserve'].values[0]
            cancel_rsv = df1['Cancel Reserve %'].values[0]
            discount_amt = round((D/(H+S))*100,2)
            net_amt_contract = df1['Net Amount,Contract'].values[0]
            net_amt = round(net_amt_contract * N_contracts)
            N = (abs(net_amt)/(D+H)/12).round()
            row = (cohort,cancel_rsv,discount_amt,N)
            return row
    else:
        return (cohort,0.0,0.0,0)

@cache.memoize()
def buildCohortTableOutput2(df,fee):
    dataframe = df.copy()
    term_mix = ['1','2-6','7-12','13-15','16-18','19-24']
    table = []
    table2 = []
    for terms in term_mix:
        table.append(getContracts(dataframe,fee,terms))
    columns = ['Installment Terms','Cancel Reserve %','Discount Amt %','Contracts,Month']
    result = pd.DataFrame(table,columns=columns)
    return result

@cache.memoize()
def getOutput(df,dff,fee):
    table = []
    for i,row in dff.iterrows():
        dataframe = df.copy()
        cohort = row["Installment Terms"]

        if cohort == '1':
            dataframe = dataframe.loc[dataframe.Installments==1]
        elif cohort == '2-6':
            dataframe = dataframe.loc[(dataframe.Installments>=2) & (dataframe.Installments<=6)]
        elif cohort == '7-12':
            dataframe = dataframe.loc[(dataframe.Installments>=7) & (dataframe.Installments<=12)]
        elif cohort == '13-15':
            dataframe = dataframe.loc[(dataframe.Installments>=13) & (dataframe.Installments<=15)]
        elif cohort == '16-18':
            dataframe = dataframe.loc[(dataframe.Installments>=16) & (dataframe.Installments<=18)]
        elif cohort == '19-24':
            dataframe = dataframe.loc[(dataframe.Installments>=19) & (dataframe.Installments<=24)]

        N_contracts = dataframe.shape[0]
        D = row['Discount Amt %']
        H = row['Cancel Reserve %']
        if (float(H) == 0) and (float(D) == 0):
            net_per_contract = 0
            irr = np.nan
        else:
            if N_contracts < 75:
                df1 = DF_SPFAVG.loc[DF_SPFAVG['Installment Terms']==cohort]
                const = df1['Seller Advance'].values[0] + df1['Cancel Reserve'].values[0]
                cohortDF = getCohortSPFAVG(DF,cohort)
                D = round(float(D)*const/100.0,2)
                H = round(float(H)*const/100.0,2)
                net_amt = calcNetHoldbackPerContract(cohortDF,DF_PER,fee,'amount',H,D)
                net_per_contract = round(net_amt/cohortDF.shape[0])
                irr = round(getCohortIRR(cohortDF,H,D)*100,2)
            else:
                const = dataframe.CancelReserveAmount.mean() + dataframe.SellerAdvanceAmount.mean()
                D = round(float(D)*const/100.0,2)
                H = round(float(H)*const/100.0,2)
                net_amt = calcNetHoldbackPerContract(dataframe,DF_PER,fee,'amount',H,D)
                net_per_contract = round(net_amt/N_contracts)
                irr = round(getCohortIRR(dataframe,H,D)*100,2)
        table.append((cohort,net_per_contract,irr))
    return pd.DataFrame(table,columns=['Installment Terms','Net Amount,Contract','Expected IRR %'])

@cache.memoize()
def getOutput2(df,dff,fee):
    table = []
    for i,row in dff.iterrows():
        dataframe = df.copy()
        cohort = row["Installment Terms"]
        if cohort == '1':
            dataframe = dataframe.loc[dataframe.Installments==1]
        elif cohort == '2-6':
            dataframe = dataframe.loc[(dataframe.Installments>=2) & (dataframe.Installments<=6)]
        elif cohort == '7-12':
            dataframe = dataframe.loc[(dataframe.Installments>=7) & (dataframe.Installments<=12)]
        elif cohort == '13-15':
            dataframe = dataframe.loc[(dataframe.Installments>=13) & (dataframe.Installments<=15)]
        elif cohort == '16-18':
            dataframe = dataframe.loc[(dataframe.Installments>=16) & (dataframe.Installments<=18)]
        elif cohort == '19-24':
            dataframe = dataframe.loc[(dataframe.Installments>=19) & (dataframe.Installments<=24)]

        N_contracts = dataframe.shape[0]
        D = row['Discount Amt %']
        H = row['Cancel Reserve %']
        N = row['Contracts,Month']
        if (float(H) == 0) and (float(D) == 0):
            net_per_contract = 0
            accuring = int(N) * net_per_contract
            irr = np.nan
        else:
            if N_contracts < 75:
                df1 = DF_SPFAVG.loc[DF_SPFAVG['Installment Terms']==cohort]
                const = df1['Seller Advance'].values[0] + df1['Cancel Reserve'].values[0]
                cohortDF = getCohortSPFAVG(DF,cohort)
                D = round(float(D)*const/100.0,2)
                H = round(float(H)*const/100.0,2)
                net_amt = calcNetHoldbackPerContract(cohortDF,DF_PER,fee,'amount',H,D)
                net_per_contract = round(net_amt/cohortDF.shape[0])
                irr = round(getCohortIRR(cohortDF,H,D)*100,2)
            else:
                const = dataframe.CancelReserveAmount.mean() + dataframe.SellerAdvanceAmount.mean()
                D = round(float(D)*const/100.0,2)
                H = round(float(H)*const/100.0,2)
                net_amt = calcNetHoldbackPerContract(dataframe,DF_PER,fee,'amount',H,D)
                net_per_contract = round(net_amt/N_contracts)
                irr = round(getCohortIRR(dataframe,H,D)*100,2)
            accuring = round(int(N) * net_per_contract)
        table.append((cohort,net_per_contract,accuring,irr))
    return pd.DataFrame(table,columns=['Installment Terms','Net Amt,Contract','Accuring Net,Month','Expected IRR %'])

#callbacks to update values in layout 2
@app.callback(Output('total_net','value'),
             [Input('funder','value'),
              Input('seller','value'),
              Input('fee','value')])
def update_NetDeficit(funder,seller,fee):
    if ((funder is not None) and (seller is not None)):
        dataframe = getCohort(DF,seller,funder)
        hldbckAmt = getTotalNetAmount(dataframe,fee)
        if hldbckAmt < 0:
            amount = '-${:,.0f}'.format(abs(hldbckAmt))
        else:
            amount = '${:,.0f}'.format(abs(hldbckAmt))
        return '%s' % amount

#callbacks to update values in layout 2
@app.callback(Output('total_cancel_rsv','value'),
             [Input('funder','value'),
              Input('seller','value')])
def update_NetCancelRsv(funder,seller):
    if ((funder is not None) and (seller is not None)):
        dataframe = getCohort(DF,seller,funder)
        total_crsv = dataframe.CancelReserveAmount.sum().round()
        total = '${:,.0f}'.format(total_crsv)
        return '%s' % total

@app.callback(Output('avg_contracts_month','value'),
               [Input('funder','value'),
               Input('seller','value')])
def update_AvgContracts(funder,seller):
    if ((funder is not None) and (seller is not None)):
        dataframe = getCohort(DF,seller,funder)
        return MonthlySales(dataframe,'mean')

@app.callback(Output('cohort','rows'),
             [Input('funder','value'),
              Input('seller','value'),
              Input('fee','value')])
def update_CohortTable(funder,seller,fee):
    if ((funder is not None) and (seller is not None)):
        #core dataframe
        dataframe = getCohort(DF,seller,funder)
        final_result = buildCohortTable(dataframe,fee)
        return final_result.to_dict('records',into=OrderedDict)

@app.callback(Output('cohortT2','rows'),
             [Input('funder','value'),
              Input('seller','value'),
              Input('fee','value')])
def update_CohortTable2(funder,seller,fee):
    if ((funder is not None) and (seller is not None)):
        #core dataframe
        dataframe = getCohort(DF,seller,funder)
        result = buildCohortTable2(dataframe,fee)
        columns = ['Installment Terms','Cancel Reserve %','Discount Amt %']
        return result[columns].to_dict('records',into=OrderedDict)

@app.callback(Output('cohortT3','rows'),
             [Input('funder','value'),
              Input('seller','value'),
              Input('fee','value'),
              Input('cohortT2','rows')])
def update_CohortTable3(funder,seller,fee,rows):
    if ((funder is not None) and (seller is not None)):
        #core dataframe
        dff = pd.DataFrame(rows)
        dataframe = getCohort(DF,seller,funder)
        result = getOutput(dataframe,dff,fee)
        return result.to_dict('records',into=OrderedDict)
    else:
        return pd.DataFrame().to_dict('records')

@app.callback(Output('cohortT4','rows'),
             [Input('funder','value'),
              Input('seller','value'),
              Input('fee','value')])
def update_CohortTable4(funder,seller,fee):
    if ((funder is not None) and (seller is not None)):
        #core dataframe
        dataframe = getCohort(DF,seller,funder)

        result = buildCohortTableOutput2(dataframe,fee)
        return result.to_dict('records',into=OrderedDict)

@app.callback(Output('cohortT5','rows'),
             [Input('funder','value'),
              Input('seller','value'),
              Input('fee','value'),
              Input('cohortT4','rows')])
def update_CohortTable5(funder,seller,fee,rows):
    if ((funder is not None) and (seller is not None)):
        #core dataframe
        dff = pd.DataFrame(rows)
        dataframe = getCohort(DF,seller,funder)
        result = getOutput2(dataframe,dff,fee)
        return result.to_dict('records',into=OrderedDict)
    else:
        return pd.DataFrame().to_dict('records')
