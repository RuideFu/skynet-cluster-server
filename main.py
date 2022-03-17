import sys
import os
from os import error
import sqlite3
import traceback
from flask import Flask, json, request, render_template

from sklearn.metrics import rand_score
from werkzeug.utils import secure_filename
import numpy as np
import ast

from gaia import gaia_args_verify
from gaia_util import gaia_match

api = Flask(__name__)

# from flask_cors import CORS
# CORS(api)
# api.debug = True

cols = [
    "junk",
    "junk",
    "junk",
    "U",
    "B",
    "V",
    "R",
    "I",
    "Jx",
    "Hx",
    "Kx",
    "uprime",
    "gprime",
    "rprime",
    "iprime",
    "zprime",
    "J",  # TODO: make these distinct
    "H",
    "Ks",
    "junk",
]


def find_data_in_files(age: float, metallicity: float, filters: list) -> list:

    # attempt to retrieve data from files
    try:
        data = np.load(
            os.path.join(
                os.path.dirname(__file__),
                "iso-npy-data",
                f"Girardi_{age:.2f}_{metallicity:.2f}.npy",
            )
        )

    except FileNotFoundError:
        raise ValueError({"error": "Requested data not found"})
    # format data
    try:

        def get_col(number: int):
            return data[:, cols.index(filters[number])]

        r_data = list(
            zip([round(a - b, 4)
                for a, b in zip(get_col(0), get_col(1))], get_col(2))
        )

        # r_data = list(zip(*[data[:, cols.index(i)] for i in filters]))
    except:
        raise error({"error": "Requested filter not found"})
    # return
    return r_data


def get_iSkip(age, metallicity):
    iSkip_file = os.path.join(os.path.dirname(__file__), 'iSkip.sqlite')
    conn = sqlite3.connect(iSkip_file)
    result = -1
    try:
        cur = conn.cursor()
        sources = cur.execute(
            'SELECT * FROM iSkip_forsql WHERE age = ? AND metallicity = ?', [age, metallicity]).fetchall()
        if sources != []:
            result = sources[0][2]
    except:
        raise error({"error": "Cannot Pull from iSkip Database"})
    finally:
        conn.close()
    return result


@api.route("/isochrone", methods=["GET"])
def get_data():
    tb = sys.exc_info()[2]
    try:
        age = float(request.args.get("age"))
        metallicity = float(request.args.get("metallicity"))
        filters = ast.literal_eval(request.args.get("filters"))
        iSkip = get_iSkip(age, metallicity)
        return json.dumps({'data': find_data_in_files(age, metallicity, filters), 'iSkip': iSkip})
        # print(filters)
    except Exception as e:
        return json.dumps({'err': str(e), 'log': traceback.format_tb(e.__traceback__)})


@api.route("/gaia", methods=["POST"])
def get_gaia():
    tb = sys.exc_info()[2]
    try:
        try:
            data = json.loads(request.get_data())['data']
            range = json.loads(request.get_data())['range']
        except:
            raise error({'error': 'GAIA Input invalid type'})
        result = gaia_match(data, range)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({'err': str(e), 'log': traceback.format_tb(e.__traceback__)})


def main():
    api.run()


if __name__ == "__main__":
    main()
