# para correr: export FLASK_APP=app.py;flask run

from flask import Flask, render_template, request
import joblib
import pandas as pd
import sqlite3
from flask import g

app = Flask(__name__)

PREGUNTAS = open('preguntas.txt').read().split("\n")
CANDIDATOS = ['Candidato 1', 'Candidato 2', 'Juan Sartori (aka u/nano2412)']

DATABASE = 'predictor.db'


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None)
    return db


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        if validate(request.form):
            save_response(request.form)
            # Esto habría que reemplazar por un render_template
            return 'Gracias por contestar!'
        else:
            # Esto también
            return 'Error'

    return render_template(
        'main.html', preguntas=PREGUNTAS, candidatos=CANDIDATOS
    )


def validate(form):
    valid_keys = {
        'candidato',
        *_get_question_keys(PREGUNTAS)
    }
    return all(form.get(key, '').isdecimal() for key in valid_keys)


def predict(responses):
    xgb = joblib.load('xg_model')
    df_test = pd.DataFrame.from_dict({'resp1': [1], 'resp2': [1]})
    print(xgb.predict(df_test))


def save_response(form):
    cur = get_db().cursor()
    candidato = form['candidato']
    sql = "insert into encuestas('candidato_elegido') values(?);"
    res = cur.execute(sql, (candidato))
    id_encuesta = int(res.lastrowid)

    for id_pregunta in _get_question_keys(PREGUNTAS):
        respuesta = int(form[id_pregunta])

        print("resp {}".format(respuesta))
        sql = (
            "insert into respuestas_encuestas('id_encuesta','id_pregunta','respuesta') "
            "values(?,?,?);"
        )
        res = cur.execute(sql, (id_encuesta, id_pregunta.split('_')[-1], respuesta))
        print(res.lastrowid)


def _get_question_keys(questions):
    return ['pregunta_{}'.format(i + 1) for i, _ in enumerate(questions)]
