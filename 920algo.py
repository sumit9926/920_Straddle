"""
Author = RustAlgo

Basic Code Created in an Hour purely for Education, Not for Trading Using Real Money
You are Solely and wholly Responsible for Your Loss, Author is Not Responsible for Any of Your Losses

For Morea details refer README.md

"""

import datetime
import time
import requests
import pandas as pd
from dhanhq import dhanhq
import os
from nsepython import *
import dhancred
import json


dhan= dhanhq(client_id=dhancred.client_id(),access_token=dhancred.access_token())
print(f"Session to Broker Dhan Established at {datetime.datetime.now()}")

## Lot Size and SL Points ##########

Qty= 50
SL= 30
############################################################################################
underlying = "NIFTY"
nearestexpiry= expiry_list(underlying)
expiry= nearestexpiry[0]
print(f'Selected Expiry is {expiry}')

##############################################################################################

# Downloading Scrip Master of Dhan
security_idsource = "https://images.dhan.co/api-data/api-scrip-master.csv"

todays_date= datetime.datetime.now().strftime("%Y-%m-%d")

file_name= f'api-scrip-master.csv'

response = requests.get(security_idsource)
with open(file_name, "wb") as f:
    f.write(response.content)
    print(f"Scrip Master '{file_name}' downloaded successfully.")

#Created a Pandas Data Frame for Placing Orders
required_cols = ['SEM_EXM_EXCH_ID','SEM_SMST_SECURITY_ID','SEM_INSTRUMENT_NAME','SEM_TRADING_SYMBOL','SEM_CUSTOM_SYMBOL','SEM_EXPIRY_DATE','SEM_EXPIRY_FLAG']
master= pd.read_csv("api-scrip-master.csv",usecols=required_cols)

#############################################################################################

while True:
    current_time = datetime.datetime.now().time()
    if current_time >= datetime.time(9, 20, 00):  #9,20,30
        print(f"It is now {datetime.datetime.now()}. Continuing...")
        break
    else:
        print(f"It is currently {current_time}. Waiting for 9:20:30 AM...")
        time.sleep(1) # sleep for 1 second before checking at 9:20:30 AM

###############################################################################

ltp= (nse_quote_ltp(underlying))
print(f'LTP of {underlying} is {ltp}')
ATM = round(ltp/50)*50
print(f'At The Money Strike Of Underlying {underlying} is {ATM}')
expiry_date_string = expiry
expiry_date = datetime.datetime.strptime(expiry_date_string, '%d-%b-%Y')
year = expiry_date.year
month = expiry_date.strftime('%b').upper()
day = expiry_date.day

atmCE= f'NIFTY {day} {month} {ATM} CALL'

atmPE= f'NIFTY {day} {month} {ATM} PUT'

print(f"At The Money Call Strike is {atmCE}, At The Money Put Strike is {atmPE}")

LTPofCE= float(nse_quote_ltp(underlying,"latest","CE",ATM))
print(f'Call is Now Trading at {LTPofCE}')

LTPofPE= float(nse_quote_ltp(underlying,"latest","PE",ATM))
print(f'Put is Now Trading at {LTPofPE}')

# Saving SL as LTP of CE and PE Minus SL as defined earlier Before placing order

ce_entry_price= float(LTPofCE)
pe_entry_price= float(LTPofPE)

ceSL= float(round(LTPofCE-SL,1))
peSL= float(round(LTPofPE-SL,1))


#Getting Security ID for ATM CE and PE
securityidCE = master.loc[master['SEM_CUSTOM_SYMBOL'] == atmCE, 'SEM_SMST_SECURITY_ID'].iloc[0]
securityidPE = master.loc[master['SEM_CUSTOM_SYMBOL'] == atmPE, 'SEM_SMST_SECURITY_ID'].iloc[0]

print(f'Retrieved Security Id of Boker for CE is {securityidCE}')
print(f'Retrieved Security Id of Boker for PE is {securityidPE}')

print(f'placing Market Orders for {atmCE} and {atmPE}')

