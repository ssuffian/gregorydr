from flask import Flask, send_file, make_response, request
from datetime import datetime,timedelta
from luzero import psql
import pandas as pd
from sqlalchemy import cast,Date,text
import logging
import json
from logging.handlers import RotatingFileHandler
app = Flask(__name__)

@app.route("/clear")
def clear_limit_value():
    try:
       
        output_dict = {}
        metadata = psql.get_metadata()
        table_dict = psql.setup_tables(metadata)
        psql.add_values_to_table(table_dict['clear_table'],output_dict)
    except Exception , e :
        out = 'Set Failed.\n'
        out += str(request.args)
        out += str(e)
    
        return make_response(out, 404)
    return json.dumps({"status:":"Successfully reset limit counter."})

@app.route("/get_limit")
def get_limit():
    try:
        output_dict = {}
        metadata = psql.get_metadata()
        table_dict = psql.setup_tables(metadata)
        result = table_dict['limit_table'].select().\
        order_by(table_dict['limit_table'].c.datetime.desc()).execute().fetchone()
        if result is not None:
            limit_val = result[2]
        else:
            limit_val = 150
    except Exception , e :
        out = 'Set Failed.\n'
        out += str(request.args)
        out += str(e)
    
        return make_response(out, 404)
    return json.dumps({"limit:":limit_val})

@app.route("/get_limit_value")
def get_limit_value():
    try:
        output_dict = {}
        metadata = psql.get_metadata()
        table_dict = psql.setup_tables(metadata)
        last_clear = table_dict['clear_table'].select().\
        order_by(table_dict['clear_table'].c.datetime.desc()).execute().fetchone()
        print last_clear
        if last_clear is not None:
            result = table_dict['zwave_table'].select().where(cast(table_dict['zwave_table'].c.datetime,Date)>=last_clear[1]).\
            order_by(table_dict['zwave_table'].c.datetime.asc()).execute()
        else:
            result = table_dict['zwave_table'].select().\
            order_by(table_dict['zwave_table'].c.datetime.asc()).execute()
        columns = result.keys()
        values = result.fetchall()
        df = pd.DataFrame(values,columns=columns)
        if len(df)>0:
            limit_value = df[-1:]['houseAll_Energy'].values[0]-df[:1]['houseAll_Energy'].values[0]
        else:
            limit_value = 0
    except Exception , e :
        out = 'Set Failed.\n'
        out += str(request.args)
        out += str(e)
    
        return make_response(out, 404)
    return json.dumps({"value:":limit_value})

@app.route("/set_limit")
def set_limit():
    try:
        limit = request.args.get('limit')
        output_dict = {}
        output_dict['limit'] = int(limit)
        metadata = psql.get_metadata()
        table_dict = psql.setup_tables(metadata)
        psql.add_values_to_table(table_dict['limit_table'],output_dict)
    except Exception , e :
        out = 'Set Failed.\n'
        out += str(request.args)
        out += str(e)
    
        return make_response(out, 404)
    return json.dumps({"status:":"Successfully set limit to "+limit})

@app.route("/get_days")
def get_days():
    try:
        weekday_letters = ['Lu','Mar','Mi','Ju','Vi','Sa','Do']
        output_dict = {}
        output = []
        metadata = psql.get_metadata()
        table_dict = psql.setup_tables(metadata)
        weekday_num = days=datetime.now().weekday()
        last_date=datetime.now() - timedelta(weekday_num)
        last_date = datetime(last_date.year,last_date.month,last_date.day)
        result = table_dict['zwave_table'].select().where(cast(table_dict['zwave_table'].c.datetime,Date)>=last_date).\
        order_by(table_dict['zwave_table'].c.datetime.asc()).execute()
        columns = result.keys()
        values = result.fetchall()

        df = pd.DataFrame(values,columns=columns)
        df = df.set_index('datetime')
        df = df[df['houseAll_Energy']>0]
        #df = fix_zwave_values(df)
        pos_lim = df['houseAll_Energy'].diff().mean()+3*df['houseAll_Energy'].diff().std()
        neg_lim = df['houseAll_Energy'].diff().mean()-3*df['houseAll_Energy'].diff().std()
        #df = df[df['houseAll_Energy'].diff()<pos_lim]
        #df = df[df['houseAll_Energy'].diff()>0]
        for day in range(0,7):
            
            output_dict = {}
            output_dict['Letter'] = weekday_letters[day]
            output_dict['Val'] = 0
            if len(df)>0:
                day_num_points = len(df[df.index.weekday==day])
                if day_num_points>0:
                    day_diff = df[df.index.weekday==day]['houseAll_Energy'].iloc[day_num_points-1] - \
                    df[df.index.weekday==day]['houseAll_Energy'].iloc[0]
                    output_dict['Val'] = day_diff
            output.append(output_dict)
      
    except Exception , e :
        out = 'Query Failed.\n'
        out += str(request.args)
        out += str(e)
    
        return make_response(out, 404)
    
    return json.dumps(output)

@app.route("/get_hours")
def get_hours():
    try:
        output_dict = {}
        output = []
        metadata = psql.get_metadata()
        table_dict = psql.setup_tables(metadata)
        weekday_num = days=datetime.now().weekday()
        last_date=datetime.now()
        last_date = datetime(last_date.year,last_date.month,last_date.day)
        result = table_dict['zwave_table'].select().where(cast(table_dict['zwave_table'].c.datetime,Date)==last_date).\
        order_by(table_dict['zwave_table'].c.datetime.asc()).execute()
        columns = result.keys()
        values = result.fetchall()

        df = pd.DataFrame(values,columns=columns)
        df = df.set_index('datetime')
        df = df[df['houseAll_Energy']>0]
        #df = fix_zwave_values(df)
        pos_lim = df['houseAll_Energy'].diff().mean()+3*df['houseAll_Energy'].diff().std()
        neg_lim = df['houseAll_Energy'].diff().mean()-3*df['houseAll_Energy'].diff().std()
        #df = df[df['houseAll_Energy'].diff()<pos_lim]
        #df = df[df['houseAll_Energy'].diff()>0]
        
        for hour in range(0,24):
            
            output_dict = {}
            output_dict['Hora'] = hour
            output_dict['Val'] = 0
            if len(df)>0:
                hour_num_points = len(df[df.index.hour==hour])
                if hour_num_points>0:
                    hour_diff = df[df.index.hour==hour]['houseAll_Energy'].iloc[hour_num_points-1] - \
                    df[df.index.hour==hour]['houseAll_Energy'].iloc[0]
                    output_dict['Val'] = hour_diff
            output.append(output_dict)
      
    except Exception , e :
        out = 'Query Failed.\n'
        out += str(request.args)
        out += str(e)
    
        return make_response(out, 404)
    
    return json.dumps(output)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=8888)