########################################################################################

dhan.place_order(security_id=str(securityidCE),
    exchange_segment=dhan.FNO,
    transaction_type=dhan.SELL,
    quantity=Qty,
    order_type=dhan.MARKET,
    product_type=dhan.INTRA,
    price=0)
print(f'Market Order Placed for {atmCE}')

dhan.place_order(security_id=str(securityidPE),  
    exchange_segment=dhan.FNO,
    transaction_type=dhan.SELL,
    quantity=Qty,
    order_type=dhan.MARKET,
    product_type=dhan.INTRA,
    price=0)
print(f'Market Order Placed for {atmPE}')

################################################################################
print(f"CEentryprice is {ce_entry_price}")
print(f"PEentryprice is {pe_entry_price}")
print(f"CESL is now {ceSL}")
print(f"PESL is now {peSL}")

###############################################################################

print("All Positions are Punched, Wating for SL")

traded = "No"
while traded == "No":
    dt=datetime.datetime.now()
    try:
        LTPofCE=nse_quote_ltp(underlying,"latest","CE",ATM)
        LTPofPE=nse_quote_ltp(underlying,"latest","PE",ATM)
        print("Inside Exit: Checking CE:",LTPofCE," and PE:",LTPofPE)
        if ((LTPofCE > ceSL) or (dt.hour >= 15 and dt.minute >= 15)):
            exitCE= dhan.place_order(security_id=str(securityidCE),  exchange_segment=dhan.FNO,transaction_type=dhan.BUY,quantity=Qty,order_type=dhan.MARKET,product_type=dhan.INTRA,price=0)
            traded = "CE"
            print("PE SL Hit or Market is About to be closed")
            time.sleep(5)
        elif((LTPofPE > peSL) or (dt.hour >= 15 and dt.minute >= 15)):

            exitPE= dhan.place_order(security_id=str(securityidPE),  exchange_segment=dhan.FNO,transaction_type=dhan.BUY,quantity=Qty,order_type=dhan.MARKET,product_type=dhan.INTRA,price=0)
            traded = "PE"
            print("Exiting PE Leg")
            time.sleep(5)
        else:
            print("No SL is Hit")
            time.sleep(5)
            
    except:
        print("Couldn't find LTP , RETRYING !!")
        time.sleep(5)
        
    if(traded=="CE"):
        peSL = pe_entry_price
        while traded == "CE":
            dt= datetime.datetime.now()
            try:
                LTPofPE=nse_quote_ltp(underlying,"latest","PE",ATM)
                if ((ltp > peSL) or (dt.hour >= 15 and dt.minute >= 15)):
                    exitPE= dhan.place_order(security_id=str(securityidPE),  exchange_segment=dhan.FNO,transaction_type=dhan.BUY,quantity=Qty,order_type=dhan.MARKET,product_type=dhan.INTRA,price=0)
                    traded = "Close"
                    print("PE SL Hit or Market is About to be closed")
                    time.sleep(5)
                else:
                    print("PE SL not hit")
                    time.sleep(1)
                  
            except:
                print("Couldn't find LTP , RETRYING !!")
                time.sleep(1)

    elif(traded == "PE"):
        ceSL = ce_entry_price
        while traded == "PE":
            dt = datetime.datetime.now()
            try:
                LTPofCE=nse_quote_ltp(underlying,"latest","CE",ATM)
                if ((ltp > ceSL) or (dt.hour >= 15 and dt.minute >= 15)):
                    exitCE= dhan.place_order(security_id=str(securityidCE),  exchange_segment=dhan.FNO,transaction_type=dhan.BUY,quantity=Qty,order_type=dhan.MARKET,product_type=dhan.INTRA,price=0)
                    traded = "Close"
                    time.sleep(5)
                    
                else:
                    print("CE SL not hit")
                    time.sleep(5)
            except:
                print("Couldn't find LTP , RETRYING !!")
                time.sleep(1)
    elif (traded == "Close"):
        print("All trades done. Exiting Code")
        